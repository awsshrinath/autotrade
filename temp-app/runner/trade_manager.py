import datetime
import json
import os
from runner.risk_governor import RiskGovernor

# ✅ Initialize with limits
risk_guard = RiskGovernor(max_daily_loss=500, max_trades=3, cutoff_time="15:00")

def execute_trade(trade, paper_mode=True):
    if not risk_guard.can_trade():
        print(f"🚫 Trade blocked by RiskGovernor: {trade['symbol']}")
        return

    now = datetime.datetime.now().isoformat()
    trade["timestamp"] = now
    trade["mode"] = "paper" if paper_mode else "real"
    trade["status"] = "open"

    log_path = f"logs/trade_log_{trade['strategy'].lower()}.jsonl"
    os.makedirs("logs", exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps(trade) + "\n")

    print(f"[EXECUTE-{trade['mode'].upper()}] {trade['strategy']} trade executed for {trade['symbol']}")
    print(f"Qty: {trade['quantity']} | Entry: {trade['entry_price']} | SL: {trade['stop_loss']} | Target: {trade['target']}")

    risk_guard.update_trade(0)  # Initial placeholder for PnL

def simulate_exit(trade, candles):
    entry = trade["entry_price"]
    sl = trade["stop_loss"]
    target = trade["target"]
    direction = trade["direction"]
    qty = trade["quantity"]
    status = "open"
    exit_price = entry
    hold_minutes = 0

    for candle in candles:
        hold_minutes += 5
        high = candle["high"]
        low = candle["low"]

        if direction == "bullish":
            if high >= target:
                status = "target_hit"
                exit_price = target
                break
            elif low <= sl:
                status = "stop_loss_hit"
                exit_price = sl
                break
        else:
            if low <= target:
                status = "target_hit"
                exit_price = target
                break
            elif high >= sl:
                status = "stop_loss_hit"
                exit_price = sl
                break
    else:
        status = "auto_exit"
        exit_price = candles[-1]["close"]

    # Update trade
    trade["status"] = status
    trade["exit_price"] = exit_price
    trade["exit_time"] = candles[-1]["date"]
    trade["hold_duration"] = f"{hold_minutes} mins"
    trade["pnl"] = round((exit_price - entry) * qty if direction == "bullish" else (entry - exit_price) * qty, 2)

    # ✅ Log updated trade
    log_path = f"logs/trade_log_{trade['strategy'].lower()}.jsonl"
    with open(log_path, "a") as f:
        f.write(json.dumps(trade) + "\n")

    # ✅ Update RiskGovernor PnL
    risk_guard.update_trade(trade["pnl"])

    print(f"[EXIT-{trade['mode'].upper()}] {trade['symbol']} - {status.upper()} at {exit_price} | PnL: {trade['pnl']} | Held: {trade['hold_duration']}")