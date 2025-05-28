"""
Enhanced Logging System for TRON Trading System
Comprehensive logging with Firestore and GCS bucket integration
Structured logging for trades, positions, system events, and performance metrics
"""

import datetime
import json
import os
import gzip
import pickle
import threading
import time
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import queue

try:
    from google.cloud import storage
    from google.cloud import firestore
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("Warning: Google Cloud libraries not available. GCS logging disabled.")

from runner.firestore_client import FirestoreClient


class LogLevel(Enum):
    """Log levels for structured logging"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
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
class LogEntry:
    """Structured log entry"""
    timestamp: datetime.datetime
    level: LogLevel
    category: LogCategory
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
    """Enhanced logging system with Firestore and GCS integration"""
    
    def __init__(self, session_id: str = None, project_id: str = None, 
                 enable_gcs: bool = True, enable_firestore: bool = True):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT', 'autotrade-453303')
        self.enable_gcs = enable_gcs and GCS_AVAILABLE
        self.enable_firestore = enable_firestore and GCS_AVAILABLE and FirestoreClient is not None
        
        # Date for organizing logs
        self.today_date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Local logging setup
        self._setup_local_logging()
        
        # GCS setup
        if self.enable_gcs:
            self._setup_gcs_client()
        
        # Firestore setup
        if self.enable_firestore:
            self._setup_firestore_client()
        
        # Async logging queue
        self.log_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="EnhancedLogger")
        self.background_thread = threading.Thread(target=self._background_logger, daemon=True)
        self.background_thread.start()
        
        # Performance tracking
        self.performance_metrics = {
            'logs_written': 0,
            'firestore_writes': 0,
            'gcs_uploads': 0,
            'errors': 0,
            'start_time': datetime.datetime.now()
        }
        
        # Log buffers for batch operations
        self.log_buffer = []
        self.buffer_size = 50
        self.last_flush = time.time()
        self.flush_interval = 30  # seconds
        
        self.log_event("Enhanced logging system initialized", LogLevel.INFO, LogCategory.SYSTEM)
    
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
        
        # Setup Python logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{self.log_folder}/python_log.log"),
                logging.StreamHandler()
            ]
        )
        self.python_logger = logging.getLogger('EnhancedLogger')
    
    def _setup_gcs_client(self):
        """Setup Google Cloud Storage client for pod execution"""
        try:
            # For pod execution, the service account will be automatically detected
            self.gcs_client = storage.Client(project=self.project_id)
            
            # Environment-based bucket configuration
            env_prefix = os.getenv('ENVIRONMENT', 'prod')
            if env_prefix == 'prod':
                env_prefix = ''
            else:
                env_prefix = f"{env_prefix}-"
            
            # Use environment variables for bucket names if available
            self.buckets = {
                'logs': os.getenv('GCS_LOGS_BUCKET', f"{env_prefix}tron-trading-logs"),
                'trades': os.getenv('GCS_TRADES_BUCKET', f"{env_prefix}tron-trade-data"),
                'performance': os.getenv('GCS_PERFORMANCE_BUCKET', f"{env_prefix}tron-analysis-reports"),
                'backups': os.getenv('GCS_BACKUPS_BUCKET', f"{env_prefix}tron-memory-backups")
            }
            
            # Verify bucket access
            for bucket_name in self.buckets.values():
                try:
                    bucket = self.gcs_client.bucket(bucket_name)
                    bucket.reload()  # Test access
                    self.python_logger.info(f"Successfully connected to GCS bucket: {bucket_name}")
                except Exception as e:
                    self.python_logger.warning(f"Cannot access GCS bucket {bucket_name}: {e}")
            
            self.python_logger.info("GCS client initialized successfully for pod execution")
            
        except Exception as e:
            self.python_logger.error(f"Failed to initialize GCS client: {e}")
            self.enable_gcs = False
    
    def _setup_firestore_client(self):
        """Setup Firestore client for pod execution"""
        try:
            # For pod execution, the service account will be automatically detected
            self.firestore_client = FirestoreClient()
            self.python_logger.info("Firestore client initialized successfully for pod execution")
        except Exception as e:
            self.python_logger.error(f"Failed to initialize Firestore client: {e}")
            self.enable_firestore = False
    
    def _background_logger(self):
        """Background thread for async logging operations"""
        while True:
            try:
                # Process log queue
                while not self.log_queue.empty():
                    try:
                        log_entry = self.log_queue.get_nowait()
                        self._process_log_entry(log_entry)
                    except queue.Empty:
                        break
                    except Exception as e:
                        self.python_logger.error(f"Error processing log entry: {e}")
                
                # Flush buffers periodically
                if time.time() - self.last_flush > self.flush_interval:
                    self._flush_buffers()
                
                time.sleep(1)  # Small delay to prevent busy waiting
                
            except Exception as e:
                self.python_logger.error(f"Error in background logger: {e}")
                time.sleep(5)  # Longer delay on error
    
    def _process_log_entry(self, log_entry: LogEntry):
        """Process a single log entry"""
        try:
            # Add to buffer
            self.log_buffer.append(log_entry)
            
            # Write to local file immediately for critical logs
            if log_entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]:
                self._write_to_local_file(log_entry)
            
            # Flush buffer if it's full
            if len(self.log_buffer) >= self.buffer_size:
                self._flush_buffers()
                
        except Exception as e:
            self.python_logger.error(f"Error processing log entry: {e}")
    
    def _write_to_local_file(self, log_entry: LogEntry):
        """Write log entry to appropriate local file"""
        try:
            # Determine target file based on category
            if log_entry.category == LogCategory.TRADE:
                target_file = self.log_files['trades']
            elif log_entry.category == LogCategory.POSITION:
                target_file = self.log_files['positions']
            elif log_entry.category == LogCategory.ERROR:
                target_file = self.log_files['errors']
            elif log_entry.category == LogCategory.PERFORMANCE:
                target_file = self.log_files['performance']
            elif log_entry.category == LogCategory.SYSTEM:
                target_file = self.log_files['system']
            else:
                target_file = self.log_files['main']
            
            # Write to file
            with open(target_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry.to_dict()) + '\n')
            
            # Also write to main log
            if target_file != self.log_files['main']:
                with open(self.log_files['main'], 'a', encoding='utf-8') as f:
                    f.write(json.dumps(log_entry.to_dict()) + '\n')
            
            # Console output for important logs
            if log_entry.level in [LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]:
                print(f"[{log_entry.timestamp.strftime('%H:%M:%S')}] {log_entry.level.value}: {log_entry.message}")
            
            self.performance_metrics['logs_written'] += 1
            
        except Exception as e:
            self.python_logger.error(f"Error writing to local file: {e}")
            self.performance_metrics['errors'] += 1
    
    def _flush_buffers(self):
        """Flush log buffers to Firestore and GCS"""
        if not self.log_buffer:
            return
        
        try:
            # Write all buffered logs to local files
            for log_entry in self.log_buffer:
                self._write_to_local_file(log_entry)
            
            # Upload to Firestore
            if self.enable_firestore:
                self._upload_to_firestore(self.log_buffer.copy())
            
            # Upload to GCS
            if self.enable_gcs:
                self._upload_to_gcs(self.log_buffer.copy())
            
            # Clear buffer
            self.log_buffer.clear()
            self.last_flush = time.time()
            
        except Exception as e:
            self.python_logger.error(f"Error flushing buffers: {e}")
            self.performance_metrics['errors'] += 1
    
    def _upload_to_firestore(self, log_entries: List[LogEntry]):
        """Upload log entries to Firestore"""
        try:
            for log_entry in log_entries:
                # Store in appropriate collection based on category
                collection_name = f"enhanced_logs_{log_entry.category.value}"
                
                # Add to Firestore
                doc_data = log_entry.to_dict()
                doc_data['date'] = self.today_date
                doc_data['session_id'] = self.session_id
                
                self.firestore_client.db.collection(collection_name).add(doc_data)
                self.performance_metrics['firestore_writes'] += 1
            
        except Exception as e:
            self.python_logger.error(f"Error uploading to Firestore: {e}")
            self.performance_metrics['errors'] += 1
    
    def _upload_to_gcs(self, log_entries: List[LogEntry]):
        """Upload log entries to GCS"""
        try:
            # Group logs by category
            categorized_logs = {}
            for log_entry in log_entries:
                category = log_entry.category.value
                if category not in categorized_logs:
                    categorized_logs[category] = []
                categorized_logs[category].append(log_entry.to_dict())
            
            # Upload each category to appropriate bucket
            for category, logs in categorized_logs.items():
                bucket_name = self._get_bucket_for_category(category)
                if bucket_name:
                    self._upload_logs_to_bucket(bucket_name, category, logs)
            
        except Exception as e:
            self.python_logger.error(f"Error uploading to GCS: {e}")
            self.performance_metrics['errors'] += 1
    
    def _get_bucket_for_category(self, category: str) -> Optional[str]:
        """Get appropriate bucket for log category"""
        if category in ['trade', 'position']:
            return self.buckets['trades']
        elif category == 'performance':
            return self.buckets['performance']
        else:
            return self.buckets['logs']
    
    def _upload_logs_to_bucket(self, bucket_name: str, category: str, logs: List[Dict]):
        """Upload logs to specific GCS bucket"""
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            
            # Create compressed JSON data
            json_data = '\n'.join([json.dumps(log) for log in logs])
            compressed_data = gzip.compress(json_data.encode('utf-8'))
            
            # Upload with timestamp
            timestamp = datetime.datetime.now().strftime("%H%M%S")
            blob_name = f"{self.today_date}/{category}/{self.session_id}_{timestamp}.jsonl.gz"
            
            blob = bucket.blob(blob_name)
            blob.upload_from_string(compressed_data, content_type='application/gzip')
            
            self.performance_metrics['gcs_uploads'] += 1
            
        except Exception as e:
            self.python_logger.error(f"Error uploading to bucket {bucket_name}: {e}")
            self.performance_metrics['errors'] += 1
    
    def log_event(self, message: str, level: LogLevel = LogLevel.INFO, 
                  category: LogCategory = LogCategory.SYSTEM, data: Dict[str, Any] = None,
                  trade_id: str = None, position_id: str = None, strategy: str = None,
                  symbol: str = None, bot_type: str = None, source: str = "system"):
        """Log a structured event"""
        log_entry = LogEntry(
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
            bot_type=bot_type
        )
        
        # Add to queue for async processing
        self.log_queue.put(log_entry)
    
    def log_trade_execution(self, trade_data: Dict[str, Any], success: bool = True):
        """Log trade execution with comprehensive data"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Trade {'executed' if success else 'failed'}: {trade_data.get('symbol', 'Unknown')}"
        
        enhanced_data = {
            **trade_data,
            'execution_success': success,
            'execution_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=level,
            category=LogCategory.TRADE,
            data=enhanced_data,
            trade_id=trade_data.get('id'),
            strategy=trade_data.get('strategy'),
            symbol=trade_data.get('symbol'),
            bot_type=trade_data.get('bot_type'),
            source="trade_manager"
        )
        
        # Also log to Firestore trade collection
        if self.enable_firestore and success:
            try:
                self.firestore_client.log_trade(
                    bot_name=trade_data.get('bot_type', 'unknown'),
                    date_str=self.today_date,
                    trade_data=enhanced_data
                )
            except Exception as e:
                self.python_logger.error(f"Error logging trade to Firestore: {e}")
    
    def log_position_update(self, position_data: Dict[str, Any], update_type: str = "update"):
        """Log position updates and monitoring data"""
        message = f"Position {update_type}: {position_data.get('symbol', 'Unknown')}"
        
        enhanced_data = {
            **position_data,
            'update_type': update_type,
            'update_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=LogLevel.INFO,
            category=LogCategory.POSITION,
            data=enhanced_data,
            position_id=position_data.get('id'),
            trade_id=position_data.get('trade_id'),
            strategy=position_data.get('strategy'),
            symbol=position_data.get('symbol'),
            bot_type=position_data.get('bot_type'),
            source="position_monitor"
        )
    
    def log_exit_execution(self, exit_data: Dict[str, Any], success: bool = True):
        """Log position exit execution"""
        level = LogLevel.INFO if success else LogLevel.ERROR
        message = f"Exit {'executed' if success else 'failed'}: {exit_data.get('symbol', 'Unknown')} - {exit_data.get('exit_reason', 'Unknown')}"
        
        enhanced_data = {
            **exit_data,
            'exit_success': success,
            'exit_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=level,
            category=LogCategory.POSITION,
            data=enhanced_data,
            position_id=exit_data.get('position_id'),
            trade_id=exit_data.get('trade_id'),
            strategy=exit_data.get('strategy'),
            symbol=exit_data.get('symbol'),
            bot_type=exit_data.get('bot_type'),
            source="position_monitor"
        )
    
    def log_performance_metrics(self, metrics: Dict[str, Any], metric_type: str = "general"):
        """Log performance metrics and analytics"""
        message = f"Performance metrics: {metric_type}"
        
        enhanced_data = {
            **metrics,
            'metric_type': metric_type,
            'calculation_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=LogLevel.INFO,
            category=LogCategory.PERFORMANCE,
            data=enhanced_data,
            source="performance_tracker"
        )
    
    def log_risk_event(self, risk_data: Dict[str, Any], risk_level: str = "medium"):
        """Log risk management events"""
        level_map = {
            'low': LogLevel.INFO,
            'medium': LogLevel.WARNING,
            'high': LogLevel.ERROR,
            'critical': LogLevel.CRITICAL
        }
        
        level = level_map.get(risk_level, LogLevel.WARNING)
        message = f"Risk event ({risk_level}): {risk_data.get('event', 'Unknown')}"
        
        enhanced_data = {
            **risk_data,
            'risk_level': risk_level,
            'risk_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=level,
            category=LogCategory.RISK,
            data=enhanced_data,
            source="risk_manager"
        )
    
    def log_strategy_signal(self, signal_data: Dict[str, Any], strategy_name: str):
        """Log strategy signals and decisions"""
        message = f"Strategy signal: {strategy_name} - {signal_data.get('signal_type', 'Unknown')}"
        
        enhanced_data = {
            **signal_data,
            'strategy_name': strategy_name,
            'signal_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=LogLevel.INFO,
            category=LogCategory.STRATEGY,
            data=enhanced_data,
            strategy=strategy_name,
            symbol=signal_data.get('symbol'),
            source="strategy_engine"
        )
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, source: str = "system"):
        """Log errors with full context"""
        message = f"Error in {source}: {str(error)}"
        
        error_data = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'error_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.log_event(
            message=message,
            level=LogLevel.ERROR,
            category=LogCategory.ERROR,
            data=error_data,
            source=source
        )
    
    def log_system_health(self, health_data: Dict[str, Any]):
        """Log system health metrics"""
        message = f"System health check: {health_data.get('status', 'Unknown')}"
        
        enhanced_data = {
            **health_data,
            'health_timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id,
            'logger_metrics': self.get_performance_metrics()
        }
        
        self.log_event(
            message=message,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            data=enhanced_data,
            source="health_monitor"
        )
    
    def create_daily_summary(self) -> Dict[str, Any]:
        """Create comprehensive daily summary"""
        try:
            summary = {
                'date': self.today_date,
                'session_id': self.session_id,
                'summary_timestamp': datetime.datetime.now().isoformat(),
                'performance_metrics': self.get_performance_metrics(),
                'log_files': self.log_files,
                'gcs_enabled': self.enable_gcs,
                'firestore_enabled': self.enable_firestore
            }
            
            # Add file sizes
            file_sizes = {}
            for log_type, file_path in self.log_files.items():
                try:
                    if os.path.exists(file_path):
                        file_sizes[log_type] = os.path.getsize(file_path)
                    else:
                        file_sizes[log_type] = 0
                except Exception:
                    file_sizes[log_type] = 0
            
            summary['file_sizes'] = file_sizes
            
            # Log the summary
            self.log_event(
                message="Daily logging summary created",
                level=LogLevel.INFO,
                category=LogCategory.SYSTEM,
                data=summary,
                source="enhanced_logger"
            )
            
            return summary
            
        except Exception as e:
            self.python_logger.error(f"Error creating daily summary: {e}")
            return {}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get logger performance metrics"""
        runtime = (datetime.datetime.now() - self.performance_metrics['start_time']).total_seconds()
        
        return {
            **self.performance_metrics,
            'runtime_seconds': runtime,
            'logs_per_second': self.performance_metrics['logs_written'] / max(runtime, 1),
            'error_rate': self.performance_metrics['errors'] / max(self.performance_metrics['logs_written'], 1),
            'queue_size': self.log_queue.qsize(),
            'buffer_size': len(self.log_buffer)
        }
    
    def shutdown(self):
        """Graceful shutdown of logging system - Fixed for pod execution"""
        try:
            self.log_event("Enhanced logger shutting down", LogLevel.INFO, LogCategory.SYSTEM)
            
            # Flush all remaining logs
            self._flush_buffers()
            
            # Wait for background thread to finish
            if self.background_thread.is_alive():
                self.background_thread.join(timeout=10)
            
            # Shutdown executor - Fixed for older Python versions
            try:
                self.executor.shutdown(wait=True)
            except TypeError:
                # Fallback for older Python versions without timeout parameter
                self.executor.shutdown(wait=True)
            
            # Create final summary
            summary = self.create_daily_summary()
            
            # Upload final summary to GCS
            if self.enable_gcs:
                try:
                    bucket = self.gcs_client.bucket(self.buckets['logs'])
                    blob_name = f"{self.today_date}/summaries/{self.session_id}_final_summary.json"
                    blob = bucket.blob(blob_name)
                    blob.upload_from_string(json.dumps(summary, indent=2))
                except Exception as e:
                    self.python_logger.error(f"Error uploading final summary: {e}")
            
            print(f"Enhanced logger shutdown complete. Session: {self.session_id}")
            
        except Exception as e:
            self.python_logger.error(f"Error during logger shutdown: {e}")


# Factory function for creating enhanced logger
def create_enhanced_logger(session_id: str = None, project_id: str = None,
                          enable_gcs: bool = True, enable_firestore: bool = True) -> EnhancedLogger:
    """Create an enhanced logger instance"""
    return EnhancedLogger(
        session_id=session_id,
        project_id=project_id,
        enable_gcs=enable_gcs,
        enable_firestore=enable_firestore
    )


# Backward compatibility wrapper
class Logger:
    """Backward compatibility wrapper for existing Logger class"""
    
    def __init__(self, today_date: str):
        self.enhanced_logger = create_enhanced_logger(
            session_id=f"legacy_{today_date}_{int(time.time())}"
        )
        self.today_date = today_date
    
    def log_event(self, event_text: str):
        """Legacy log_event method"""
        self.enhanced_logger.log_event(
            message=event_text,
            level=LogLevel.INFO,
            category=LogCategory.SYSTEM,
            source="legacy_logger"
        ) 