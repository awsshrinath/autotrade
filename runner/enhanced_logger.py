"""
Enhanced Logging System for TRON Trading System - UPDATED
Comprehensive logging with optimized Firestore and GCS bucket integration
Now uses the new runner.logging module for cost-optimized storage
"""

import datetime
import json
import os
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Import the new optimized logging system
try:
    from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory, LogType
    from runner.enhanced_logging.log_types import TradeLogData, CognitiveLogData, ErrorLogData
    NEW_LOGGING_AVAILABLE = True
except ImportError:
    NEW_LOGGING_AVAILABLE = False
    print("Warning: New logging system not available. Using legacy mode.")

# Legacy imports for backward compatibility
try:
    from google.cloud import storage
    from google.cloud import firestore
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("Warning: Google Cloud libraries not available. GCS logging disabled.")

from runner.firestore_client import FirestoreClient


# Legacy enums for backward compatibility
class LegacyLogLevel(Enum):
    """Log levels for structured logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LegacyLogCategory(Enum):
    """Log categories for better organization"""
    SYSTEM = "system"
    TRADE = "trade"
    POSITION = "position"
    STRATEGY = "strategy"
    RISK = "risk"
    PERFORMANCE = "performance"
    ERROR = "error"
    COGNITIVE = "cognitive"
    MARKET_DATA = "market_data"
    RECOVERY = "recovery"


@dataclass
class LegacyLogEntry:
    """Structured log entry for backward compatibility"""
    timestamp: datetime.datetime
    level: LegacyLogLevel
    category: LegacyLogCategory
    message: str
    data: Dict[str, Any]
    source: str
    session_id: str
    trade_id: Optional[str] = None
    position_id: Optional[str] = None
    strategy: Optional[str] = None
    symbol: Optional[str] = None
    bot_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        def serialize_value(value):
            """Helper to serialize datetime and other objects"""
            if isinstance(value, datetime.datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                return value
        
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'data': serialize_value(self.data),
            'source': self.source,
            'session_id': self.session_id,
            'trade_id': self.trade_id,
            'position_id': self.position_id,
            'strategy': self.strategy,
            'symbol': self.symbol,
            'bot_type': self.bot_type
        }


class EnhancedLogger:
    """Enhanced logging system with optimized Firestore and GCS integration"""
    
    def __init__(self, session_id: str = None, project_id: str = None, 
                 enable_gcs: bool = True, enable_firestore: bool = True,
                 bot_type: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'autotrade-453303')
        self.bot_type = bot_type or "enhanced"
        
        # Use new optimized logging system if available
        if NEW_LOGGING_AVAILABLE:
            self.trading_logger = TradingLogger(
                session_id=self.session_id,
                bot_type=self.bot_type,
                project_id=self.project_id
            )
            self.use_new_system = True
            print("Using new optimized logging system")
        else:
            # Fallback to legacy system
            self.use_new_system = False
            self.enable_gcs = enable_gcs and GCS_AVAILABLE
            self.enable_firestore = enable_firestore and GCS_AVAILABLE and FirestoreClient is not None
            self._setup_legacy_system()
            print("Using legacy logging system")
        
        # Date for organizing logs
        self.today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Performance tracking
        self.performance_metrics = {
            'logs_written': 0,
            'firestore_writes': 0,
            'gcs_uploads': 0,
            'errors': 0,
            'start_time': datetime.datetime.now()
        }
        
        self.log_event("Enhanced logging system initialized", LegacyLogLevel.INFO, LegacyLogCategory.SYSTEM)
    
    def _setup_legacy_system(self):
        """Setup legacy logging components"""
        # Local logging setup
        self._setup_local_logging()
        
        # GCS setup
        if self.enable_gcs:
            self._setup_gcs_client()
        
        # Firestore setup
        if self.enable_firestore:
            self._setup_firestore_client()
    
    def _setup_local_logging(self):
        """Setup local file logging"""
        self.log_folder = f"logs/{self.today_date}"
        os.makedirs(self.log_folder, exist_ok=True)
        
        # Different log files for different purposes
        self.log_files = {
            'main': f"{self.log_folder}/enhanced_log.jsonl",
            'trades': f"{self.log_folder}/trade_log.jsonl",
            'positions': f"{self.log_folder}/position_log.jsonl",
            'errors': f"{self.log_folder}/error_log.jsonl",
            'performance': f"{self.log_folder}/performance_log.jsonl",
            'system': f"{self.log_folder}/system_log.jsonl"
        }
    
    def _setup_gcs_client(self):
        """Setup Google Cloud Storage client"""
        try:
            self.gcs_client = storage.Client(project=self.project_id)
            print("Legacy GCS client initialized")
        except Exception as e:
            print(f"Error setting up legacy GCS client: {e}")
            self.enable_gcs = False
    
    def _setup_firestore_client(self):
        """Setup Firestore client"""
        try:
            self.firestore_client = FirestoreClient()
            print("Legacy Firestore client initialized")
        except Exception as e:
            print(f"Error setting up legacy Firestore client: {e}")
            self.enable_firestore = False
    
    def log_event(self, message: str, level: LegacyLogLevel = LegacyLogLevel.INFO, 
                  category: LegacyLogCategory = LegacyLogCategory.SYSTEM, 
                  data: Dict[str, Any] = None, trade_id: str = None, 
                  position_id: str = None, strategy: str = None, 
                  symbol: str = None, source: str = "enhanced_logger"):
        """Log a structured event"""
        
        if self.use_new_system:
            # Use new optimized logging system
            self._log_with_new_system(message, level, category, data, trade_id, 
                                    position_id, strategy, symbol, source)
        else:
            # Use legacy system
            self._log_with_legacy_system(message, level, category, data, trade_id, 
                                       position_id, strategy, symbol, source)
        
        self.performance_metrics['logs_written'] += 1
    
    def _log_with_new_system(self, message: str, level: LegacyLogLevel, 
                           category: LegacyLogCategory, data: Dict[str, Any], 
                           trade_id: str, position_id: str, strategy: str, 
                           symbol: str, source: str):
        """Log using the new optimized system"""
        # Convert legacy enums to new enums
        new_level = self._convert_level(level)
        new_category = self._convert_category(category)
        
        if category == LegacyLogCategory.TRADE:
            # Use specialized trade logging
            if data and 'trade_data' in data:
                try:
                    trade_data = TradeLogData(**data['trade_data'])
                    self.trading_logger.log_trade_entry(trade_data)
                    return
                except Exception as e:
                    print(f"Error creating TradeLogData: {e}")
        
        elif category == LegacyLogCategory.ERROR:
            # Use specialized error logging
            if data and 'error' in data:
                try:
                    error_data = ErrorLogData(
                        error_id=data.get('error_id', f"error_{int(time.time())}"),
                        error_type=data.get('error_type', 'UnknownError'),
                        error_message=data.get('error_message', message),
                        stack_trace=data.get('stack_trace'),
                        context=data.get('context', {})
                    )
                    self.trading_logger.firestore_logger.log_alert(error_data)
                    return
                except Exception as e:
                    print(f"Error creating ErrorLogData: {e}")
        
        elif category == LegacyLogCategory.COGNITIVE:
            # Use specialized cognitive logging
            if data and 'decision_data' in data:
                try:
                    cognitive_data = CognitiveLogData(**data['decision_data'])
                    self.trading_logger.log_cognitive_decision(cognitive_data)
                    return
                except Exception as e:
                    print(f"Error creating CognitiveLogData: {e}")
        
        # Default to system event logging
        self.trading_logger.log_system_event(message, data or {}, new_level)
    
    def _log_with_legacy_system(self, message: str, level: LegacyLogLevel, 
                              category: LegacyLogCategory, data: Dict[str, Any], 
                              trade_id: str, position_id: str, strategy: str, 
                              symbol: str, source: str):
        """Log using the legacy system"""
        entry = LegacyLogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            category=category,
            message=message,
            data=data or {},
            source=source,
            session_id=self.session_id,
            trade_id=trade_id,
            position_id=position_id,
            strategy=strategy,
            symbol=symbol,
            bot_type=self.bot_type
        )
        
        # Write to local file
        self._write_to_local_file(entry)
        
        # Write to console
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} [{level.value}] [{category.value}] {message}")
    
    def _write_to_local_file(self, entry: LegacyLogEntry):
        """Write log entry to local file"""
        try:
            # Determine which file to write to
            file_key = 'main'
            if entry.category == LegacyLogCategory.TRADE:
                file_key = 'trades'
            elif entry.category == LegacyLogCategory.POSITION:
                file_key = 'positions'
            elif entry.category == LegacyLogCategory.ERROR:
                file_key = 'errors'
            elif entry.category == LegacyLogCategory.PERFORMANCE:
                file_key = 'performance'
            elif entry.category == LegacyLogCategory.SYSTEM:
                file_key = 'system'
            
            with open(self.log_files[file_key], 'a', encoding='utf-8') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
                
        except Exception as e:
            print(f"Error writing to local file: {e}")
    
    def _convert_level(self, legacy_level: LegacyLogLevel) -> LogLevel:
        """Convert legacy log level to new log level"""
        if not NEW_LOGGING_AVAILABLE:
            return legacy_level
        
        mapping = {
            LegacyLogLevel.DEBUG: LogLevel.DEBUG,
            LegacyLogLevel.INFO: LogLevel.INFO,
            LegacyLogLevel.WARNING: LogLevel.WARNING,
            LegacyLogLevel.ERROR: LogLevel.ERROR,
            LegacyLogLevel.CRITICAL: LogLevel.CRITICAL
        }
        return mapping.get(legacy_level, LogLevel.INFO)
    
    def _convert_category(self, legacy_category: LegacyLogCategory) -> LogCategory:
        """Convert legacy log category to new log category"""
        if not NEW_LOGGING_AVAILABLE:
            return legacy_category
        
        mapping = {
            LegacyLogCategory.SYSTEM: LogCategory.SYSTEM,
            LegacyLogCategory.TRADE: LogCategory.TRADE,
            LegacyLogCategory.POSITION: LogCategory.POSITION,
            LegacyLogCategory.STRATEGY: LogCategory.STRATEGY,
            LegacyLogCategory.RISK: LogCategory.RISK,
            LegacyLogCategory.PERFORMANCE: LogCategory.PERFORMANCE,
            LegacyLogCategory.ERROR: LogCategory.ERROR,
            LegacyLogCategory.COGNITIVE: LogCategory.COGNITIVE,
            LegacyLogCategory.MARKET_DATA: LogCategory.MARKET_DATA,
            LegacyLogCategory.RECOVERY: LogCategory.RECOVERY
        }
        return mapping.get(legacy_category, LogCategory.SYSTEM)
    
    # Specialized logging methods for backward compatibility
    
    def log_trade_execution(self, trade_data: Dict[str, Any], success: bool = True):
        """Log trade execution with comprehensive data"""
        level = LegacyLogLevel.INFO if success else LegacyLogLevel.ERROR
        message = f"Trade {'executed' if success else 'failed'}: {trade_data.get('symbol', 'Unknown')}"
        
        if self.use_new_system:
            try:
                # Convert to new format
                trade_log_data = TradeLogData(
                    trade_id=trade_data.get('id', f"trade_{int(time.time())}"),
                    symbol=trade_data.get('symbol', 'UNKNOWN'),
                    strategy=trade_data.get('strategy', 'unknown'),
                    bot_type=trade_data.get('bot_type', self.bot_type),
                    direction=trade_data.get('direction', 'unknown'),
                    quantity=trade_data.get('quantity', 0),
                    entry_price=trade_data.get('entry_price', 0.0),
                    stop_loss=trade_data.get('stop_loss'),
                    target=trade_data.get('target'),
                    status=trade_data.get('status', 'open'),
                    entry_time=datetime.datetime.now(),
                    confidence_level=trade_data.get('confidence_level'),
                    metadata=trade_data.get('metadata', {})
                )
                
                if success:
                    self.trading_logger.log_trade_entry(trade_log_data)
                else:
                    # Log as error
                    error_data = ErrorLogData(
                        error_id=f"trade_error_{int(time.time())}",
                        error_type="TradeExecutionError",
                        error_message=f"Failed to execute trade for {trade_data.get('symbol')}",
                        context=trade_data
                    )
                    self.trading_logger.firestore_logger.log_alert(error_data, severity="high")
            except Exception as e:
                print(f"Error logging trade with new system: {e}")
                # Fallback to legacy
                self.log_event(message, level, LegacyLogCategory.TRADE, 
                             {'trade_data': trade_data, 'execution_success': success})
        else:
            self.log_event(message, level, LegacyLogCategory.TRADE, 
                         {'trade_data': trade_data, 'execution_success': success})
    
    def log_position_update(self, position_data: Dict[str, Any], update_type: str = "update"):
        """Log position updates and monitoring data"""
        message = f"Position {update_type}: {position_data.get('symbol', 'Unknown')}"
        
        if self.use_new_system:
            self.trading_logger.firestore_logger.log_position_update(
                position_id=position_data.get('id', f"pos_{int(time.time())}"),
                position_data=position_data
            )
        else:
            self.log_event(message, LegacyLogLevel.INFO, LegacyLogCategory.POSITION, 
                         {'position_data': position_data, 'update_type': update_type})
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  source: str = "enhanced_logger"):
        """Log error with full context"""
        if self.use_new_system:
            self.trading_logger.log_error(error, context, source)
        else:
            import traceback
            error_data = {
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'context': context or {}
            }
            self.log_event(f"Error: {str(error)}", LegacyLogLevel.ERROR, 
                         LegacyLogCategory.ERROR, error_data, source=source)
    
    def log_performance_metrics(self, metrics: Dict[str, Any], metric_type: str = "general"):
        """Log performance metrics"""
        if self.use_new_system:
            for metric_name, metric_value in metrics.items():
                self.trading_logger.log_performance_metric(
                    metric_name=metric_name,
                    metric_value=metric_value,
                    metadata={'metric_type': metric_type}
                )
        else:
            self.log_event(f"Performance metrics: {metric_type}", 
                         LegacyLogLevel.INFO, LegacyLogCategory.PERFORMANCE, 
                         {'metrics': metrics, 'metric_type': metric_type})
    
    def log_cognitive_decision(self, decision_data: Dict[str, Any]):
        """Log cognitive system decision"""
        if self.use_new_system:
            try:
                cognitive_log_data = CognitiveLogData(
                    decision_id=decision_data.get('decision_id', f"decision_{int(time.time())}"),
                    decision_type=decision_data.get('decision_type', 'unknown'),
                    confidence_level=decision_data.get('confidence_level', 0.5),
                    reasoning=decision_data.get('reasoning', 'No reasoning provided'),
                    market_context=decision_data.get('market_context', {}),
                    outcome=decision_data.get('outcome'),
                    tags=decision_data.get('tags', []),
                    metadata=decision_data.get('metadata', {})
                )
                self.trading_logger.log_cognitive_decision(cognitive_log_data)
            except Exception as e:
                print(f"Error logging cognitive decision with new system: {e}")
                # Fallback to legacy
                self.log_event(f"Cognitive decision: {decision_data.get('decision_type', 'unknown')}", 
                             LegacyLogLevel.INFO, LegacyLogCategory.COGNITIVE, 
                             {'decision_data': decision_data})
        else:
            self.log_event(f"Cognitive decision: {decision_data.get('decision_type', 'unknown')}", 
                         LegacyLogLevel.INFO, LegacyLogCategory.COGNITIVE, 
                         {'decision_data': decision_data})
    
    def log_daily_reflection(self, reflection_text: str):
        """Log GPT daily reflection"""
        if self.use_new_system:
            self.trading_logger.log_daily_reflection(reflection_text)
        else:
            self.log_event("Daily reflection generated", LegacyLogLevel.INFO, 
                         LegacyLogCategory.COGNITIVE, {'reflection': reflection_text})
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logger performance metrics"""
        if self.use_new_system:
            return self.trading_logger.get_metrics()
        else:
            uptime = datetime.datetime.now() - self.performance_metrics['start_time']
            return {
                **self.performance_metrics,
                'uptime_seconds': uptime.total_seconds(),
                'system_type': 'legacy'
            }
    
    def flush_all(self):
        """Flush all pending logs"""
        if self.use_new_system:
            self.trading_logger.flush_all()
        # Legacy system writes immediately, no buffering
    
    def shutdown(self):
        """Graceful shutdown"""
        if self.use_new_system:
            self.trading_logger.shutdown()
        else:
            self.log_event("Enhanced logger shutdown", LegacyLogLevel.INFO, LegacyLogCategory.SYSTEM)
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.shutdown()
        except:
            pass


# Backward compatibility aliases
LogLevel = LegacyLogLevel
LogCategory = LegacyLogCategory
LogEntry = LegacyLogEntry


# Factory function for backward compatibility
def create_enhanced_logger(session_id: str = None, project_id: str = None, 
                          enable_gcs: bool = True, enable_firestore: bool = True,
                          bot_type: str = None) -> EnhancedLogger:
    """
    Factory function to create an EnhancedLogger instance
    
    Args:
        session_id: Unique session identifier
        project_id: Google Cloud project ID
        enable_gcs: Whether to enable GCS logging
        enable_firestore: Whether to enable Firestore logging
        bot_type: Type of bot using the logger
        
    Returns:
        EnhancedLogger instance
    """
    return EnhancedLogger(
        session_id=session_id,
        project_id=project_id, 
        enable_gcs=enable_gcs,
        enable_firestore=enable_firestore,
        bot_type=bot_type
    ) 