import os
import sys
import time
from datetime import datetime
from datetime import time as dtime
import pytz
import requests
import kiteconnect
from runner.config import PAPER_TRADE
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.strategy_factory import load_strategy
from runner.trade_manager import execute_trade
from runner.enhanced_logger import EnhancedLogger, create_enhanced_logger
from runner.enhanced_logging import LogLevel, LogCategory
from config.config_manager import get_trading_config
from runner.market_data.market_data_fetcher import MarketDataFetcher
# from kite.kite_manager import KiteManager  # Not available
# from utils.gcp_utils import get_firestore_client  # Not available
# from utils.notifications import send_slack_notification  # Not available

# Enhanced logging imports (already imported above)
# from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory
from runner.enhanced_trade_manager import create_enhanced_trade_manager

import logging
import asyncio
import traceback
from typing import Dict, Any, Optional

from runner.config import get_trading_config
from runner.trade_manager import simulate_exit
from runner.enhanced_logging import create_trading_logger, LogLevel, LogCategory
from strategies.opening_range_strategy import OpeningRangeStrategy
from strategies.vwap_strategy import VwapStrategy
from strategies.range_reversal import RangeReversalStrategy
from runner.logger import create_enhanced_logger
from runner.trade_manager import create_enhanced_trade_manager
from runner.firestore_client import FirestoreClient
from runner.strategy_factory import StrategyFactory
from runner.utils.trade_utils import is_market_open, get_today_date
from runner.config import get_trading_config
from strategies.orb_strategy import OrbStrategy

# Global logger instance
logger = logging.getLogger(__name__)

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

IST = pytz.timezone("Asia/Kolkata")

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

MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 10

def run_stock_trading_bot():
    """
    Main function to run the stock trading bot.
    Includes retry logic and enhanced error handling.
    """
    retries = 0
    while retries < MAX_RETRIES:
        try:
            config = load_config('config/stock_config.json')
            firestore_client = get_firestore_client()
            main_logger = EnhancedLogger(
                log_category=LogCategory.SYSTEM,
                log_level=LogLevel.INFO,
                config=config,
                firestore_client=firestore_client
            )
            main_logger.log_event("Stock Trading Bot started.")

            # ... (rest of the existing setup code inside the loop)
            kite_manager = KiteManager(
                api_key=os.getenv('KITE_API_KEY'),
                access_token=os.getenv('KITE_ACCESS_TOKEN'),
                firestore_client=firestore_client
            )
            # ... (rest of the setup)
            trade_manager = TradeManager(kite_manager, main_logger, config)
            data_provider = DataProvider(kite_manager, main_logger, config)

            strategy_name = config.get('strategy', 'default_strategy')
            strategy = load_strategy(strategy_name, trade_manager, main_logger, config)

            main_logger.log_event(f"Using strategy: {strategy_name}")

            while True:
                if is_market_open():
                    strategy.run()
                else:
                    main_logger.log_event("Market is closed. Pausing.")
                time.sleep(config.get('update_interval', 60))
            
            # If the loop breaks for some reason, we exit the retry loop
            break

        except (requests.exceptions.ConnectionError, kiteconnect.exceptions.NetworkException) as e:
            retries += 1
            main_logger.log_event(
                f"Connection error: {e}. Retrying ({retries}/{MAX_RETRIES}) in {RETRY_DELAY_SECONDS * retries}s...",
                level=LogLevel.WARNING
            )
            time.sleep(RETRY_DELAY_SECONDS * retries) # Exponential backoff
        
        except Exception as e:
            main_logger.log_event(f"An unexpected error occurred in stock_runner: {e}", level=LogLevel.ERROR)
            send_slack_notification(f"🚨 CRITICAL ERROR in Stock Trading Bot: {e}")
            # For critical errors, we might want to break immediately
            break 
    
    if retries >= MAX_RETRIES:
        final_message = "Stock Trading Bot failed after multiple retries."
        main_logger.log_event(final_message, level=LogLevel.CRITICAL)
        send_slack_notification(f"🚨 BOT OFFLINE: {final_message}")

def main():
    """Main entry point for stock trading bot"""
    run_stock_trading_bot()

if __name__ == "__main__":
    main()

def load_strategy(strategy_name: str, trade_manager, logger_instance, stock_config: dict):
    """Load a strategy instance by name."""
    strategy_factory = StrategyFactory(
        trade_manager=trade_manager,
        logger=logger_instance,
        config=stock_config
    )
    return strategy_factory.get_strategy(strategy_name)
