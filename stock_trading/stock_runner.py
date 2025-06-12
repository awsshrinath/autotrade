import os
import sys

# Add project root to path BEFORE any other imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import time
from datetime import datetime
from datetime import time as dtime
import pytz
from runner.config import is_paper_trade
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory
from runner.strategy_factory import load_strategy
from runner.enhanced_trade_manager import create_enhanced_trade_manager, TradeRequest
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier

# Import paper trading components
try:
    from runner.paper_trader_integration import PaperTradingManager
    PAPER_TRADING_AVAILABLE = True
except ImportError:
    PAPER_TRADING_AVAILABLE = False

# Add missing PAPER_TRADE variable
PAPER_TRADE = is_paper_trade()

IST = pytz.timezone("Asia/Kolkata")

# Add missing simulate_exit function
def simulate_exit(trade, exit_candles):
    """Simulate exit for paper trading"""
    if not exit_candles:
        return
    
    exit_price = exit_candles[-1]['close']
    trade['exit_price'] = exit_price
    trade['exit_time'] = datetime.now().isoformat()
    trade['status'] = 'closed'
    
    # Calculate P&L
    entry_price = trade.get('entry_price', 0)
    quantity = trade.get('quantity', 0)
    trade_type = trade.get('trade_type', 'BUY')
    
    if trade_type == 'BUY':
        pnl = (exit_price - entry_price) * quantity
    else:
        pnl = (entry_price - exit_price) * quantity
    
    trade['pnl'] = pnl
    print(f"[PAPER-EXIT] {trade['symbol']}: Entry={entry_price}, Exit={exit_price}, PnL={pnl}")


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
    paper_trade_mode = is_paper_trade()
    
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
        f"Stock Trading Bot Started - Paper Trade Mode: {paper_trade_mode}",
        LogLevel.INFO,
        LogCategory.SYSTEM,
        data={
            'session_id': session_id,
            'date': today_date,
            'bot_type': 'stock-trader',
            'startup_time': datetime.now().isoformat(),
            'paper_trade_mode': paper_trade_mode
        },
        bot_type="stock-trader",
        source="stock_bot_startup"
    )

    # Initialize Firestore Client
    firestore_client = FirestoreClient(logger)
    
    # Initialize KiteConnectManager
    kite_manager = KiteConnectManager(logger)
    if not paper_trade_mode:
        kite_manager.set_access_token()

    # Initialize EnhancedTradeManager
    trade_manager = create_enhanced_trade_manager(
        logger=logger,
        kite_manager=kite_manager,
        firestore_client=firestore_client
    )
    trade_manager.start_trading_session()

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
            bot_type="stock-trader",
            source="strategy_loader"
        )
    
    # The actual strategy logic for getting signals would go here
    # For now, we'll simulate running the strategy periodically.
    
    logger.log_event(f"Starting trading loop with strategy: {strategy_name}")

    while is_market_open():
        try:
            # In a real scenario, a signal generation mechanism would replace this.
            # This just calls the placeholder `run_strategy_once` method.
            trade_manager.run_strategy_once(strategy_name, "bullish", "stock")
            
            # Sleep for a while before the next cycle
            time.sleep(300) # 5 minutes

        except Exception as e:
            logger.log_event(f"[ERROR] An error occurred in the trading loop: {e}")
            enhanced_logger.log_error(
                "Trading loop exception",
                error=str(e),
                bot_type="stock-trader"
            )
            time.sleep(60)

    logger.log_event("Market is closed. Stopping stock trading bot.")
    trade_manager.stop_trading_session()
    logger.log_event("Trading session stopped and positions closed if any.")


if __name__ == "__main__":
    run_stock_trading_bot()
