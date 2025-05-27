# main_runner.py


import os
import datetime
import time

from runner.market_monitor import MarketMonitor
from runner.strategy_selector import StrategySelector
from runner.trade_manager import TradeManager
from runner.logger import Logger
from runner.gpt_codefix_suggestor import GPTCodeFixSuggestor
from runner.daily_report_generator import DailyReportGenerator
from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.utils import create_daily_folders
from runner.openai_manager import OpenAIManager
from runner.kiteconnect_manager import KiteConnectManager
from runner.market_data_fetcher import MarketDataFetcher
from runner.firestore_client import FirestoreClient



def main():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    create_daily_folders(today_date)

    logger.log_event("GPT Runner+ Started Successfully.")

    firestore_client = FirestoreClient(logger)
    
    # Initialize Secret Manager / OpenAIManager if needed
    
    openai_manager = OpenAIManager(logger)

    # Initialize KiteConnect Manager
    kite_manager = KiteConnectManager(logger)
    kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()

    market_data_fetcher = MarketDataFetcher(kite, logger)

    # Initialize StrategySelector
    strategy_selector = StrategySelector(logger)

    # Initialize TradeManager
    trade_manager = TradeManager(kite, logger)

    # Pre-Market Monitoring
    market_monitor = MarketMonitor(logger)
    pre_market_data = market_monitor.fetch_premarket_data()
    logger.log_event("Starting Pre-Market Monitoring...")

    # Select Strategy
    selected_strategy = strategy_selector.select_strategy(pre_market_data)
    logger.log_event(f"Selected Strategy for Today: {selected_strategy}")
    trade_manager.load_strategy(selected_strategy)

    # Wait for Market Open
    now = datetime.datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        logger.log_event("Waiting for Indian Market Open at 9:15 AM...")
        time.sleep((market_open - now).total_seconds())

    # Start Live Trading
    logger.log_event("Starting Live Trading Session...")
    trade_manager.start_trading(selected_strategy, market_data_fetcher)

    monitor = GPTSelfImprovementMonitor(logger, firestore_client, openai_manager)
    monitor.analyze(bot_name=selected_strategy)


if __name__ == "__main__":
    main()
