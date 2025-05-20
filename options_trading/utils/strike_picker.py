from datetime import datetime, timedelta

# Pick strike and expiry for option trading based on premium and direction
def pick_strike(kite, symbol, direction, target_premium=100):
    instruments = kite.instruments("NSE")
    now = datetime.now()

    # Find closest expiry date (Friday/Monday depending on current date)
    expiries = sorted(
        list(set([i['expiry'] for i in instruments if i['instrument_type'] == 'OPTIDX' and i['name'] in ['NIFTY', 'BANKNIFTY']]))
    )
    
    next_expiry = next((e for e in expiries if e > now.date()), None)
    if not next_expiry:
        return None

    underlying_ltp = kite.ltp(f"NSE:{symbol}")[f"NSE:{symbol}"]['last_price']
    rounded_price = int(round(underlying_ltp / 50.0) * 50)  # nearest 50 for NIFTY/BNF

    strikes_to_try = range(rounded_price - 500, rounded_price + 500, 50)
    tradingsymbol_prefix = f"{symbol}{next_expiry.strftime('%y%b').upper()}"

    # Filter instruments for CE/PE options in range and check premium
    option_type = 'CE' if direction == 'bullish' else 'PE'
    
    for strike in strikes_to_try:
        tradingsymbol = f"{tradingsymbol_prefix}{strike}{option_type}"
        try:
            ltp = kite.ltp(f"NFO:{tradingsymbol}")[f"NFO:{tradingsymbol}"]['last_price']
            if abs(ltp - target_premium) <= 10:
                return {
                    "tradingsymbol": tradingsymbol,
                    "strike": strike,
                    "expiry": next_expiry,
                    "ltp": ltp
                }
        except Exception:
            continue

    return None
