from datetime import datetime, time


def simulate_exit(trade, future_candles):
    trade["entry_price"]
    stop_loss = trade["stop_loss"]
    target = trade["target"]
    direction = trade["direction"]
    entry_time = datetime.fromisoformat(trade["timestamp"])
    trade["symbol"]

    for candle in future_candles:
        candle_time = candle["timestamp"]
        if candle_time <= entry_time:
            continue

        high = candle["high"]
        low = candle["low"]

        # Target hit
        if direction == "bullish" and high >= target:
            return {
                **trade,
                "exit_price": target,
                "exit_reason": "target_hit",
                "status": "closed",
                "hold_duration": (candle_time - entry_time).seconds,
            }
        elif direction == "bearish" and low <= target:
            return {
                **trade,
                "exit_price": target,
                "exit_reason": "target_hit",
                "status": "closed",
                "hold_duration": (candle_time - entry_time).seconds,
            }

        # Stop loss hit
        if direction == "bullish" and low <= stop_loss:
            return {
                **trade,
                "exit_price": stop_loss,
                "exit_reason": "stop_loss_hit",
                "status": "closed",
                "hold_duration": (candle_time - entry_time).seconds,
            }
        elif direction == "bearish" and high >= stop_loss:
            return {
                **trade,
                "exit_price": stop_loss,
                "exit_reason": "stop_loss_hit",
                "status": "closed",
                "hold_duration": (candle_time - entry_time).seconds,
            }

        # Market close fallback
        if candle_time.time() >= time(15, 18):
            return {
                **trade,
                "exit_price": candle["close"],
                "exit_reason": "auto_exit_3_18",
                "status": "closed",
                "hold_duration": (candle_time - entry_time).seconds,
            }

    # If still open after all candles
    return {
        **trade,
        "exit_price": future_candles[-1]["close"],
        "exit_reason": "auto_exit_eod",
        "status": "closed",
        "hold_duration": (
            future_candles[-1]["timestamp"] - entry_time
        ).seconds,
    }
