import os
import sys

# Add project root to path BEFORE any other imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
from datetime import time as dtime
import pytz
from runner.config import PAPER_TRADE
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory
from runner.strategy_factory import load_strategy
from runner.trade_manager import TradeManager, simulate_exit, execute_trade
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier

# Import paper trading components
try:
    from runner.paper_trader_integration import PaperTradingManager
    PAPER_TRADING_AVAILABLE = True
except ImportError:
    PAPER_TRADING_AVAILABLE = False

IST = pytz.timezone("Asia/Kolkata")


def wait_until_market_opens(logger):
    logger.log_event("[WAIT] Waiting for market to open...")
    while True:
        now = datetime.now().astimezone(IST).time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_event("[START] Market is open. Continuing.")
            break
        time.sleep(30)


# --- Static token mapping for NSE stocks ---
STATIC_TOKENS = {
    "RELIANCE": 738561,
    "TCS": 2953217,
    "INFY": 408065,
    "HDFCBANK": 341249,
    "SBIN": 779521,
}

STRATEGY_MAP = {
    "vwap": "stock_trading.strategies.vwap_strategy",
    "orb": "stock_trading.strategies.orb_strategy",
    "range_reversal": "stock_trading.strategies.range_reversal",
}


def is_market_open():
    now = datetime.now(IST)
    weekday = now.weekday()
    if weekday >= 5:
        print("[INFO] Weekend detected. Market is closed.")
        return False
    start_time = dtime(9, 15)
    end_time = dtime(15, 15)
    return start_time <= now.time() <= end_time


def graceful_exit_if_off_hours(kite):
    if is_market_open():
        return

    print("[INFO] Outside market hours. Checking and exiting open trades...")
    firestore = FirestoreClient()
    today = datetime.now().strftime("%Y-%m-%d")
    trades = firestore.fetch_trades(bot_name="stock-trader", date_str=today)

    for trade in trades:
        if trade["status"] != "open":
            continue

        symbol = trade["symbol"]
        token = STATIC_TOKENS.get(symbol)
        if not token:
            continue

        try:
            if PAPER_TRADE:
                print(f"[EXIT-PAPER] Simulating exit for {symbol}")
                exit_candles = kite.historical_data(
                    token,
                    trade["entry_time"],
                    datetime.now(),
                    interval="5minute",
                )
                simulate_exit(trade, exit_candles)
            else:
                print(f"[FORCED-EXIT] Closing real trade for {symbol}")
                trade["status"] = "forced_exit"
                trade["exit_price"] = trade["entry_price"]
                trade["exit_time"] = datetime.now().isoformat()
                trade["pnl"] = 0
                firestore.log_trade(trade)

        except Exception as e:
            print(f"[ERROR] Exit failed for {symbol}: {e}")

    print("[INFO] Exit process completed. Bot will stop.")
    exit(0)


def get_realtime_stock_data(symbols):
    data_list = []
    for symbol in symbols:
        token = STATIC_TOKENS.get(symbol)
        if not token:
            print(f"[WARN] Token not found for: {symbol}")
            continue
        data_list.append({"symbol": symbol, "token": token})
    return data_list


