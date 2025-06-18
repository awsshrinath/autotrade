import datetime
import pandas as pd
import io
import time
from runner.logger import TradingLogger
from runner.secret_manager import access_secret

from kiteconnect import KiteConnect

_cached_instruments = None

# Initialize logger
logger = TradingLogger()


def get_kite_client():
    from runner.kiteconnect_manager import PROJECT_ID
    from runner.secret_manager import access_secret

    kite = KiteConnect(api_key=access_secret("ZERODHA_API_KEY", PROJECT_ID))
    kite.set_access_token(access_secret("ZERODHA_ACCESS_TOKEN", PROJECT_ID))
    return kite


def load_instruments():
    global _cached_instruments
    if _cached_instruments is None:
        kite = get_kite_client()
        _cached_instruments = kite.instruments("NFO")
    return _cached_instruments


def get_futures_token(symbol, expiry_date_str=None):
    instruments = load_instruments()
    if expiry_date_str is None:
        expiry_date_str = get_nearest_expiry("FUT")

    for inst in instruments:
        if (
            inst["instrument_type"] == "FUT"
            and inst["name"] == symbol
            and inst["expiry"] == expiry_date_str
        ):
            return inst["instrument_token"]
    return None


def get_options_token(symbol, strike_price, option_type, expiry_date_str=None):
    instruments = load_instruments()
    if expiry_date_str is None:
        expiry_date_str = get_nearest_expiry("OPT")

    for inst in instruments:
        if (
            inst["instrument_type"] == "OPT"
            and inst["name"] == symbol
            and inst["strike"] == strike_price
            and inst["expiry"] == expiry_date_str
            and inst["tradingsymbol"].endswith(option_type.upper())
        ):
            return inst["instrument_token"]
    return None


def get_nearest_expiry(inst_type):
    today = datetime.date.today()
    instruments = load_instruments()
    expiries = sorted(
        set(
            inst["expiry"]
            for inst in instruments
            if inst["instrument_type"] == inst_type
        )
    )
    for date in expiries:
        if date >= today:
            return date.isoformat()
    return None


def get_instrument_tokens(symbols):
    instruments = load_instruments()
    token_map = {}

    for symbol in symbols:
        for inst in instruments:
            if inst["tradingsymbol"] == symbol and inst["segment"] == "NSE":
                token_map[symbol] = inst["instrument_token"]
                break
        else:
            print(f"[WARN] Token not found for: {symbol}")

    return token_map


def get_instrument_token(instrument: str, exchange: str = 'NFO') -> int:
    """
    Returns the instrument token for a given instrument and exchange.

    Parameters:
    - instrument (str): The trading symbol of the instrument.
    - exchange (str): The exchange of the instrument. Default is 'NFO'.

    Returns:
    - int: The instrument token for the given instrument and exchange.
    """
    df = get_instruments()
    try:
        token = df[(df['tradingsymbol'] == instrument) & (df['exchange'] == exchange)]['instrument_token'].iloc[0]
        return int(token)
    except (IndexError, KeyError):
        logger.log_warning(f"Instrument token for {instrument} not found in the instrument list.")
        return 0


def get_instrument_details(instrument_token: int) -> dict:
    """
    Returns the details for a given instrument token.

    Parameters:
    - instrument_token (int): The token of the instrument.

    Returns:
    - dict: The details for the given instrument token.
    """
    df = get_instruments()
    try:
        details = df[df['instrument_token'] == instrument_token].to_dict('records')[0]
        return details
    except (IndexError, KeyError):
        logger.log_warning(f"Details for instrument token {instrument_token} not found.")
        return {}
