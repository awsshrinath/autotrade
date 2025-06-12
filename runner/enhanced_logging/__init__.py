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

# Import all main components from submodules
try:
    from .core_logger import TradingLogger
    from .firestore_logger import FirestoreLogger  
    from .gcs_logger import GCSLogger
    from .lifecycle_manager import LogLifecycleManager
    from .log_types import (
        LogLevel, LogCategory, LogType,
        TradeLogData, CognitiveLogData, ErrorLogData, 
        SystemMetricsData, PerformanceLogData
    )
    
    # Convenience function
    def create_trading_logger(session_id: str, bot_type: str, 
                             enable_firestore: bool = True, 
                             enable_gcs: bool = True) -> TradingLogger:
        """Create a fully configured trading logger"""
        return TradingLogger(
            session_id=session_id,
            bot_type=bot_type, 
            enable_firestore=enable_firestore,
            enable_gcs=enable_gcs
        )
        
    __all__ = [
        'TradingLogger', 'FirestoreLogger', 'GCSLogger', 'LogLifecycleManager',
        'LogLevel', 'LogCategory', 'LogType',
        'TradeLogData', 'CognitiveLogData', 'ErrorLogData', 
        'SystemMetricsData', 'PerformanceLogData',
        'create_trading_logger'
    ]
    
except ImportError as e:
    # Fallback if dependencies are not available
    print(f"Warning: Enhanced logging not fully available: {e}")
    __all__ = []

__version__ = "2.0.0" 