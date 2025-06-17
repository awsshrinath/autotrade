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
    from .core_logger import TradingLogger, create_trading_logger as create_core_logger
    from .firestore_logger import FirestoreLogger  
    from .gcs_logger import GCSLogger
    from .lifecycle_manager import LogLifecycleManager
    from .log_types import (
        LogLevel, LogCategory, LogType,
        TradeLogData, CognitiveLogData, ErrorLogData, 
        SystemMetricsData, PerformanceLogData
    )
    from ..config.config_manager import ConfigManager
    import logging
    
    # Convenience function
    def create_trading_logger(
        config_manager: "ConfigManager" = None,
        logger_name: str = "TradingLogger",
        gcp_project_id: str = None,
        log_to_console: bool = True,
        log_to_file: bool = True,
        log_file_name: str = "trading_log.log",
        log_level: int = logging.INFO,
        enable_firestore: bool = False,
        enable_gcs: bool = False,
        gcs_bucket_name: str = None,
        session_id: str = None,
        bot_type: str = None,
        **kwargs,
    ) -> "TradingLogger":
        """
        Factory function to create and configure a TradingLogger instance.
        This acts as a bridge to the core logger, adding configuration management.
        """
        project_id = gcp_project_id
        if config_manager and not project_id:
            project_id = config_manager.get_config().get("gcp", {}).get("project_id")

        # Pass only the relevant arguments to the core logger factory
        return create_core_logger(
            session_id=session_id,
            bot_type=bot_type,
            project_id=project_id,
            enable_firestore=enable_firestore,
            enable_gcs=enable_gcs,
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