import os
import sys
import time
from datetime import datetime
from datetime import time as dtime
try:
    import pytz
    PYTZ_AVAILABLE = True
except ImportError:
    PYTZ_AVAILABLE = False
    print("Warning: pytz not available. Timezone functionality may be limited.")
import logging
import asyncio
import traceback
from typing import Dict, Any, Optional

import requests
import kiteconnect

from runner.config import PAPER_TRADE, initialize_config
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory
from runner.strategy_factory import load_strategy
from runner.trade_manager import create_enhanced_trade_manager
from runner.utils.trade_utils import is_market_open, get_today_date
from runner.health_server import start_health_server, run_script_with_monitoring
import threading


# Global logger instance
# The logger is now initialized in the main execution block
logger = None


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
    class CorrelationMonitor:
        def __init__(self, *args): pass
    class MarketRegimeClassifier:
        def __init__(self, *args): pass

# Import paper trading components
try:
    from runner.paper_trader_integration import PaperTradingManager
    PAPER_TRADING_AVAILABLE = True
except ImportError:
    PAPER_TRADING_AVAILABLE = False

# Set up timezone
if PYTZ_AVAILABLE:
    IST = pytz.timezone("Asia/Kolkata")
else:
    IST = None
    print("Warning: pytz not available. Using system timezone.")

# PAPER_TRADE already imported above

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
    logger.log_system_event("Waiting for market to open...")
    while True:
        now = datetime.now().astimezone(IST).time()
        if dtime(9, 15) <= now <= dtime(15, 15):
            logger.log_system_event("Market is open. Continuing.")
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
        # It's a weekend
        return False
    
    # Check for holidays (implementation needed)
    # from runner.utils.trade_utils import is_holiday
    # if is_holiday(now.date()):
    #     return False

    start_time = dtime(9, 15)
    end_time = dtime(15, 30) # Extended slightly for safety
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
            logger.info(f"Daily plan found after {attempt * wait_interval} seconds")
            return daily_plan
        
        if attempt == 0:
            logger.info("Daily plan not found, waiting for main runner to create it...")
        
        logger.info(f"Plan not available yet, retrying in {wait_interval}s... (attempt {attempt + 1}/{max_attempts})")
        time.sleep(wait_interval)
    
    logger.warning(f"Daily plan not found after {max_wait_minutes} minutes, using fallback")
    return None


def run_stock_trading_bot():
    """Main function to run the stock trading bot."""
    global logger
    
    # Initialize configuration
    initialize_config()
    
    # Initialize enhanced logger
    session_id = f"stock_trader_{int(time.time())}"
    logger = create_trading_logger(session_id=session_id, bot_type="stock-trader")
    
    logger.log_system_event(
        "Stock Trading Bot Initializing",
        {"version": "1.1", "paper_trade": PAPER_TRADE}
    )

    try:
        firestore_client = FirestoreClient(logger)
        today_date = get_today_date()
        daily_plan = wait_for_daily_plan(firestore_client, today_date, logger)

        if not daily_plan:
            logger.warning("No daily plan. Using fallback: RELIANCE, TCS with ORB.")
            daily_plan = {
                'symbols': ['RELIANCE', 'TCS'],
                'strategies': {'RELIANCE': 'orb', 'TCS': 'orb'}
            }
        
        kite_manager = KiteConnectManager(logger=logger)
        trade_manager = create_enhanced_trade_manager(logger, kite_manager, paper_trade=PAPER_TRADE)
        
        if not PAPER_TRADE:
            wait_until_market_opens(logger)

        strategies = {}
        for symbol, strategy_name in daily_plan.get('strategies', {}).items():
            if symbol in daily_plan.get('symbols', []):
                strategy = load_strategy(strategy_name, kite_manager.get_kite_client(), logger, paper_trade=PAPER_TRADE)
                if strategy:
                    strategies[symbol] = strategy
                    logger.info(f"Loaded strategy '{strategy_name}' for symbol '{symbol}'")
                else:
                    logger.error(f"Could not load strategy '{strategy_name}' for '{symbol}'")

        if not strategies:
            logger.critical("No valid strategies loaded. Exiting.")
            return

        while is_market_open() or PAPER_TRADE:
            try:
                # Main trading loop
                for symbol, strategy in strategies.items():
                    # This logic needs to be more robust, but for now:
                    signals = strategy.analyze(symbol=symbol)
                    for signal in signals:
                        trade_manager.execute_trade(signal)

                if PAPER_TRADE:
                    logger.info("Paper trading mode: single run complete.")
                    break
                
                # Sleep for a minute before the next cycle
                time.sleep(60)
            
            except KeyboardInterrupt:
                logger.info("StockTrader stopped by user.")
                break
            except Exception as e:
                logger.error(f"An error occurred in the main trading loop: {e}", exc_info=True)
                # Brief sleep to prevent rapid-fire error loops
                time.sleep(30)
    
    except Exception as e:
        logger.log_error(e, context={"source": "stock_trader_main", "critical": True}, source="stock_trader", urgent=True)
        sys.exit(1)
    finally:
        logger.log_system_event("Stock trading bot shutting down.")
        logger.shutdown()


def main():
    """Main entry point for stock runner."""
    def trading_logic():
        run_stock_trading_bot()

    # Start health server in a separate thread
    health_port = int(os.environ.get('SERVICE_PORT', 8081))
    health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    
    run_script_with_monitoring(trading_logic)


if __name__ == "__main__":
    main()
