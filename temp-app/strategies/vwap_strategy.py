from runner.utils.strategy_helpers import calculate_atr, calculate_quantity

def vwap_strategy(symbol, candles, capital):
    if not candles or len(candles) < 10:
        print(f"[VWAP] Not enough data for {symbol}")
        return None

    # Calculate VWAP for last 10 candles
    vwap_sum = 0
    volume_sum = 0
    for candle in candles[-10:]:
        typical_price = (candle['high'] + candle['low'] + candle['close']) / 3
        vwap_sum += typical_price * candle['volume']
        volume_sum += candle['volume']

    vwap = vwap_sum / volume_sum if volume_sum else 0
    latest_close = candles[-1]['close']

    if latest_close > vwap:
        direction = "bullish"
    elif latest_close < vwap:
        direction = "bearish"
    else:
        print(f"[VWAP] No clear direction for {symbol}")
        return None

    atr = calculate_atr(candles)
    quantity = calculate_quantity(capital, latest_close)

    trade = {
        "symbol": symbol,
        "entry_price": latest_close,
        "stop_loss": latest_close - atr if direction == "bullish" else latest_close + atr,
        "target": latest_close + 2 * atr if direction == "bullish" else latest_close - 2 * atr,
        "quantity": quantity,
        "direction": direction
    }

    return trade