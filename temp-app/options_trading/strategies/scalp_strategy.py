from runner.utils.strategy_helpers import calculate_atr, calculate_quantity
from runner.utils.instrument_utils import get_options_token, get_nearest_expiry


def scalp_strategy(symbol, candles, capital, direction_hint="bullish"):
    if not candles or len(candles) < 5:
        print(f"[SCALP] Not enough data for {symbol}")
        return None

    latest = candles[-1]
    previous = candles[-2]

    # Entry logic: look for a strong reversal candle
    if direction_hint == "bullish" and latest["close"] > latest["open"] and previous["close"] < previous["open"]:
        direction = "bullish"
    elif direction_hint == "bearish" and latest["close"] < latest["open"] and previous["close"] > previous["open"]:
        direction = "bearish"
    else:
        print(f"[SCALP] No valid candle pattern for {symbol}")
        return None

    entry_price = latest["close"]
    atr = calculate_atr(candles, period=5)
    quantity = calculate_quantity(capital, entry_price)

    # Pick strike ~100 premium ITM based on direction
    expiry = get_nearest_expiry("OPT")
    strike = round(entry_price / 100) * 100
    strike = strike - 100 if direction == "bearish" else strike + 100
    option_type = "PE" if direction == "bearish" else "CE"

    token = get_options_token(symbol, strike_price=strike, option_type=option_type, expiry_date_str=expiry)

    trade = {
        "symbol": f"{symbol}{expiry[2:].replace('-', '')}{strike}{option_type}",
        "entry_price": entry_price,
        "stop_loss": entry_price - 0.3 * atr if direction == "bullish" else entry_price + 0.3 * atr,
        "target": entry_price + 0.6 * atr if direction == "bullish" else entry_price - 0.6 * atr,
        "quantity": quantity,
        "direction": direction,
        "strategy": "scalp",
        "option_token": token
    }

    return trade