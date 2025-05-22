import os
import sys
import time
import traceback
from datetime import datetime
from datetime import time as dtime
import pytz
from runner.config import PAPER_TRADE
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.strategy_factory import load_strategy
from runner.trade_manager import simulate_exit

IST = pytz.timezone("Asia/Kolkata")

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def safe_log(message, logger=None):
    """Safe logging that works even if logger fails"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message, flush=True)  # Force flush to stdout
    if logger:
        try:
            logger.log_event(message)
        except Exception as e:
            print(f"[{timestamp}] Logger failed: {e}", flush=True)


def wait_until_market_opens(logger):
    safe_log("[WAIT] Waiting for market to open...", logger)
    while True:
        try:
            now = datetime.now().astimezone(IST)
            current_time = now.time()
            current_weekday = now.weekday()
            
            safe_log(f"[DEBUG] Current time: {current_time}, Weekday: {current_weekday}", logger)
            
            # Check if it's weekend
            if current_weekday >= 5:  # Saturday = 5, Sunday = 6
                safe_log("[WEEKEND] Weekend detected. Sleeping for 1 hour...", logger)
                time.sleep(3600)
                continue
            
            # Check if market is open (9:15 AM to 3:15 PM)
            if dtime(9, 15) <= current_time <= dtime(15, 15):
                safe_log("[START] Market is open. Continuing.", logger)
                break
            else:
                safe_log(f"[WAIT] Market closed. Current time: {current_time}. Sleeping for 5 minutes...", logger)
                time.sleep(300)  # Wait 5 minutes
                
        except Exception as e:
            safe_log(f"[ERROR] Exception in wait_until_market_opens: {e}", logger)
            safe_log(f"[ERROR] Traceback: {traceback.format_exc()}", logger)
            time.sleep(60)  # Wait 1 minute on error


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
    try:
        now = datetime.now(IST)
        weekday = now.weekday()
        if weekday >= 5:
            return False
        start_time = dtime(9, 15)
        end_time = dtime(15, 15)
        return start_time <= now.time() <= end_time
    except Exception as e:
        print(f"[ERROR] Exception in is_market_open: {e}", flush=True)
        return False


def graceful_exit_if_off_hours(kite, logger):
    try:
        if is_market_open():
            return

        safe_log("[INFO] Outside market hours. Checking and exiting open trades...", logger)
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
                    safe_log(f"[EXIT-PAPER] Simulating exit for {symbol}", logger)
                    exit_candles = kite.historical_data(
                        token,
                        trade["entry_time"],
                        datetime.now(),
                        interval="5minute",
                    )
                    simulate_exit(trade, exit_candles)
                else:
                    safe_log(f"[FORCED-EXIT] Closing real trade for {symbol}", logger)
                    trade["status"] = "forced_exit"
                    trade["exit_price"] = trade["entry_price"]
                    trade["exit_time"] = datetime.now().isoformat()
                    trade["pnl"] = 0
                    firestore.log_trade(trade)

            except Exception as e:
                safe_log(f"[ERROR] Exit failed for {symbol}: {e}", logger)

        safe_log("[INFO] Exit process completed. Waiting for next market session...", logger)
        
    except Exception as e:
        safe_log(f"[ERROR] Exception in graceful_exit_if_off_hours: {e}", logger)
        safe_log(f"[ERROR] Traceback: {traceback.format_exc()}", logger)


def run_stock_trading_bot():
    logger = None
    try:
        # Initialize with basic logging first
        today_date = datetime.now().strftime("%Y-%m-%d")
        safe_log("[BOOT] Starting Stock Trading Bot...")
        
        # Try to initialize logger
        try:
            logger = Logger(today_date)
            safe_log("[BOOT] Logger initialized successfully", logger)
        except Exception as e:
            safe_log(f"[WARNING] Logger initialization failed: {e}")
            # Continue without logger - we have safe_log as fallback

        # Initialize Firestore client
        safe_log("[BOOT] Initializing Firestore client...", logger)
        try:
            firestore_client = FirestoreClient(logger)
            safe_log("[BOOT] Firestore client initialized", logger)
        except Exception as e:
            safe_log(f"[ERROR] Firestore client initialization failed: {e}", logger)
            # Continue - may work later or in different conditions

        # Initialize KiteConnect
        safe_log("[BOOT] Initializing KiteConnect...", logger)
        try:
            kite = KiteConnectManager(logger).get_kite_client()
            safe_log("[BOOT] KiteConnect initialized successfully", logger)
        except Exception as e:
            safe_log(f"[ERROR] KiteConnect initialization failed: {e}", logger)
            safe_log(f"[ERROR] Traceback: {traceback.format_exc()}", logger)
            # This is critical - but let's try to continue and retry
            kite = None

        # Main continuous loop
        safe_log("[BOOT] Entering main loop...", logger)
        loop_count = 0
        
        while True:
            try:
                loop_count += 1
                safe_log(f"[LOOP] Starting loop iteration {loop_count}", logger)
                
                # Wait for market to open if it's not open
                if not is_market_open():
                    safe_log("[WAIT] Market is closed, waiting...", logger)
                    wait_until_market_opens(logger)
                
                safe_log("[ACTIVE] Market should be open now, proceeding...", logger)
                
                # Retry KiteConnect if it failed earlier
                if kite is None:
                    safe_log("[RETRY] Attempting to reinitialize KiteConnect...", logger)
                    try:
                        kite = KiteConnectManager(logger).get_kite_client()
                        safe_log("[SUCCESS] KiteConnect reinitialized", logger)
                    except Exception as e:
                        safe_log(f"[ERROR] KiteConnect reinit failed: {e}", logger)
                        safe_log("[WAIT] Sleeping 5 minutes before retry...", logger)
                        time.sleep(300)
                        continue
                
                # Check if we need to exit any trades from previous session
                try:
                    graceful_exit_if_off_hours(kite, logger)
                except Exception as e:
                    safe_log(f"[ERROR] graceful_exit_if_off_hours failed: {e}", logger)
                
                # Refresh today's date and fetch trading plan
                today_date = datetime.now().strftime("%Y-%m-%d")
                daily_plan = None
                
                try:
                    daily_plan = firestore_client.fetch_daily_plan(today_date)
                except Exception as e:
                    safe_log(f"[ERROR] Failed to fetch daily plan: {e}", logger)
                
                if not daily_plan:
                    safe_log("[ERROR] No daily plan found. Using default strategy.", logger)
                    strategy_name = "vwap"  # Default fallback
                else:
                    strategy_name = daily_plan.get("stocks", "vwap")
                    safe_log(f"[PLAN] Using strategy from daily plan: {strategy_name}", logger)

                    sentiment = daily_plan.get("market_sentiment", {})
                    if sentiment:
                        safe_log(f"[SENTIMENT] Market sentiment: {sentiment}", logger)

                # Load strategy for the day
                strategy = None
                try:
                    strategy = load_strategy(strategy_name, kite, logger)
                    if strategy:
                        safe_log(f"[SUCCESS] Strategy '{strategy_name}' loaded", logger)
                    else:
                        safe_log(f"[ERROR] Failed to load strategy: {strategy_name}", logger)
                except Exception as e:
                    safe_log(f"[ERROR] Strategy loading exception: {e}", logger)
                    safe_log(f"[ERROR] Traceback: {traceback.format_exc()}", logger)

                # Trading loop - runs while market is open
                trading_loop_count = 0
                while is_market_open():
                    trading_loop_count += 1
                    safe_log(f"[ACTIVE] Trading loop {trading_loop_count} - Market open, scanning...", logger)
                    
                    try:
                        if strategy:
                            trade_signal = strategy.analyze()
                            if trade_signal:
                                safe_log(f"[TRADE] Trade signal found: {trade_signal}", logger)
                                # Trade execution call here
                                # For production, uncomment:
                                # execute_trade(trade_signal, kite, logger)
                            else:
                                safe_log("[SCAN] No trade signal found", logger)
                        else:
                            safe_log("[ERROR] No strategy loaded, skipping analysis", logger)
                    except Exception as e:
                        safe_log(f"[ERROR] Trading loop exception: {e}", logger)
                        safe_log(f"[ERROR] Traceback: {traceback.format_exc()}", logger)
                    
                    safe_log("[SLEEP] Sleeping for 60 seconds...", logger)
                    time.sleep(60)  # Wait 1 minute before next scan

                # Market closed for the day
                safe_log("[CLOSE] Market closed for today. Processing end-of-day tasks...", logger)
                
                # Process any remaining open trades
                try:
                    graceful_exit_if_off_hours(kite, logger)
                except Exception as e:
                    safe_log(f"[ERROR] End-of-day processing failed: {e}", logger)
                
                safe_log("[SLEEP] End of trading day. Sleeping for 1 hour...", logger)
                time.sleep(3600)  # Sleep for 1 hour

            except Exception as e:
                safe_log(f"[FATAL] Main loop exception: {e}", logger)
                safe_log(f"[FATAL] Traceback: {traceback.format_exc()}", logger)
                safe_log("[RECOVERY] Sleeping 5 minutes before retry...", logger)
                time.sleep(300)  # Wait 5 minutes before trying again

    except Exception as e:
        safe_log(f"[CRITICAL] Critical exception in run_stock_trading_bot: {e}")
        safe_log(f"[CRITICAL] Traceback: {traceback.format_exc()}")
        safe_log("[CRITICAL] Sleeping 10 minutes before final retry...")
        time.sleep(600)
        # One more attempt
        safe_log("[RESTART] Attempting final restart...")
        run_stock_trading_bot()


if __name__ == "__main__":
    safe_log("=== STOCK TRADING BOT STARTING ===")
    safe_log(f"Python version: {sys.version}")
    safe_log(f"Current working directory: {os.getcwd()}")
    safe_log(f"Python path: {sys.path}")
    
    # Add some environment debugging
    safe_log("=== ENVIRONMENT DEBUG ===")
    for key, value in os.environ.items():
        if any(keyword in key.upper() for keyword in ['KITE', 'FIRE', 'GOOGLE', 'TOKEN', 'KEY', 'SECRET']):
            safe_log(f"ENV: {key}=***HIDDEN***")
        else:
            safe_log(f"ENV: {key}={value}")
    
    run_stock_trading_bot()
