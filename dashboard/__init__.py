"""
TRON Trading Dashboard Package
Real-time monitoring and analytics for the TRON trading system
"""

__version__ = "1.0.0"
__author__ = "TRON Trading System"

from .app import TradingDashboard
from .components import *
from .utils import *

__all__ = [
    "TradingDashboard",
] 