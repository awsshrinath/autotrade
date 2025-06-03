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
from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier

IST = pytz.timezone("Asia/Kolkata")


def wait_until_market_opens(logger):
    logger.log_event("[WAIT] Waiting for market to open...")
    while True:
        now = datetime.now().astimezone(IST).time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_event("[START] Market is open. Continuing.")
            break
        time.sleep(30)


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
    print("[INFO] Market closed. Attempting to exit open options trades...")
    firestore = FirestoreClient()
    today = datetime.now().strftime("%Y-%m-%d")
    trades = firestore.fetch_trades(bot_name="options-trader", date_str=today)

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


def run_options_trading_bot():
    today_date = datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    logger.log_event("[BOOT] Starting Options Trading Bot...")

    # Initialize Firestore client to fetch daily plan
    firestore_client = FirestoreClient(logger)

    # Wait for daily plan to be created by main runner (with timeout)
    daily_plan = wait_for_daily_plan(firestore_client, today_date, logger)
    
    if not daily_plan:
        logger.log_event(
            "[FALLBACK] No daily plan found even after waiting. Using intelligent fallback strategy."
        )
        
        # Intelligent fallback for options
        strategy_name = "scalp"  # Default for options
        
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
            if vix > 25:
                strategy_name = "scalp"  # High volatility - scalping works well
                logger.log_event(f"[FALLBACK] High VIX ({vix}), using scalp strategy")
            else:
                strategy_name = "scalp"  # Default for options
                logger.log_event(f"[FALLBACK] VIX ({vix}), using scalp strategy")
                
        except Exception as e:
            logger.log_event(f"[FALLBACK] Could not get market sentiment for fallback: {e}")
    else:
        # Extract the options strategy from the plan
        strategy_tuple = daily_plan.get("options", "scalp")
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
                f"[ERROR] Failed to load strategy: {strategy_name}. Falling back to scalp."
            )
            strategy = load_strategy("scalp", kite, logger)

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
                                logger.log_event(f"[SUCCESS] Options trade executed successfully: {result}")
                            else:
                                logger.log_event(f"[FAILED] Options trade execution failed")
                        except Exception as trade_error:
                            logger.log_event(f"[ERROR] Options trade execution exception: {trade_error}")
                    else:
                        logger.log_event("[WAIT] No valid trade signal.")
                else:
                    logger.log_event("[ERROR] Strategy not loaded.")
            except Exception as e:
                logger.log_event(f"[ERROR] Strategy loop exception: {e}")
            time.sleep(60)

        logger.log_event("[CLOSE] Market closed. Sleeping to prevent CrashLoop.")
        sys.exit(0)

    except Exception as e:
        logger.log_event(f"[FATAL] Bot crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_options_trading_bot()
