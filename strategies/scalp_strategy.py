from options_trading.utils.strike_picker import pick_strike
from runner.market_monitor import get_nifty_trend
from runner.utils.strategy_helpers import calculate_atr, calculate_quantity


def scalp_strategy(index_name, option_chain, capital):
    trend = get_nifty_trend()
    if trend not in ["bullish", "bearish"]:
        print("[SCALP] No clear trend detected.")
        return None

    # Select strike and expiry
    strike_info = pick_strike(
        index_name=index_name, direction=trend, premium_range=(100, 120)
    )
    if not strike_info:
        print("[SCALP] No suitable strike found")
        return None

    symbol = strike_info["symbol"]
    ltp = strike_info["ltp"]
    candles = strike_info["candles"]  # list of dicts with 'high', 'low', 'close'

    calculate_atr(candles)
    quantity = calculate_quantity(capital, ltp)

    trade = {
        "symbol": symbol,
        "entry_price": ltp,
        "stop_loss": ltp - 30 if trend == "bullish" else ltp + 30,
        "target": ltp + 60 if trend == "bullish" else ltp - 60,
        "quantity": quantity,
        "direction": trend,
        "strategy": "Scalp",
    }

    return trade
