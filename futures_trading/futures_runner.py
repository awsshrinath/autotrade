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
from runner.strategy_factory import load_strategy
from runner.trade_manager import simulate_exit, execute_trade
from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory

def create_enhanced_logger(*args, **kwargs):
    """Wrapper for backward compatibility"""
    return create_trading_logger(*args, **kwargs)

# Import market components with fallbacks
try:
    from runner.market_data import MarketDataFetcher, TechnicalIndicators
    from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
except ImportError:
    class MarketDataFetcher:
        def __init__(self, *args): pass
    class TechnicalIndicators:
        def __init__(self, *args): pass
    class MarketMonitor:
        def __init__(self, *args): pass
        def get_market_sentiment(self, kite):
            return {"INDIA VIX": 15}
    class CorrelationMonitor:
        def __init__(self, *args): pass
    class MarketRegimeClassifier:
        def __init__(self, *args): pass

IST = pytz.timezone("Asia/Kolkata")


def wait_until_market_opens(logger):
    logger.log_event("[WAIT] Waiting for market to open...")
    while True:
        now = datetime.now().astimezone(IST).time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_event("[START] Market is open. Continuing.")
            break
        time.sleep(30)


# Strategy Map
STRATEGY_MAP = {"orb": "futures_trading.strategies.orb_strategy"}


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
    print("[INFO] Market closed. Attempting to exit open futures trades...")
    firestore = FirestoreClient()
    today = datetime.now().strftime("%Y-%m-%d")
    trades = firestore.fetch_trades(bot_name="futures-trader", date_str=today)

    for trade in trades:
        if trade["status"] != "open":
            continue
        try:
            if PAPER_TRADE:
                print(f"[EXIT-PAPER] Simulating exit for {trade['symbol']}")
                exit_candles = kite.historical_data(
                    trade["symbol"],
                    trade["entry_time"],
                    datetime.now(),
                    interval="5minute",
                )
                simulate_exit(trade, exit_candles)
            else:
                print(f"[FORCED-EXIT] Closing real trade for {trade['symbol']}")
                trade["status"] = "forced_exit"
                trade["exit_price"] = trade["entry_price"]
                trade["exit_time"] = datetime.now().isoformat()
                trade["pnl"] = 0
                firestore.log_trade(trade)
        except Exception as e:
            print(f"[ERROR] Exit failed for {trade['symbol']}: {e}")
    print("[INFO] All open trades handled. Exiting bot.")
    exit(0)


def get_realtime_futures_data(kite):
    instruments = kite.instruments(exchange="NFO")
    for ins in instruments:
        if ins["name"] == "NIFTY" and ins["instrument_type"] == "FUT":
            return {
                "symbol": ins["tradingsymbol"],
                "token": ins["instrument_token"],
            }
    return None


