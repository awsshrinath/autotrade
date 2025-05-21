

def opening_range_strategy(stock_data, capital, open_range):
    """
    ORB strategy:
    - Entry when price breaks above the high of first N minutes
    - SL below range low, target = 2x risk
    """
    high = open_range["high"]
    low = open_range["low"]
    ltp = stock_data["ltp"]
    symbol = stock_data["symbol"]
    quantity = capital // ltp

    if ltp > high:
        entry = ltp
        sl = round(low, 2)
        target = round(entry + 2 * (entry - sl), 2)
        return {
            "symbol": symbol,
            "entry_price": entry,
            "stop_loss": sl,
            "target": target,
            "quantity": quantity,
            "strategy": "ORB",
        }

    return None
