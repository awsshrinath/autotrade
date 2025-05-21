from datetime import datetime


def get_strike_symbol(kite, index_symbol="BANKNIFTY", direction="bullish"):
    instruments = kite.instruments("NFO")
    datetime.now()

    def parse_expiry(ins):
        try:
            return datetime.strptime(ins["expiry"], "%Y-%m-%d")
        except:
            return None
    filtered = [
        ins
        for ins in instruments
        if ins["segment"] == "NFO-OPT" and
        ins["name"] == index_symbol and
        (
            (direction == "bullish" and ins["instrument_type"] == "CE") or
            (direction == "bearish" and ins["instrument_type"] == "PE")
        ) and
        80 <= ins["last_price"] <= 120 and
        ins["volume"] > 50000
    ]
    if not filtered:
        print("[STRIKE PICKER] No instrument matched.")
        return None
    nearest = min(filtered, key=lambda x: parse_expiry(x))
    return {
        "symbol": nearest["tradingsymbol"],
        "instrument_token": nearest["instrument_token"],
        "ltp": nearest["last_price"],
    }
