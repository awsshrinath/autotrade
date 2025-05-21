import datetime
from runner.logger import Logger
from kiteconnect import KiteConnect


def pick_strike(
    kite: KiteConnect,
    direction="bullish",
    instrument_type="NIFTY",
    premium_range=(100, 120),
):
    """
    Returns a tuple (tradingsymbol, strike_price, expiry_date) for ITM/ATM CE or PE based on market direction
    """
    today = datetime.date.today()
    instruments = kite.instruments(exchange="NFO")

    weekly_expiries = sorted(
        {
            inst["expiry"]
            for inst in instruments
            if inst["name"] == instrument_type and
            inst["segment"] == "NFO-OPT" and
            inst["expiry"] >= today
        }
    )

    if not weekly_expiries:
        raise Exception("No valid expiries found")

    selected_expiry = weekly_expiries[0]  # Pick the nearest expiry

    # Fetch LTP of index
    index_ltp = kite.ltp(f"NSE:{instrument_type}")[f"NSE:{instrument_type}"][
        "last_price"
    ]
    strike_diff = 50 if instrument_type == "BANKNIFTY" else 100
    base_strike = int(round(index_ltp / strike_diff)) * strike_diff

    strike_prices = range(
        base_strike - 10 * strike_diff,
        base_strike + 10 * strike_diff,
        strike_diff,
    )
    direction = direction.lower()
    option_type = "CE" if direction == "bullish" else "PE"

    candidates = []
    for strike in strike_prices:
        symbol = f"{instrument_type}{selected_expiry.strftime('%y%b').upper()}{strike}{option_type}"
        try:
            ltp = kite.ltp(f"NFO:{symbol}")[f"NFO:{symbol}"]["last_price"]
            if premium_range[0] <= ltp <= premium_range[1]:
                candidates.append((symbol, strike, selected_expiry, ltp))
        except Exception as e:
            Logger().warning(f"Skipping '{symbol}' due to error: {e}")
            continue

    if not candidates:
        raise Exception("No suitable option found within premium range")

    # Return best match (could sort by closest to ₹110)
    candidates.sort(key=lambda x: abs(x[3] - sum(premium_range) / 2))
    return candidates[0]