def wait_for_daily_plan(firestore_client, today_date, logger, max_wait_minutes=10):
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
            return daily_plan
        
        if attempt == 0:
            logger.log_event(f"[WAIT] Daily plan not found, waiting for main runner to create it...")
        
        logger.log_event(f"[WAIT] Plan not available yet, retrying in {wait_interval}s... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(wait_interval)
    
    logger.log_event(f"[TIMEOUT] Daily plan not found after {max_wait_minutes} minutes, using fallback")
    return None


def run_futures_trading_bot():
    today_date = datetime.now().strftime("%Y-%m-%d")
    paper_trade_mode = PAPER_TRADE
    
    # Initialize enhanced logger
    session_id = f"futures_trader_{int(time.time())}"
    enhanced_logger = create_enhanced_logger(
        session_id=session_id,
        bot_type="futures-trader"
    )
    
    # Initialize basic logger for backward compatibility
    logger = Logger(today_date)
    
    # Log startup with enhanced logger
    enhanced_logger.log_system_event(
        "Futures Trading Bot Started",
        {"version": "1.0", "paper_trade": paper_trade_mode}
    )
    
    logger.log_event("[BOOT] Starting Futures Trading Bot...")

    # Initialize Firestore client to fetch daily plan
    firestore_client = FirestoreClient(logger)

    # Wait for daily plan to be created by main runner (with timeout)
    daily_plan = wait_for_daily_plan(firestore_client, today_date, logger)
    
    if not daily_plan:
        logger.log_event(
            "[FALLBACK] No daily plan found even after waiting. Using intelligent fallback strategy."
        )
        
        # Intelligent fallback for futures
        strategy_name = "orb"  # Default for futures
        
        # Try to get market sentiment independently for better fallback
        try:
            from runner.market_monitor import MarketMonitor
            
            # Initialize Kite connection for fallback analysis
            kite_manager = KiteConnectManager(logger)
            kite_manager.set_access_token()
            kite = kite_manager.get_kite_client()
            
            market_monitor = MarketMonitor(logger)
            sentiment_data = market_monitor.get_market_sentiment(kite)
            
            # Use market sentiment to choose better fallback
            vix = sentiment_data.get("INDIA VIX", 15)
            if vix > 20:
                strategy_name = "orb"  # High volatility - ORB works well
                logger.log_event(f"[FALLBACK] High VIX ({vix}), using orb strategy")
            else:
                strategy_name = "orb"  # Default for futures
                logger.log_event(f"[FALLBACK] VIX ({vix}), using orb strategy")
                
        except Exception as e:
            logger.log_event(f"[FALLBACK] Could not get market sentiment for fallback: {e}")
    else:
        # Extract the futures strategy from the plan
        strategy_tuple = daily_plan.get("futures", "orb")
        strategy_name = strategy_tuple[0] if isinstance(strategy_tuple, (list, tuple)) else strategy_tuple
        logger.log_event(f"[PLAN] Using strategy from daily plan: {strategy_name}")

        # Log market sentiment from the plan
        sentiment = daily_plan.get("market_sentiment", {})
        if sentiment:
            logger.log_event(f"[SENTIMENT] Market sentiment from plan: {sentiment}")

    wait_until_market_opens(logger)

    try:
        # Initialize Kite connection
        kite_manager = KiteConnectManager(logger)
        kite_manager.set_access_token()
        kite = kite_manager.get_kite_client()
        
        # Load the strategy
        strategy = load_strategy(strategy_name, kite, logger)

        if not strategy:
            logger.log_event(
                f"[ERROR] Failed to load strategy: {strategy_name}. Falling back to orb."
            )
            strategy = load_strategy("orb", kite, logger)

        while is_market_open():
            logger.log_event("[ACTIVE] Market open, scanning for trades...")
            try:
                if strategy:
                    trade_signal = strategy.analyze()
                    if trade_signal:
                        logger.log_event(f"[TRADE] Executing trade: {trade_signal}")
                        # Execute trade in both paper and live mode
                        try:
                            result = execute_trade(trade_signal, paper_mode=PAPER_TRADE)
                            if result:
                                logger.log_event(f"[SUCCESS] Futures trade executed successfully: {result}")
                            else:
                                logger.log_event(f"[FAILED] Futures trade execution failed")
                        except Exception as trade_error:
                            logger.log_event(f"[ERROR] Futures trade execution exception: {trade_error}")
                    else:
                        logger.log_event("[WAIT] No valid trade signal.")
                        enhanced_logger.log_strategy_signal(
                            strategy=strategy_name,
                            symbol="N/A",
                            signal_data={'signal': 'none'}
                        )
                else:
                    logger.log_event("[ERROR] Strategy object not loaded.")
                    enhanced_logger.log_error(
                        Exception("Strategy not loaded"),
                        context={'strategy': strategy_name},
                        source="futures_trader"
                    )
            except Exception as e:
                logger.log_event(f"[ERROR] Strategy loop exception: {e}")
                enhanced_logger.log_error(
                    e,
                    context={'component': 'trading_loop', 'strategy': strategy_name},
                    source="futures_trader"
                )
            time.sleep(60)

        logger.log_event("[CLOSE] Market closed. Sleeping to prevent CrashLoop.")
        sys.exit(0)

    except Exception as e:
        logger.log_event(f"[FATAL] Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_futures_trading_bot()
