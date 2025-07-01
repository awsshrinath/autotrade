"""
Compatibility layer for the old runner.logger module.

This module provides backward compatibility for existing code that imports from runner.logger
by re-exporting the enhanced logging system components.
"""

# Import everything from the enhanced logging system
from .enhanced_logging import (
    TradingLogger,
    create_enhanced_logger,
    create_trading_logger,
    FirestoreLogger,
    GCSLogger,
    LogLevel,
    LogCategory,
    LogType,
    TradeLogData,
    CognitiveLogData,
    ErrorLogData,
    SystemMetricsData,
    PerformanceLogData,
)

# Create aliases for backward compatibility
Logger = TradingLogger  # Old Logger class -> TradingLogger

# For compatibility with old create_enhanced_logger calls
# Some files might expect different function signatures
def create_logger(*args, **kwargs):
    """Compatibility function for old create_logger calls"""
    return create_enhanced_logger(*args, **kwargs)

# Export everything that old code might expect
__all__ = [
    "Logger",
    "TradingLogger",
    "create_enhanced_logger",
    "create_trading_logger", 
    "create_logger",
    "FirestoreLogger",
    "GCSLogger",
    "LogLevel",
    "LogCategory",
    "LogType",
    "TradeLogData",
    "CognitiveLogData",
    "ErrorLogData",
    "SystemMetricsData",
    "PerformanceLogData",
] 