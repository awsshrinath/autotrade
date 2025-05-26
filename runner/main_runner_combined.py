import datetime
import os
import time

from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
from gpt_runner.rag.rag_worker import embed_logs_for_today
from runner.common_utils import create_daily_folders
from runner.firestore_client import FirestoreClient
from runner.gpt_self_improvement_monitor import run_gpt_reflection
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.market_monitor import MarketMonitor
from runner.openai_manager import OpenAIManager
from runner.strategy_selector import StrategySelector

# Load trading mode (PAPER or LIVE)
PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"


def initialize_memory(logger):
    """Initialize RAG memory by syncing FAISS with Firestore and embedding today's logs"""
    logger.log_event("[RAG] Syncing FAISS with Firestore...")
    sync_firestore_to_faiss()
    logger.log_event("[RAG] Embedding today's logs...")
    embed_logs_for_today()


def main():
    """Main orchestrator function that coordinates all trading activities"""
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    create_daily_folders(today_date)
    logger.log_event("✅ GPT Runner+ Orchestrator Started")

    # Init memory + RAG sync
    initialize_memory(logger)

    # Initialize clients
    firestore_client = FirestoreClient(logger)
    OpenAIManager(logger)
    kite_manager = KiteConnectManager(logger)
    kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()

    # Get market context
    market_monitor = MarketMonitor(logger)
    sentiment_data = market_monitor.get_market_sentiment(kite)
    logger.log_event(f"📈 Market Sentiment Data: {sentiment_data}")

    # Create and store daily strategy plan
    plan = {
        "date": today_date,
        "stocks": StrategySelector(logger).choose_strategy(
            "stock", market_sentiment=sentiment_data
        ),
        "options": StrategySelector(logger).choose_strategy(
            "options", market_sentiment=sentiment_data
        ),
        "futures": StrategySelector(logger).choose_strategy(
            "futures", market_sentiment=sentiment_data
        ),
        "mode": "paper" if PAPER_TRADE else "live",
        "timestamp": datetime.datetime.now().isoformat(),
        "market_sentiment": sentiment_data,
    }
    firestore_client.store_daily_plan(plan)
    logger.log_event(f"✅ Strategy Plan Saved: {plan}")

    # Wait until market opens at 9:15 AM IST
    now = datetime.datetime.now()
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    if now < market_open:
        wait_minutes = int((market_open - now).total_seconds() / 60)
        logger.log_event(
            f"⏳ Waiting {wait_minutes} minutes until market opens at 9:15 AM IST..."
        )
        time.sleep((market_open - now).total_seconds())

    # Note: In Kubernetes, we don't need to start bots manually
    # The bots are deployed separately and will read the plan from Firestore
    logger.log_event(
        "🚀 Trading bots are running in separate pods and will read the plan from Firestore"
    )

    try:
        # Monitor the market until close
        while True:
            time.sleep(60)
            now = time.strftime("%H:%M")
            if now >= "15:30":
                logger.log_event("🔔 Market closed. Trading day complete.")

                # Run GPT self-improvement analysis
                logger.log_event("🧠 Starting GPT Self-Improvement Analysis...")
                run_gpt_reflection()  # Run reflection for all bots
                break

    except KeyboardInterrupt:
        logger.log_event("🛑 Interrupted manually. Stopping monitoring.")
        logger.log_event("🧠 Running GPT Reflection after manual stop...")
        run_gpt_reflection()


if __name__ == "__main__":
    main()
