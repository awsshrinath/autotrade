from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from runner.config import PAPER_TRADE

def orb_strategy(symbol, candles, capital):
    """
    Executes ORB logic:
    - Uses 9:15 to 9:30 range as base
    - Enters breakout trade post 9:30
    - SL = Low/High of the base candle
    - Target = 1.5x risk
    """
    # Filter only candles between 9:15 and 9:30
    opening_range = [c for c in candles if "09:15" <= c["time"][-5:] <= "09:30"]
    if len(opening_range) < 3:
        print("[ORB] Not enough opening candles")
        return None

    high = max(c["high"] for c in opening_range)
    low = min(c["low"] for c in opening_range)
    range_mid = (high + low) / 2
    direction = None

    # Fetch the next candle after 9:30
    post_open = [c for c in candles if c["time"][-5:] > "09:30"]
    if not post_open:
        return None
    first_candle = post_open[0]

    if first_candle["close"] > high:
        direction = "bullish"
        entry = first_candle["close"]
        stop_loss = low
    elif first_candle["close"] < low:
        direction = "bearish"
        entry = first_candle["close"]
        stop_loss = high
    else:
        return None  # No breakout

    risk_per_unit = abs(entry - stop_loss)
    target = entry + 1.5 * risk_per_unit if direction == "bullish" else entry - 1.5 * risk_per_unit
    quantity = int(capital / entry)

    return {
        "symbol": symbol,
        "entry_price": round(entry, 2),
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "quantity": quantity,
        "direction": direction
    }

