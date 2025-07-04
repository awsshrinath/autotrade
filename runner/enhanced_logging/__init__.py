"""
Enhanced Logging System for TRON Trading Platform

This module provides cost-optimized logging with dual storage:
- Firestore: Real-time, queryable data (trades, errors, decisions)
- GCS: Bulk storage with lifecycle management (historical data)

Key Features:
   - Intelligent routing based on data urgency
   - Batch operations for cost efficiency
   - Automatic data compression and archival
   - GCS bucket lifecycle policies
   - Firestore TTL for temporary data
   - Version tagging for duplicates

Usage:
    from runner.enhanced_logging import TradingLogger, FirestoreLogger, GCSLogger
    
    # Main logger with both backends
    logger = TradingLogger(session_id="trading_session", bot_type="stock-trader")
    
    # Log real-time trade
    logger.log_trade(...)
    
    # Log cognitive decision
    logger.log_cognitive(...)
"""

from .core_logger import TradingLogger, create_trading_logger, create_enhanced_logger

try:
    from .firestore_logger import FirestoreLogger
except ImportError:
    FirestoreLogger = None

try:
    from .gcs_logger import GCSLogger
except ImportError:
    GCSLogger = None

try:
    from .lifecycle_manager import LogLifecycleManager
except ImportError:
    LogLifecycleManager = None
from .log_types import (
    LogLevel,
    LogCategory,
    LogType,
    TradeLogData,
    CognitiveLogData,
    ErrorLogData,
    SystemMetricsData,
    PerformanceLogData,
)

__all__ = [
    "TradingLogger",
    "create_trading_logger",
    "create_enhanced_logger",
    "FirestoreLogger",
    "GCSLogger",
    "LogLifecycleManager",
    "LogLevel",
    "LogCategory",
    "LogType",
    "TradeLogData",
    "CognitiveLogData",
    "ErrorLogData",
    "SystemMetricsData",
    "PerformanceLogData",
]

__version__ = "2.0.0" 