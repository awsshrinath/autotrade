import json
import os
import sys
from datetime import datetime

# Add project root to path to fix import issues
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import the GPTSelfImprovementMonitor from the correct location
try:
    from gpt_runner.rag.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
except ImportError:
    # Fallback to the runner version if rag version is not available
    print("Warning: Could not import from gpt_runner.rag, falling back to runner version")
    from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor

from runner.firestore_client import FirestoreClient
from runner.logger import Logger
from runner.openai_manager import OpenAIManager


def analyze_trades():
    log_dir = "logs"
    reflection_log = "logs/gpt_reflection.jsonl"
    summary = []

    for fname in os.listdir(log_dir):
        if fname.startswith("trade_log_") and fname.endswith(".jsonl"):
            path = os.path.join(log_dir, fname)
            with open(path, "r") as f:
                trades = [json.loads(line) for line in f.readlines()]
                total = len(trades)
                if total == 0:
                    continue
                wins = sum(1 for t in trades if t["target"] > t["entry_price"])
                losses = total - wins
                summary.append(
                    {
                        "strategy": fname.replace("trade_log_", "").replace(
                            ".jsonl", ""
                        ),
                        "total_trades": total,
                        "profitable_trades": wins,
                        "loss_trades": losses,
                    }
                )

    now = datetime.now().isoformat()
    reflection = {"timestamp": now, "summary": summary}

    with open(reflection_log, "a") as f:
        f.write(json.dumps(reflection) + "\n")

    firestore_client = FirestoreClient()
    gpt_client = OpenAIManager()
    logger = Logger("gpt_runner")
    monitor = GPTSelfImprovementMonitor(logger, firestore_client, gpt_client)
    monitor.analyze_errors(log_path="logs/gpt_runner.log", bot_name="stock-trader")


if __name__ == "__main__":
    analyze_trades()
