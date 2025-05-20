import os
import datetime
import time

from runner.market_monitor import MarketMonitor
from runner.strategy_selector import StrategySelector
from runner.trade_manager import execute_trade, simulate_exit
from runner.logger import Logger
from runner.gpt_codefix_suggestor import GPTCodeFixSuggestor
from runner.daily_report_generator import DailyReportGenerator
from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
from runner.common_utils import create_daily_folders
from runner.openai_manager import OpenAIManager
from runner.kiteconnect_manager import KiteConnectManager
from runner.market_data_fetcher import MarketDataFetcher
from runner.firestore_client import FirestoreClient

def main():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    create_daily_folders(today_date)

    logger.log_event("✅ GPT Runner+ Started Successfully.")

    # Firestore
    firestore_client = FirestoreClient(logger)

    # GPT
    openai_manager = OpenAIManager(logger)

    # Kite Client
    kite_manager = KiteConnectManager(logger)
    kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()

    market_data_fetcher = MarketDataFetcher(kite, logger)

    # Strategy
    strategy_selector = StrategySelector(logger)
    market_monitor = MarketMonitor(logger)

    # Market Sentiment using live LTP
    sentiment_data = market_monitor.get_market_sentiment(kite)
    logger.log_event(f"📈 Market Sentiment Data: {sentiment_data}")

    # Pre-market data used for strategy selection
    pre_market_data = market_monitor.fetch_premarket_data()
    logger.log_event("📊 Pre-Market Data Fetched")

    selected_strategy, sentiment = strategy_selector.choose_strategy("stock", pre_market_data)
    logger.log_event(f"📌 Strategy Selected: {selected_strategy} | Sentiment: {sentiment}")

    # Wait till market open
    now = datetime.datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        logger.log_event("⏰ Waiting for market to open at 9:15 AM...")
        time.sleep((market_open - now).total_seconds())

    # --- Simulate strategy execution (replace with your actual bot logic)
    logger.log_event("🚀 Live Trading Session Started")

    # Simulate trade (example)
    candles = market_data_fetcher.get_candles("RELIANCE", "5minute", 60)
    from stock_trading.strategies.vwap_strategy import vwap_strategy
    trade = vwap_strategy("RELIANCE", candles, capital=10000)

    if trade:
        trade["strategy"] = selected_strategy
        execute_trade(trade, paper_mode=True)
        simulate_exit(trade, candles)
    else:
        logger.log_event("⚠️ No signal from strategy")

    # GPT Reflection
    monitor = GPTSelfImprovementMonitor(logger, firestore_client, openai_manager)
    monitor.analyze(bot_name="stock-trader")

if __name__ == "__main__":
    main()