"""
Market Data Module

This module contains all market data related functionality split from the original
monolithic market_monitor.py for better organization and maintainability.

Components:
- MarketDataFetcher: Live market data fetching from multiple APIs
- TechnicalIndicators: Technical analysis calculations (ADX, Bollinger Bands, etc.)
- CorrelationMonitor: Cross-market correlation analysis
- MarketRegimeClassifier: Market regime classification logic
"""

from .market_data_fetcher import MarketDataFetcher
from .technical_indicators import TechnicalIndicators

__all__ = [
    'MarketDataFetcher',
    'TechnicalIndicators'
] 