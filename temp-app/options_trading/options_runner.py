import os
import sys
import time
from datetime import datetime, timedelta

# Ensure root path is added
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Strategy Imports ---
from options_trading.strategies.scalp_strategy import scalp_strategy
from runner.trade_manager import simulate_exit
from options_trading.utils.strike_picker import pick_strike

# --- Core System ---
from runner.secret_manager_client import get_kite_client
from runner.trade_manager import execute_trade
from runner.config import PAPER_TRADE


def run_options_trading_bot():
    print("[INFO] Starting Options Trading Bot...")
    kite = get_kite_client("autotrade-453303")

    strike_info = pick_strike("NIFTY", direction="bullish", kite=kite)
    if not strike_info:
        print("[ERROR] Could not pick strike")
        return

    from_date = datetime.now() - timedelta(minutes=60)
    to_date = datetime.now()
    candles = kite.historical_data(strike_info["token"], from_date, to_date, interval="5minute")

    trade = scalp_strategy(strike_info["symbol"], candles, capital=10000)
    if trade:
        trade["strategy"] = "scalp"
        execute_trade(trade, paper_mode=PAPER_TRADE)
    else:
        print("[WAIT] No valid scalp trade identified.")

    if PAPER_TRADE:
        exit_candles = kite.historical_data(trade["symbol"], trade["entry_time"], "15:20", interval="5minute")
        simulate_exit(trade, exit_candles)


if __name__ == "__main__":
    run_options_trading_bot()
