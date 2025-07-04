"""
Compatibility module for runner.logger imports.

This module provides backward compatibility for code that imports from runner.logger
by re-exporting the new enhanced logging system.
"""

from runner.enhanced_logging import (
    TradingLogger,
    create_trading_logger,
    LogLevel,
    LogCategory,
    LogType,
    TradeLogData,
    CognitiveLogData,
    ErrorLogData,
    SystemMetricsData,
    PerformanceLogData,
)
from runner.enhanced_logging.core_logger import create_enhanced_logger

# Export all the commonly used classes and functions
__all__ = [
    "TradingLogger",
    "create_trading_logger", 
    "create_enhanced_logger",
    "LogLevel",
    "LogCategory", 
    "LogType",
    "TradeLogData",
    "CognitiveLogData",
    "ErrorLogData",
    "SystemMetricsData",
    "PerformanceLogData",
]