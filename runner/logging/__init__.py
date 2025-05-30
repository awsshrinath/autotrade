"""
TRON Trading System - Optimized Logging Architecture
=====================================================

This module provides a comprehensive logging system optimized for cost and performance:

1. **Firestore**: Real-time, queryable data for dashboards and alerts
   - Trade status updates (open/closed)
   - Live errors and warnings
   - Cognitive decisions and state transitions
   - Current day GPT reflections

2. **GCS**: Bulk storage and archival for long-term analysis
   - Trade entry/exit logs (JSON/CSV)
   - Historical GPT reflections
   - System performance metrics
   - Debug traces and detailed logs

3. **Lifecycle Management**: Automatic cleanup of old data to minimize costs
   - GCS bucket lifecycle policies
   - Firestore TTL for temporary data
   - Version tagging for duplicates

Usage:
    from runner.logging import TradingLogger, FirestoreLogger, GCSLogger
    
    # Main logger with both backends
    logger = TradingLogger(session_id="trading_session", bot_type="stock-trader")
    
    # Log real-time trade
    logger.log_trade_status(trade_data, status="open")  # -> Firestore
    
    # Archive detailed logs
    logger.archive_trade_details(trade_data)  # -> GCS
"""

from .core_logger import TradingLogger
from .firestore_logger import FirestoreLogger, FirestoreCollections
from .gcs_logger import GCSLogger, GCSBuckets
from .log_types import LogLevel, LogCategory, LogType
from .lifecycle_manager import LogLifecycleManager

__all__ = [
    'TradingLogger',
    'FirestoreLogger', 
    'GCSLogger',
    'LogLevel',
    'LogCategory', 
    'LogType',
    'FirestoreCollections',
    'GCSBuckets',
    'LogLifecycleManager'
]

__version__ = "2.0.0" 