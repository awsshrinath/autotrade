"""
TRON Trading Dashboard Package
Real-time monitoring and analytics for the TRON trading system
"""

__version__ = "1.0.0"
__author__ = "TRON Trading System"

from dashboard.app import TradingDashboard
from dashboard.components import *
from dashboard.utils import *

__all__ = [
    "TradingDashboard",
] 