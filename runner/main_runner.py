import time
import subprocess
from runner.market_monitor import MarketMonitor
from runner.strategy_selector import StrategySelector
#from runner.firestore_client import store_daily_plan
from runner.firestore_client import FirestoreClient
from runner.secret_manager_client import access_secret
import os
from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
from gpt_runner.rag.rag_worker import embed_logs_for_today
from gpt_runner.gpt_runner import run_gpt_runner

def initialize_memory():
    print("[RAG] Syncing FAISS with Firestore...")
    sync_firestore_to_faiss()
    print("[RAG] Embedding today's logs...")
    embed_logs_for_today()

# Load trading mode (PAPER or LIVE)
PAPER_TRADE = os.getenv("PAPER_TRADE", "true").lower() == "true"

# Define bot launch commands (can be subprocess or Kubernetes jobs)
BOT_COMMANDS = {
    "stocks": ["python", "stock_trading/stock_runner.py"],
    "options": ["python", "options_trading/options_runner.py"],
    "futures": ["python", "futures_trading/futures_runner.py"]
}

PROCESS_MAP = {}


def start_bot(bot_type):
    print(f"🚀 Starting bot: {bot_type}")
    PROCESS_MAP[bot_type] = subprocess.Popen(BOT_COMMANDS[bot_type])


def stop_bot(bot_type):
    if bot_type in PROCESS_MAP:
        print(f"🛑 Stopping bot: {bot_type}")
        PROCESS_MAP[bot_type].terminate()
        PROCESS_MAP[bot_type].wait()
        del PROCESS_MAP[bot_type]


def main():
    print("\n🌅 [MAIN] GPT Runner Main Orchestrator starting...")
    
    initialize_memory()
    monitor = MarketMonitor()
    sentiment = monitor.get_market_sentiment()

    print(f"📊 Market Sentiment: {sentiment}")

    plan = StrategySelector.choose_strategy(sentiment)
    plan["mode"] = "paper" if PAPER_TRADE else "live"

    FirestoreClient.store_daily_plan(plan)
    print(f"✅ Strategy Plan Saved: {plan}")

    # Launch bots
    for bot in ["stocks", "options", "futures"]:
        start_bot(bot)

    # Monitor and restart crashed bots
    try:
        while True:
            time.sleep(60)
            now = time.strftime("%H:%M")
            if now >= "15:30":
                print("\n🔔 Market closed. Shutting down all bots...")
                for bot in list(PROCESS_MAP.keys()):
                    stop_bot(bot)

                print("🧠 Starting GPT Self-Improvement Analysis...")
                run_gpt_runner()
                break
            for bot, proc in list(PROCESS_MAP.items()):
                if proc.poll() is not None:
                    print(f"⚠️ Bot crashed: {bot}. Restarting...")
                    start_bot(bot)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted manually. Stopping all bots...")
        for bot in list(PROCESS_MAP.keys()):
            stop_bot(bot)


if __name__ == "__main__":
    main()
