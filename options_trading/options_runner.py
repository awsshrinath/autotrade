
import os
import sys
from datetime import datetime, timedelta, time, timezone

# Ensure root path is added
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Strategy Imports ---
from options_trading.strategies.scalp_strategy import scalp_strategy
from runner.trade_manager import simulate_exit
from runner.secret_manager_client import get_kite_client
from runner.trade_manager import execute_trade
from runner.capital_manager import CapitalManager
from runner.firestore_client import FirestoreClient
from runner.config import PAPER_TRADE
from options_trading.utils.strike_picker import pick_strike
from runner.strategy_selector import select_best_strategy
import time
from runner.logger import Logger
from runner.strategy_factory import load_strategy
from runner.kiteconnect_manager import KiteConnectManager


IST = timezone(timedelta(hours=5, minutes=30))
def is_market_open():
    now = datetime.now(IST)
    weekday = now.weekday()
    if weekday >= 5:
        print("[INFO] Weekend detected. Market is closed.")
        return False
    start_time = time(9, 15)
    end_time = time(15, 15)
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
                    trade["symbol"], trade["entry_time"], datetime.now(), interval="5minute"
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

def run_options_trading_bot():
    logger = Logger(datetime.now().strftime("%Y-%m-%d"))
    logger.log_event("[BOOT] Starting Options Trading Bot...")

    try:
        kite = KiteConnectManager(logger).get_kite_client()
        strategy = load_strategy("scalp", kite, logger)

        while is_market_open():
            logger.log_event("[ACTIVE] Market open, scanning for trades...")
            try:
                if strategy:
                    trade_signal = strategy.analyze()
                    if trade_signal:
                        logger.log_event(f"[TRADE] Executing trade: {trade_signal}")
                        # Trade execution call here (mocked)
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
