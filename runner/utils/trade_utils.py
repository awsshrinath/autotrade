"""
Utility functions for trading operations.
"""

from datetime import datetime, time as dtime
import pytz

# Set up timezone
try:
    IST = pytz.timezone("Asia/Kolkata")
    PYTZ_AVAILABLE = True
except ImportError:
    IST = None
    PYTZ_AVAILABLE = False


def get_today_date():
    """
    Get today's date in YYYY-MM-DD format.
    
    Returns:
        str: Today's date in YYYY-MM-DD format
    """
    if PYTZ_AVAILABLE and IST:
        return datetime.now(IST).strftime("%Y-%m-%d")
    else:
        return datetime.now().strftime("%Y-%m-%d")


def is_market_open():
    """
    Check if the Indian stock market is currently open.
    
    Returns:
        bool: True if market is open, False otherwise
    """
    if PYTZ_AVAILABLE and IST:
        now = datetime.now(IST)
    else:
        now = datetime.now()
    
    # Check if it's a weekend
    weekday = now.weekday()
    if weekday >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Market hours: 9:15 AM to 3:15 PM IST
    start_time = dtime(9, 15)
    end_time = dtime(15, 15)
    current_time = now.time()
    
    return start_time <= current_time <= end_time


def get_market_status():
    """
    Get detailed market status information.
    
    Returns:
        dict: Market status with details
    """
    if PYTZ_AVAILABLE and IST:
        now = datetime.now(IST)
    else:
        now = datetime.now()
        
    weekday = now.weekday()
    current_time = now.time()
    
    status = {
        "is_open": is_market_open(),
        "current_time": current_time.strftime("%H:%M:%S"),
        "current_date": now.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "is_weekend": weekday >= 5
    }
    
    if status["is_weekend"]:
        status["reason"] = "Weekend"
    elif current_time < dtime(9, 15):
        status["reason"] = "Before market open"
    elif current_time > dtime(15, 15):
        status["reason"] = "After market close"
    else:
        status["reason"] = "Market open"
    
    return status 