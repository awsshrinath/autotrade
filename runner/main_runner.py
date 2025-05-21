import datetime
import os
import subprocess
import time

from gpt_runner.gpt_runner import run_gpt_runner
from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
from gpt_runner.rag.rag_worker import embed_logs_for_today
from runner.common_utils import create_daily_folders
from runner.firestore_client import FirestoreClient
from runner.kiteconnect_manager import KiteConnectManager
from runner.logger import Logger
from runner.market_monitor import MarketMonitor
from runner.openai_manager import OpenAIManager
from runner.strategy_selector import StrategySelector

# Load trading mode (PAPER or LIVE)
PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"

# Note: PROCESS_MAP is deprecated in Kubernetes mode
PROCESS_MAP = {}


def initialize_memory(logger):
    logger.log_event("[RAG] Syncing FAISS with Firestore...")
    sync_firestore_to_faiss()
    logger.log_event("[RAG] Embedding today's logs...")
    embed_logs_for_today()


def start_bot(bot_type, logger):
    # Validate bot_type to prevent command injection
    allowed_bot_types = ["stocks", "options", "futures"]
    if bot_type not in allowed_bot_types:
        logger.log_event(f"❌ Invalid bot type: {bot_type}. Must be one of {allowed_bot_types}")
        return
        
    logger.log_event(
        f"🚀 Triggering Kubernetes rollout restart for bot: {bot_type}"
    )
    try:
        # Use subprocess.run with shell=False for better security
        cmd = ["kubectl", "rollout", "restart", f"deployment/{bot_type}-trader", "-n", "gpt"]
        result = subprocess.run(cmd, shell=False, check=False, capture_output=True, text=True)
        if result.returncode == 0:
            logger.log_event(
                f"✅ Restart triggered for {bot_type}-trader deployment"
            )
        else:
            logger.log_event(f"❌ Failed to restart {bot_type}-trader: exit code {result.returncode}")
            if result.stderr:
                logger.log_event(f"Error details: {result.stderr}")
    except Exception as e:
        logger.log_event(f"❌ Failed to restart {bot_type}-trader: {e}")


def stop_bot(bot_type, logger):
    logger.log_event(
        f"⚠️ Note: stop_bot() not supported for Kubernetes-managed pods. Skipping stop for {bot_type}."
    )


def main():
    today_date = datetime.datetime.now().strftime("%Y-%m-%d")
    logger = Logger(today_date)
    create_daily_folders(today_date)
    logger.log_event("✅ GPT Runner+ Orchestrator Started")

    # Init memory + RAG sync
    initialize_memory(logger)

    # GPT + Firestore + Kite
    firestore_client = FirestoreClient(logger)
    OpenAIManager(logger)
    kite_manager = KiteConnectManager(logger)
    kite_manager.set_access_token()
    kite = kite_manager.get_kite_client()

    # Market Context
    market_monitor = MarketMonitor(logger)
    sentiment_data = market_monitor.get_market_sentiment(kite)
    logger.log_event(f"📈 Market Sentiment Data: {sentiment_data}")

    # Strategy Plan
    plan = {
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
    }
    firestore_client.db.collection("gpt_runner_daily_plan").document(
        today_date
    ).set(plan)
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

    # Launch all bots
    for bot in ["stocks", "options", "futures"]:
        start_bot(bot, logger)

    try:
        while True:
            time.sleep(60)
            now = time.strftime("%H:%M")
            if now >= "15:30":
                logger.log_event("🔔 Market closed. Stopping bots...")
                for bot in list(PROCESS_MAP.keys()):
                    stop_bot(bot, logger)

                logger.log_event(
                    "🧠 Starting GPT Self-Improvement Analysis..."
                )
                run_gpt_runner()
                break

            logger.log_event(
                "⚠️ Skipping bot crash detection in Kubernetes mode. Pods are self-healing via K8s."
            )

    except KeyboardInterrupt:
        logger.log_event("🛑 Interrupted manually. Stopping all bots...")
        for bot in list(PROCESS_MAP.keys()):
            stop_bot(bot, logger)

        logger.log_event("🧠 Running GPT Reflection after manual stop...")
        run_gpt_runner()


if __name__ == "__main__":
    main()
