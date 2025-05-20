from datetime import datetime, timedelta
from kiteconnect import KiteConnect
from runner.config import PAPER_TRADE

def orb_strategy(symbol, kite: KiteConnect, capital):
    instrument_token = get_instrument_tokens(symbol)
    now = datetime.now()
    today_9_15 = now.replace(hour=9, minute=15, second=0, microsecond=0)
    today_9_30 = now.replace(hour=9, minute=30, second=0, microsecond=0)

    if now < today_9_30:
        return None  # Wait for opening range

    candles = kite.historical_data(
        instrument_token,
        from_date=today_9_15,
        to_date=today_9_30,
        interval="5minute"
    )

    if len(candles) < 3:
        return None

    opening_high = max(c['high'] for c in candles)
    opening_low = min(c['low'] for c in candles)

    latest = kite.historical_data(
        instrument_token,
        from_date=now - timedelta(minutes=15),
        to_date=now,
        interval="5minute"
    )[-1]

    current_price = latest['close']
    volume = latest['volume']
    direction = None

    if current_price > opening_high and volume > 100000:
        direction = "bullish"
    elif current_price < opening_low and volume > 100000:
        direction = "bearish"

    if not direction:
        return None

    entry_price = current_price
    atr = calculate_atr(candles)
    stop_loss = entry_price - atr if direction == "bullish" else entry_price + atr
    target = entry_price + 2 * atr if direction == "bullish" else entry_price - 2 * atr
    quantity = calculate_quantity(capital, entry_price)

    return {
        "symbol": symbol,
        "entry_price": entry_price,
        "stop_loss": stop_loss,
        "target": target,
        "quantity": quantity,
        "direction": direction
    }

def calculate_atr(candles, period=5):
    trs = []
    for i in range(1, len(candles)):
        high = candles[i]['high']
        low = candles[i]['low']
        prev_close = candles[i - 1]['close']
        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        trs.append(tr)
    return sum(trs[-period:]) / period if len(trs) >= period else 0

def calculate_quantity(capital, price):
    risk_percent = 0.01
    risk_amount = capital * risk_percent
    return int(risk_amount / price)

def get_instrument_tokens(symbol):
    instrument_map = {
        "RELIANCE": 738561,
        "ICICIBANK": 1270529,
        "SBIN": 779521
    }
    return instrument_map.get(symbol, 738561)
