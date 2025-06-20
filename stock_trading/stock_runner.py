import os
import sys
import time
from datetime import datetime
from datetime import time as dtime
import pytz
import logging
import asyncio
import traceback
from typing import Dict, Any, Optional

import requests
import kiteconnect

from runner.config import get_trading_config, load_config, PAPER_TRADE
from runner.firestore_client import FirestoreClient, get_firestore_client
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import create_enhanced_logger
from runner.strategy_factory import StrategyFactory, load_strategy
from runner.trade_manager import create_enhanced_trade_manager, EnhancedTradeManager, execute_trade, simulate_exit
from runner.market_data.market_data_fetcher import MarketDataFetcher
from runner.utils.notifications import send_slack_notification
from runner.position_monitor import PositionMonitor
from runner.risk_governor import RiskGovernor
from runner.utils.instrument_utils import get_instrument_token
from runner.utils.trade_utils import is_market_open, get_today_date

from strategies.base_strategy import BaseStrategy
from strategies.opening_range_strategy import OpeningRangeStrategy
from strategies.vwap_strategy import VwapStrategy
from strategies.range_reversal import RangeReversalStrategy
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
    main_logger = None
    while retries < MAX_RETRIES:
        try:
            main_logger = create_enhanced_logger(session_id="stock_trader_session")
            config = get_trading_config()

            main_logger.log_event("Stock Trading Bot started.")

            firestore_client = get_firestore_client()
            kite_manager = KiteConnectManager(logger=main_logger)
            trade_manager = create_enhanced_trade_manager(
                logger=main_logger,
                kite_manager=kite_manager,
                firestore_client=firestore_client
            )
            data_provider = MarketDataFetcher(kite_manager=kite_manager, logger=main_logger)

            stocks_to_trade = config.get('stocks_to_trade', [])
            strategy_name = config.get('strategy', 'vwap')
            
            wait_until_market_opens(main_logger)

            while is_market_open():
                market_data = data_provider.fetch_latest_data(stocks_to_trade)
                
                strategy = StrategyFactory.get_strategy(strategy_name)
                
                for stock_data in market_data:
                    trade_signal = strategy.generate_signal(stock_data)
                    if trade_signal:
                        trade_manager.execute_trade(trade_signal)
                
                time.sleep(60) # Main loop delay

            main_logger.log_event("Market is closed. Shutting down.")
            return

        except (requests.exceptions.ConnectionError, kiteconnect.exceptions.NetworkException) as e:
            if main_logger:
                main_logger.log_event(f"Network error: {e}. Retrying...", level="ERROR")
            retries += 1
            time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            if main_logger:
                main_logger.log_event(f"Critical error: {e}", level="CRITICAL")
                send_slack_notification(f"🚨 CRITICAL ERROR in Stock Trading Bot: {e}\n```{traceback.format_exc()}```")
            break # Exit on critical unknown error
            
    if retries >= MAX_RETRIES:
        if main_logger:
            main_logger.log_event("Bot failed after multiple retries.", level="CRITICAL")
            send_slack_notification("🚨 BOT OFFLINE: Stock trading bot failed after multiple retries.")

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

class StockTrader:
    def __init__(self, strategy_name: str, paper_trade: bool = False):
        self.strategy_name = strategy_name
        self.paper_trade = paper_trade
        
        # Initialize configuration
        initialize_config('config/base.yaml', 'config/development.yaml')
        self.config = get_config()
        
        # Initialize logger
        self.logger = TradingLogger()
        
        self.kite_manager = KiteConnectManager(logger=self.logger, config=self.config)
        self.risk_governor = RiskGovernor(self.logger)
        self.trade_manager = create_trade_manager(
            logger=self.logger, 
            kite_manager=self.kite_manager,
            config=self.config
        )
        self.position_monitor = PositionMonitor(
            self.logger, self.kite_manager, self.trade_manager, paper_trade=self.paper_trade
        )
        self.technical_indicators = TechnicalIndicators(self.market_data_fetcher)
        self.strategy_selector = StrategySelector(self.logger)
        self.kite_manager = KiteConnectManager(self.logger, get_trading_config())
        self.risk_governor = RiskGovernor(self.logger)
        self.trade_manager = create_enhanced_trade_manager(
            self.logger, self.kite_manager, paper_trade=self.paper_trade
        )
        self.position_monitor = PositionMonitor(
            self.logger, self.kite_manager, self.trade_manager, paper_trade=self.paper_trade
        )
        self.logger.log_info(f"StockTrader for '{self.strategy_name}' initialized.")

    def _get_market_data_fetcher(self):
        # This can be customized based on needs
        return MarketDataFetcher(self.logger, self.kite_manager)

    def _get_strategy(self, strategy_name: str):
        # ... existing code ...
        return None

    def run(self):
        """Main loop for the stock trader."""
        self.logger.log_info(f"Starting StockTrader with strategy: {self.strategy.name}")
        
        while True:
            # ... existing code ...
            try:
                # ... existing code ...
                # Add a small delay to avoid rapid looping
                time.sleep(10)
            except KeyboardInterrupt:
                self.logger.log_info("StockTrader stopped by user.")
                break
            except Exception as e:
                self.logger.log_error(f"An unexpected error occurred in StockTrader: {e}", exc_info=True)
                # Wait longer after an error
                time.sleep(60)

def run_stock_trader(strategy_name: str, paper_trade: bool = False):
    trader = StockTrader(strategy_name=strategy_name, paper_trade=paper_trade)
    trader.run()

if __name__ == "__main__":
    run_stock_trader(strategy_name="ORB", paper_trade=True)
