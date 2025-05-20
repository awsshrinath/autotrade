
import os
import json
from datetime import datetime

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
                summary.append({
                    "strategy": fname.replace("trade_log_", "").replace(".jsonl", ""),
                    "total_trades": total,
                    "profitable_trades": wins,
                    "loss_trades": losses
                })

    now = datetime.now().isoformat()
    reflection = {
        "timestamp": now,
        "summary": summary
    }

    with open(reflection_log, "a") as f:
        f.write(json.dumps(reflection) + "\n")

    print(f"[GPT] Reflection complete. Summary saved to {reflection_log}")

if __name__ == "__main__":
    analyze_trades()
