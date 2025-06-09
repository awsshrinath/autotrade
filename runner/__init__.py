#!/usr/bin/env python3
"""
Runner Package
Core trading system modules including configuration, trading logic, and cognitive systems.
"""

# Package metadata
__version__ = "1.0.0"
__author__ = "Tron Trading System"

# Import key components for easier access
try:
    from .config import PAPER_TRADE, OFFLINE_MODE, is_development, is_production
    from .logger import Logger
    __all__ = ["PAPER_TRADE", "OFFLINE_MODE", "is_development", "is_production", "Logger"]
except ImportError:
    # Graceful fallback if imports fail
    __all__ = []
