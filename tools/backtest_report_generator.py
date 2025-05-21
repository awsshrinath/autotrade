import matplotlib.pyplot as plt
from datetime import datetime
from runner.openai_manager import OpenAIManager
import json


def generate_equity_curve(trades, output_path):
    equity = 0
    curve = []
    timestamps = []

    for t in trades:
        pnl = t.get("pnl", 0)
        equity += pnl
        curve.append(equity)
        timestamps.append(t.get("timestamp", str(datetime.now())))

    plt.figure(figsize=(10, 4))
    plt.plot(timestamps, curve, marker="o")
    plt.title("Equity Curve")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{output_path}/equity_curve.png")
    plt.close()


def summarize_backtest_with_gpt(trades):
    logs = [
        f"{t['timestamp']} {t['symbol']} {t['status']} PnL: {t.get('pnl', 0)}"
        for t in trades
    ]
    context = "\n".join(logs)
    prompt = f"Summarize this trading bot's performance:\n{context}"
    gpt = OpenAIManager()
    return gpt.summarize_text(prompt)


def run_backtest_report(path_to_log_json):
    with open(path_to_log_json, "r") as f:
        trades = json.load(f)

    generate_equity_curve(trades, "./reports")
    gpt_summary = summarize_backtest_with_gpt(trades)
    with open("./reports/gpt_summary.txt", "w") as f:
        f.write(gpt_summary)
