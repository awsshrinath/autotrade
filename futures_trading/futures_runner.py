import os
import sys
from datetime import datetime, time as dtime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# --- Core Imports ---
from runner.trade_manager import simulate_exit
from runner.firestore_client import FirestoreClient
from runner.config import PAPER_TRADE
from datetime import datetime, time as dtime
from runner.logger import Logger
from runner.strategy_factory import load_strategy
from runner.kiteconnect_manager import KiteConnectManager
import pytz

IST = pytz.timezone("Asia/Kolkata")


def is_market_open():
    now = datetime.now().astimezone(IST)
    weekday = now.weekday()
    if weekday >= 5:
        print("[INFO] Weekend. Market is closed.")
        return False
    return dtime(9, 15) <= now.time() <= dtime(15, 15)


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
    start_time = time(9, 15)
    end_time = time(15, 15)
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
            return {"symbol": ins["tradingsymbol"], "token": ins["instrument_token"]}
    return None


def run_futures_trading_bot():
    today_date = datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    logger.log_event("[BOOT] Starting Futures Trading Bot...")

    # Initialize Firestore client to fetch daily plan
    firestore_client = FirestoreClient(logger)

    # Fetch today's trading plan from Firestore
    daily_plan = firestore_client.fetch_daily_plan(today_date)
    if not daily_plan:
        logger.log_event(
            "[ERROR] No daily plan found in Firestore. Using default strategy."
        )
        strategy_name = "orb"  # Default fallback
    else:
        # Extract the futures strategy from the plan
        strategy_name = daily_plan.get("futures", "orb")
        logger.log_event(f"[PLAN] Using strategy from daily plan: {strategy_name}")

        # Log market sentiment from the plan
        sentiment = daily_plan.get("market_sentiment", {})
        if sentiment:
            logger.log_event(f"[SENTIMENT] Market sentiment from plan: {sentiment}")

    wait_until_market_opens(logger)

    try:
        kite = KiteConnectManager(logger).get_kite_client()
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
                        # Trade execution call here
                        # For production, uncomment:
                        # execute_trade(trade_signal, kite, logger)
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
    run_futures_trading_bot()
