# runner/utils/strategy_helpers.py

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
    return instrument_map.get(symbol)

