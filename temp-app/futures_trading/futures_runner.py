import os
import sys
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Core Imports ---
from runner.secret_manager_client import get_kite_client
from runner.trade_manager import execute_trade, simulate_exit
from runner.config import PAPER_TRADE

# --- Strategy ---
from futures_trading.strategies.orb_strategy import orb_strategy


def get_realtime_futures_data(kite):
    instruments = kite.instruments(exchange="NFO")
    for ins in instruments:
        if ins["name"] == "NIFTY" and ins["instrument_type"] == "FUT":
            return {
                "symbol": ins["tradingsymbol"],
                "token": ins["instrument_token"]
            }
    return None


def run_futures_trading_bot():
    print("[INFO] Starting Futures Trading Bot...")
    kite = get_kite_client("autotrade-453303")
    data = get_realtime_futures_data(kite)

    if not data:
        print("[ERROR] Could not fetch futures instrument")
        return

    from_date = datetime.now() - timedelta(minutes=60)
    to_date = datetime.now()
    candles = kite.historical_data(data["token"], from_date, to_date, interval="5minute")

    trade = orb_strategy(data["symbol"], candles, capital=15000)
    if trade:
        trade["strategy"] = "orb"
        execute_trade(trade, paper_mode=PAPER_TRADE)

        if PAPER_TRADE:
            exit_candles = kite.historical_data(trade["symbol"], trade["entry_time"], "15:20", interval="5minute")
            simulate_exit(trade, exit_candles)
    else:
        print("[WAIT] No valid ORB trade found.")


if __name__ == "__main__":
    run_futures_trading_bot()