def wait_for_daily_plan(firestore_client, today_date, logger, enhanced_logger, max_wait_minutes=10):
    """
    Wait for the daily plan to be available, created by the main runner.
    Returns the plan if found, None if timeout reached.
    """
    wait_interval = 30  # seconds
    max_attempts = (max_wait_minutes * 60) // wait_interval
    
    for attempt in range(max_attempts):
        daily_plan = firestore_client.fetch_daily_plan(today_date)
        if daily_plan:
            logger.log_event(f"[PLAN] Daily plan found after {attempt * wait_interval} seconds")
            enhanced_logger.log_event(
                "Daily plan retrieved successfully",
                LogLevel.INFO,
                LogCategory.STRATEGY,
                data={
                    'wait_time_seconds': attempt * wait_interval,
                    'attempt_number': attempt + 1,
                    'plan_found': True
                },
                bot_type="stock-trader",
                source="plan_retrieval"
            )
            return daily_plan
        
        if attempt == 0:
            logger.log_event(f"[WAIT] Daily plan not found, waiting for main runner to create it...")
            enhanced_logger.log_event(
                "Waiting for daily plan creation",
                LogLevel.INFO,
                LogCategory.STRATEGY,
                data={
                    'max_wait_minutes': max_wait_minutes,
                    'wait_interval': wait_interval
                },
                bot_type="stock-trader",
                source="plan_retrieval"
            )
        
        logger.log_event(f"[WAIT] Plan not available yet, retrying in {wait_interval}s... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(wait_interval)
    
    logger.log_event(f"[TIMEOUT] Daily plan not found after {max_wait_minutes} minutes, using fallback")
    enhanced_logger.log_event(
        "Daily plan wait timeout, using fallback",
        LogLevel.WARNING,
        LogCategory.STRATEGY,
        data={
            'wait_time_minutes': max_wait_minutes,
            'total_attempts': max_attempts,
            'plan_found': False
        },
        bot_type="stock-trader",
        source="plan_retrieval"
    )
    return None


def run_stock_trading_bot():
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # Initialize enhanced logger for Firestore and GCS logging
    session_id = f"stock_trader_{int(time.time())}"
    enhanced_logger = create_enhanced_logger(
        session_id=session_id,
        enable_gcs=True,
        enable_firestore=True
    )
    
    # Initialize basic logger for backward compatibility
    logger = Logger(today_date)
    
    # Log startup with enhanced logger
    enhanced_logger.log_event(
        f"Stock Trading Bot Started - Paper Trade Mode: {PAPER_TRADE}",
        LogLevel.INFO,
        LogCategory.SYSTEM,
        data={
            'session_id': session_id,
            'date': today_date,
            'bot_type': 'stock-trader',
            'startup_time': datetime.now().isoformat(),
            'paper_trade_mode': PAPER_TRADE
        },
        bot_type="stock-trader",
        source="stock_bot_startup"
    )

    # Initialize Firestore Client
    firestore_client = FirestoreClient(logger)
    
    # Initialize TradeManager with proper paper trading support
    kite_manager = KiteConnectManager(logger)
    if not PAPER_TRADE:
        kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()
    
    trade_manager = TradeManager(
        logger=logger,
        kite=kite,
        firestore_client=firestore_client
    )
    
    # Initialize Paper Trading Manager if enabled
    paper_trading_manager = None
    if PAPER_TRADE and PAPER_TRADING_AVAILABLE:
        paper_trading_manager = PaperTradingManager(
            logger=logger,
            firestore_client=firestore_client
        )
        logger.log_event("Paper Trading Manager initialized for stock trading")

    # Strategy selection from daily plan or fallback
    strategy_name = "vwap"  # Default strategy
    
    daily_plan = wait_for_daily_plan(firestore_client, today_date, logger, enhanced_logger)
    if daily_plan:
        strategy_tuple = daily_plan.get("stocks", "vwap")
        strategy_name = strategy_tuple[0] if isinstance(strategy_tuple, (list, tuple)) else strategy_tuple
        logger.log_event(f"[PLAN] Using strategy from daily plan: {strategy_name}")
        
        enhanced_logger.log_event(
            "Daily strategy plan loaded",
            LogLevel.INFO,
            LogCategory.STRATEGY,
            data={
                'strategy': strategy_name,
                'daily_plan': daily_plan
            },
            strategy=strategy_name,
            bot_type="stock-trader",
            source="strategy_selection"
        )

        # Log market sentiment from the plan
        sentiment = daily_plan.get("market_sentiment", {})
        if sentiment:
            logger.log_event(f"[SENTIMENT] Market sentiment from plan: {sentiment}")
            enhanced_logger.log_event(
                "Market sentiment analysis loaded",
                LogLevel.INFO,
                LogCategory.MARKET_DATA,
                data={'market_sentiment': sentiment},
                bot_type="stock-trader",
                source="market_analysis"
            )

    wait_until_market_opens(logger)

    try:
        strategy = load_strategy(strategy_name, kite, logger)

        if not strategy:
            logger.log_event(
                f"[ERROR] Failed to load strategy: {strategy_name}. Falling back to vwap."
            )
            strategy = load_strategy("vwap", kite, logger)

        # Track active trades for paper trading
        active_paper_trades = []

        while is_market_open():
            logger.log_event("[ACTIVE] Market open, scanning for trades...")
            enhanced_logger.log_event(
                "Market scan cycle started",
                LogLevel.DEBUG,
                LogCategory.SYSTEM,
                data={'scan_time': datetime.now().isoformat()},
                bot_type="stock-trader",
                source="trading_loop"
            )
            
            try:
                if strategy:
                    trade_signal = strategy.analyze()
                    if trade_signal:
                        logger.log_event(f"[TRADE] Executing trade: {trade_signal}")
                        enhanced_logger.log_event(
                            "Trade signal generated",
                            LogLevel.INFO,
                            LogCategory.TRADE,
                            data={
                                'trade_signal': trade_signal,
                                'strategy': strategy_name,
                                'signal_time': datetime.now().isoformat()
                            },
                            strategy=strategy_name,
                            symbol=trade_signal.get('symbol') if isinstance(trade_signal, dict) else None,
                            bot_type="stock-trader",
                            source="strategy_analysis"
                        )
                        
                        # Execute trade using appropriate manager
                        try:
                            if PAPER_TRADE and paper_trading_manager:
                                # Use paper trading manager
                                result = paper_trading_manager.execute_trade(trade_signal, strategy_name)
                            else:
                                # Use TradeManager for live trading or fallback paper trading
                                result = trade_manager._execute_trade(trade_signal, "stock-trader", strategy_name)
                            
                            if result:
                                # Track paper trades for simulation
                                if PAPER_TRADE:
                                    active_paper_trades.append(result)
                                    
                                logger.log_event(f"[SUCCESS] Trade executed successfully: {result}")
                                enhanced_logger.log_event(
                                    "Trade executed successfully",
                                    LogLevel.INFO,
                                    LogCategory.TRADE,
                                    data={
                                        'trade_result': result,
                                        'paper_mode': PAPER_TRADE,
                                        'execution_time': datetime.now().isoformat()
                                    },
                                    strategy=strategy_name,
                                    symbol=trade_signal.get('symbol') if isinstance(trade_signal, dict) else None,
                                    bot_type="stock-trader",
                                    source="trade_execution"
                                )
                                
                                # Force GCS upload for successful trades
                                enhanced_logger.flush_all()
                                
                            else:
                                logger.log_event(f"[FAILED] Trade execution failed")
                                enhanced_logger.log_event(
                                    "Trade execution failed",
                                    LogLevel.WARNING,
                                    LogCategory.TRADE,
                                    data={
                                        'trade_signal': trade_signal,
                                        'paper_mode': PAPER_TRADE,
                                        'failure_time': datetime.now().isoformat()
                                    },
                                    strategy=strategy_name,
                                    symbol=trade_signal.get('symbol') if isinstance(trade_signal, dict) else None,
                                    bot_type="stock-trader",
                                    source="trade_execution"
                                )
                        except Exception as trade_error:
                            logger.log_event(f"[ERROR] Trade execution exception: {trade_error}")
                            enhanced_logger.log_event(
                                "Trade execution exception",
                                LogLevel.ERROR,
                                LogCategory.ERROR,
                                data={
                                    'trade_error': str(trade_error),
                                    'trade_signal': trade_signal,
                                    'paper_mode': PAPER_TRADE
                                },
                                strategy=strategy_name,
                                bot_type="stock-trader",
                                source="trade_execution"
                            )
                    else:
                        logger.log_event("[WAIT] No valid trade signal.")
                        enhanced_logger.log_event(
                            "No trade signal generated",
                            LogLevel.DEBUG,
                            LogCategory.STRATEGY,
                            data={
                                'strategy': strategy_name,
                                'scan_time': datetime.now().isoformat()
                            },
                            strategy=strategy_name,
                            bot_type="stock-trader",
                            source="strategy_analysis"
                        )
                        
                    # Monitor paper trades for exit conditions
                    if PAPER_TRADE and active_paper_trades:
                        # Get current market data for monitoring
                        try:
                            # Create sample market data for paper trade monitoring
                            from runner.paper_trader_integration import create_sample_market_data
                            current_market_data = create_sample_market_data()
                            
                            # Monitor trades using paper trading manager
                            if paper_trading_manager:
                                paper_trading_manager.monitor_positions(current_market_data)
                            
                            # Also simulate exits using TradeManager
                            for i, trade in enumerate(active_paper_trades[:]):
                                if trade.get('status') == 'paper_open':
                                    exit_result = trade_manager.simulate_trade_exit(trade, current_market_data)
                                    if exit_result and exit_result.get('status') == 'paper_closed':
                                        active_paper_trades[i] = exit_result
                                        enhanced_logger.flush_all()  # Upload exit to GCS
                                        
                        except Exception as monitor_error:
                            logger.log_event(f"[ERROR] Trade monitoring error: {monitor_error}")
                            
                else:
                    logger.log_event("[ERROR] Strategy not loaded.")
                    enhanced_logger.log_event(
                        "Strategy not loaded error",
                        LogLevel.ERROR,
                        LogCategory.ERROR,
                        data={'attempted_strategy': strategy_name},
                        bot_type="stock-trader",
                        source="strategy_error"
                    )
            except Exception as e:
                logger.log_event(f"[ERROR] Strategy loop exception: {e}")
                enhanced_logger.log_event(
                    "Strategy loop exception",
                    LogLevel.ERROR,
                    LogCategory.ERROR,
                    data={
                        'error': str(e),
                        'strategy': strategy_name,
                        'error_time': datetime.now().isoformat()
                    },
                    strategy=strategy_name,
                    bot_type="stock-trader",
                    source="trading_loop"
                )
            time.sleep(60)

        logger.log_event("[CLOSE] Market closed. Sleeping to prevent CrashLoop.")
        enhanced_logger.log_event(
            "Market closed - bot shutting down",
            LogLevel.INFO,
            LogCategory.SYSTEM,
            data={
                'shutdown_time': datetime.now().isoformat(),
                'reason': 'market_closed',
                'final_paper_trades': len(active_paper_trades) if PAPER_TRADE else 0
            },
            bot_type="stock-trader",
            source="bot_shutdown"
        )
        
        # Graceful shutdown of enhanced logger
        enhanced_logger.shutdown()
        sys.exit(0)

    except Exception as e:
        logger.log_event(f"[FATAL] Bot crashed: {e}")
        enhanced_logger.log_event(
            "Bot fatal error",
            LogLevel.CRITICAL,
            LogCategory.ERROR,
            data={
                'error': str(e),
                'crash_time': datetime.now().isoformat()
            },
            bot_type="stock-trader",
            source="fatal_error"
        )
        enhanced_logger.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    run_stock_trading_bot()
