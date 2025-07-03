"""
Core Trading Logger - Orchestrates Firestore and GCS logging
============================================================

Main logger that automatically routes logs to the appropriate storage:
- Real-time data -> Firestore for dashboards
- Bulk/archival data -> GCS for long-term storage
- Intelligent routing based on log type and urgency
"""

import datetime
import time
import threading
from typing import Dict, Any, List, Optional, Union
from .log_types import LogEntry, LogLevel, LogCategory, LogType, TradeLogData, CognitiveLogData, ErrorLogData
from .firestore_logger import FirestoreLogger
from .gcs_logger import GCSLogger
from .lifecycle_manager import LogLifecycleManager


class TradingLogger:
    """
    Main trading logger that intelligently routes logs to Firestore and GCS
    """
    
    def __init__(self, session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.bot_type = bot_type or "unknown"
        self.project_id = project_id
        self.enable_firestore = enable_firestore
        self.enable_gcs = enable_gcs
        
        # Initialize specialized loggers with error handling
        self.firestore_logger = None
        self.gcs_logger = None
        self.lifecycle_manager = None
        
        # Add startup delay to prevent simultaneous initialization
        import random
        startup_delay = random.uniform(0.5, 2.0)  # Random delay between 0.5-2 seconds
        time.sleep(startup_delay)
        
        if self.enable_firestore:
            try:
                self.firestore_logger = FirestoreLogger(project_id)
                print(f"✅ Firestore logger initialized for {self.bot_type}")
            except Exception as e:
                print(f"⚠️ Failed to initialize Firestore logger: {e}")
                self.enable_firestore = False
                
        if self.enable_gcs:
            try:
                self.gcs_logger = GCSLogger(project_id)
                self.lifecycle_manager = LogLifecycleManager(project_id)
                print(f"✅ GCS logger initialized for {self.bot_type}")
            except Exception as e:
                print(f"⚠️ Failed to initialize GCS logger: {e}")
                self.enable_gcs = False
        
        # Buffering for efficient batch operations
        self.gcs_buffer = []
        self.buffer_size = 50
        self.last_gcs_flush = time.time()
        self.gcs_flush_interval = 300  # 5 minutes
        
        # Background thread for periodic tasks - only start if we have loggers
        if self.firestore_logger or self.gcs_logger:
        self.background_thread = threading.Thread(target=self._background_tasks, daemon=True)
        self.background_thread.start()
        else:
            print(f"⚠️ No loggers available for {self.bot_type}, background thread not started")
        
        # Performance metrics
        self.metrics = {
            'firestore_writes': 0,
            'gcs_writes': 0,
            'errors': 0,
            'start_time': datetime.datetime.now()
        }
        
        # Log initialization with fallback to console if loggers failed
        init_message = f"Trading logger initialized for {self.bot_type}"
        init_data = {
            'session_id': self.session_id,
            'bot_type': self.bot_type,
            'firestore_enabled': self.enable_firestore,
            'gcs_enabled': self.enable_gcs
        }
        
        try:
            self.log_system_event(init_message, init_data)
        except Exception as e:
            # Fallback to console if logging fails
            print(f"✅ {init_message} - {init_data}")
            print(f"⚠️ Initial log failed: {e}")
    
    def _background_tasks(self):
        """Background thread for periodic maintenance tasks"""
        while True:
            try:
                # Only run tasks if loggers are available
                tasks_run = 0
                
                # Flush GCS buffer periodically
                if self.gcs_logger and self.enable_gcs and (time.time() - self.last_gcs_flush > self.gcs_flush_interval or 
                    len(self.gcs_buffer) >= self.buffer_size):
                    self._flush_gcs_buffer()
                    tasks_run += 1
                
                # Flush Firestore batch
                if self.firestore_logger and self.enable_firestore:
                    try:
                    self.firestore_logger.flush_batch()
                        tasks_run += 1
                    except Exception as fb_error:
                        print(f"⚠️ Firestore batch flush failed: {fb_error}")
                
                # If no tasks were run, we might not have any working loggers
                if tasks_run == 0 and not (self.firestore_logger or self.gcs_logger):
                    print(f"🔄 Background tasks: No active loggers for {self.bot_type}")
                
                # Sleep before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ Error in background tasks for {self.bot_type}: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _flush_gcs_buffer(self):
        """Flush buffered entries to GCS"""
        if not self.gcs_buffer or not self.gcs_logger:
            return
        
        try:
            # Group entries by type for efficient archival
            trades = []
            cognitive_data = []
            error_logs = []
            system_logs = []
            
            for entry in self.gcs_buffer:
                if entry.category == LogCategory.TRADE:
                    # Convert to TradeLogData if possible
                    try:
                        trade_data = TradeLogData(**entry.data)
                        trades.append(trade_data)
                    except:
                        system_logs.append(entry)
                elif entry.category == LogCategory.COGNITIVE:
                    try:
                        cognitive_log = CognitiveLogData(**entry.data)
                        cognitive_data.append(cognitive_log)
                    except:
                        system_logs.append(entry)
                elif entry.category == LogCategory.ERROR:
                    try:
                        error_log = ErrorLogData(**entry.data)
                        error_logs.append(error_log)
                    except:
                        system_logs.append(entry)
                else:
                    system_logs.append(entry)
            
            # Archive different types
            if trades:
                self.gcs_logger.archive_trade_logs(trades, self.bot_type)
            if cognitive_data:
                self.gcs_logger.archive_cognitive_data(cognitive_data, self.bot_type)
            if error_logs:
                self.gcs_logger.archive_error_logs(error_logs, self.bot_type)
            if system_logs:
                self.gcs_logger.archive_system_logs(system_logs, self.bot_type)
            
            self.gcs_buffer.clear()
            self.last_gcs_flush = time.time()
            self.metrics['gcs_writes'] += 1
            
        except Exception as e:
            print(f"Error flushing GCS buffer: {e}")
            self.metrics['errors'] += 1
    
    def _route_log(self, entry: LogEntry):
        """Route log entry to appropriate storage based on type"""
        logged_somewhere = False
        
        try:
            # Always log to Firestore for real-time data
            if self.firestore_logger and self.enable_firestore and entry.log_type in [LogType.REAL_TIME, LogType.DASHBOARD, LogType.COGNITIVE_LIVE]:
                try:
                self._log_to_firestore(entry)
                    logged_somewhere = True
                except Exception as fs_error:
                    print(f"⚠️ Firestore logging failed: {fs_error}")
            
            # Always archive to GCS for bulk/archival data
            if self.gcs_logger and self.enable_gcs and entry.log_type in [LogType.ARCHIVAL, LogType.BULK, LogType.ANALYTICS]:
                try:
                self._log_to_gcs(entry)
                    logged_somewhere = True
                except Exception as gcs_error:
                    print(f"⚠️ GCS logging failed: {gcs_error}")
            
            # Some entries go to both (e.g., critical errors)
            if (entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] or 
                entry.category == LogCategory.TRADE):
                # Critical data goes to both for redundancy
                if self.firestore_logger and self.enable_firestore:
                    try:
                    self._log_to_firestore(entry)
                        logged_somewhere = True
                    except Exception as fs_error:
                        print(f"⚠️ Critical Firestore logging failed: {fs_error}")
                        
                if self.gcs_logger and self.enable_gcs:
                    try:
                    self._log_to_gcs(entry)
                        logged_somewhere = True
                    except Exception as gcs_error:
                        print(f"⚠️ Critical GCS logging failed: {gcs_error}")
            
            # If nothing worked, at least log to console as fallback
            if not logged_somewhere:
                timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] {entry.level.value.upper()} {self.bot_type}: {entry.message}")
                if entry.data:
                    print(f"  Data: {entry.data}")
                
        except Exception as e:
            print(f"❌ Critical error routing log for {self.bot_type}: {e}")
            # Last resort console output
            try:
                timestamp = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{timestamp}] FALLBACK {self.bot_type}: {entry.message}")
            except:
                print(f"EMERGENCY LOG {self.bot_type}: {entry.message}")
            self.metrics['errors'] += 1
    
    def _log_to_firestore(self, entry: LogEntry):
        """Log entry to Firestore for real-time access"""
        if not self.firestore_logger:
            return
        try:
            if entry.category == LogCategory.TRADE:
                # Real-time trade status
                trade_data = TradeLogData(**entry.data)
                urgent = entry.level in [LogLevel.ERROR, LogLevel.CRITICAL]
                self.firestore_logger.log_trade_status(trade_data, urgent=urgent)
                
            elif entry.category == LogCategory.ERROR:
                # Alert for errors
                error_data = ErrorLogData(**entry.data)
                severity = "critical" if entry.level == LogLevel.CRITICAL else "high" if entry.level == LogLevel.ERROR else "medium"
                self.firestore_logger.log_alert(error_data, severity=severity)
                
            elif entry.category == LogCategory.SYSTEM:
                # System status update
                self.firestore_logger.log_system_status(
                    self.bot_type,
                    entry.level.value,
                    entry.message,
                    entry.data
                )
                
            elif entry.category == LogCategory.COGNITIVE:
                # Live cognitive state
                cognitive_data = CognitiveLogData(**entry.data)
                self.firestore_logger.log_cognitive_state(cognitive_data)
            
        except Exception as e:
            print(f"Error logging to Firestore: {e}")
            self.metrics['errors'] += 1
    
    def _log_to_gcs(self, entry: LogEntry):
        """Buffer entry for GCS archival"""
        if not self.gcs_logger:
            return
        self.gcs_buffer.append(entry)
        if len(self.gcs_buffer) >= self.buffer_size:
            self._flush_gcs_buffer()
    
    def log_trade_entry(self, trade_data: Union[Dict, TradeLogData], urgent: bool = False):
        """Log a new trade entry"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)
        
        entry = LogEntry(
            timestamp=trade_data.entry_time,
            level=LogLevel.CRITICAL if urgent else LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=LogType.REAL_TIME, # Log to both
            message=f"Trade Entry: {trade_data.symbol}",
            data=trade_data.to_dict(),
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_trade_exit(self, trade_data: Union[Dict, TradeLogData], exit_reason: str = None):
        """Log a trade exit"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)
        
        if exit_reason:
            trade_data.exit_reason = exit_reason
        
        entry = LogEntry(
            timestamp=trade_data.exit_time,
            level=LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=LogType.REAL_TIME, # Log to both
            message=f"Trade Exit: {trade_data.symbol}",
            data=trade_data.to_dict(),
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_cognitive_decision(self, decision_data: Union[Dict, CognitiveLogData]):
        """Log a cognitive decision or reflection"""
        if isinstance(decision_data, dict):
            decision_data = CognitiveLogData(**decision_data)
        
        entry = LogEntry(
            timestamp=decision_data.timestamp,
            level=LogLevel.DEBUG,
            category=LogCategory.COGNITIVE,
            log_type=LogType.COGNITIVE_LIVE, # Log to both
            message=f"Cognitive: {decision_data.decision}",
            data=decision_data.to_dict(),
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  source: str = "unknown", urgent: bool = True):
        """Log an application error with context"""
        import traceback
        error_data = ErrorLogData(
            timestamp=datetime.datetime.now(),
            error_message=str(error),
            error_type=type(error).__name__,
            traceback=traceback.format_exc(),
            context=context or {},
            source=source,
            bot_type=self.bot_type,
            session_id=self.session_id
        )
        
        entry = LogEntry(
            timestamp=error_data.timestamp,
            level=LogLevel.CRITICAL if urgent else LogLevel.ERROR,
            category=LogCategory.ERROR,
            log_type=LogType.REAL_TIME, # Log to both
            message=f"Error in {source}: {error}",
            data=error_data.to_dict(),
            source=source,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
        self.metrics['errors'] += 1
    
    def log_system_event(self, message: str, data: Dict[str, Any] = None, 
                        level: LogLevel = LogLevel.INFO):
        """Log system events and status updates"""
        try:
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            category=LogCategory.SYSTEM,
                log_type=LogType.REAL_TIME,
            message=message,
            data=data or {},
                source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
        except Exception as e:
            # Fallback to console if all logging fails
            print(f"CRITICAL LOGGING FAILURE: {e}")
            print(f"Original message: {message}")
    
    def log_performance_metric(self, metric_name: str, metric_value: Any, 
                              metadata: Dict[str, Any] = None):
        """Log a specific performance metric"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.DEBUG,
            category=LogCategory.PERFORMANCE,
            log_type=LogType.ANALYTICS,
            message=f"Metric: {metric_name} = {metric_value}",
            data={
                "metric_name": metric_name,
                "metric_value": metric_value,
                "metadata": metadata or {}
            },
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_strategy_signal(self, strategy: str, symbol: str, signal_data: Dict[str, Any]):
        """Log a signal generated by a trading strategy"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.STRATEGY,
            log_type=LogType.REAL_TIME,
            message=f"Signal from {strategy} for {symbol}",
            data={
                "strategy": strategy,
                "symbol": symbol,
                "signal": signal_data
            },
            source=strategy,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_market_data(self, data_type: str, data: Dict[str, Any]):
        """Log market data for archival"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.DEBUG,
            category=LogCategory.MARKET_DATA,
            log_type=LogType.ARCHIVAL,
            message=f"Market data received: {data_type}",
            data=data,
            source="market_feed",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_daily_reflection(self, reflection_text: str):
        """Log end-of-day reflections from the cognitive system"""
        cognitive_data = CognitiveLogData(
            timestamp=datetime.datetime.now(),
            decision="daily_reflection",
            reasoning=reflection_text,
            metadata={"source": "daily_summary"}
        )
        entry = LogEntry(
            timestamp=cognitive_data.timestamp,
            level=LogLevel.INFO,
            category=LogCategory.COGNITIVE,
            log_type=LogType.ANALYTICS, # For analysis
            message="Daily Reflection",
            data=cognitive_data.to_dict(),
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
    
    def log_daily_summary(self, summary_data: Dict[str, Any]):
        """Logs the daily summary to Firestore"""
        if self.firestore_logger:
            self.firestore_logger.log_daily_summary(summary_data)
    
    def get_live_trades(self, status: str = None) -> List[Dict]:
        """Fetch live trades from Firestore"""
        return self.firestore_logger.get_live_trades(status=status) if self.firestore_logger else []
    
    def get_live_alerts(self, severity: str = None) -> List[Dict]:
        """Fetch live alerts from Firestore"""
        return self.firestore_logger.get_live_alerts(severity=severity) if self.firestore_logger else []
    
    def get_system_status(self) -> Dict[str, Dict]:
        """Fetch system status from all bots"""
        return self.firestore_logger.get_system_status() if self.firestore_logger else {}
    
    def get_performance_history(self, days: int = 30) -> List[Dict]:
        """Fetch historical performance data"""
        # This might involve querying both GCS and Firestore
        return self.gcs_logger.get_performance_history(self.bot_type, days=days) if self.gcs_logger else []
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Generate a report on logging and operational costs"""
        report = {"firestore": {}, "gcs": {}}
        if self.firestore_logger:
            report['firestore'] = self.firestore_logger.estimate_costs()
        # Add GCS cost estimation later
        return report
    
    def run_cleanup(self):
        """Run log cleanup and archival tasks"""
        if self.lifecycle_manager:
            self.lifecycle_manager.apply_policies()
    
    def optimize_costs(self):
        """Run cost optimization tasks"""
        # Placeholder for future cost-saving measures
        pass
    
    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics for the logger"""
        self.metrics['uptime_minutes'] = (datetime.datetime.now() - self.metrics['start_time']).total_seconds() / 60
        self.metrics['gcs_buffer_size'] = len(self.gcs_buffer)
        if self.firestore_logger:
            self.metrics['firestore_pending_writes'] = self.firestore_logger.get_batch_size()
        return self.metrics
    
    def flush_all(self):
        """Manually flush all buffers"""
        if self.firestore_logger:
            self.firestore_logger.flush_batch()
        if self.gcs_logger:
            self._flush_gcs_buffer()

    def force_upload_to_gcs(self):
        """Forces immediate upload of the GCS buffer"""
            self._flush_gcs_buffer()

    def shutdown(self):
        """Gracefully shutdown the logger, flushing all buffers"""
        print(f"Shutting down logger for {self.bot_type}...")
            self.flush_all()
        # Give a moment for background tasks to finish
        time.sleep(2)
        # Note: The background thread is a daemon, so it will exit automatically
        print("Logger shutdown complete.")
    
    def __del__(self):
        # Ensure buffers are flushed on object deletion
        try:
                self.shutdown()
        except Exception:
            # Avoid errors during interpreter shutdown
            pass


# EnhancedLogger class for backward compatibility and simpler interface
class EnhancedLogger(TradingLogger):
    """
    A simplified interface to the TradingLogger for easier adoption.
    This maintains backward compatibility with older parts of the system.
    """
    def __init__(self, session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True):
        super().__init__(session_id, bot_type, project_id, enable_firestore, enable_gcs)

    def log(self, level: LogLevel, message: str, category: LogCategory = LogCategory.SYSTEM, data: Dict[str, Any] = None):
        """Generic log method for backward compatibility"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            category=category,
            log_type=LogType.REAL_TIME, # Default to real-time for old logs
            message=message,
            data=data or {},
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def debug(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.DEBUG, message, data=data)

    def info(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.INFO, message, data=data)

    def warning(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.WARNING, message, data=data)

    def error(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.ERROR, message, data=data)

    def critical(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.CRITICAL, message, data=data)


def create_trading_logger(session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True) -> TradingLogger:
    """
    Factory function to create a TradingLogger instance.
    This is the preferred way to get a logger instance.
    """
    # You could add logic here to return a singleton instance if needed
    return TradingLogger(session_id, bot_type, project_id, enable_firestore, enable_gcs)

# Deprecated Logger class for full backward compatibility
class Logger:
    """
    A deprecated logger class for backward compatibility.
    It wraps the new EnhancedLogger.
    """
    def __init__(self, today_date: str):
        self._internal_logger = EnhancedLogger(bot_type="legacy_runner")
        self.today_date = today_date
    
    def log_event(self, event_text: str):
        """Maps old log_event to new info level"""
        # Parse old format if possible
        if "ERROR" in event_text:
            self._internal_logger.error(event_text)
        elif "WARNING" in event_text:
            self._internal_logger.warning(event_text)
        else:
            self._internal_logger.info(event_text)

    def error(self, message: str):
        """Log an error message."""
        self._internal_logger.error(message)
    
    def warning(self, message: str):
        """Log a warning message."""
        self._internal_logger.warning(message)
    
    def info(self, message: str):
        """Log an informational message."""
        self._internal_logger.info(message)
    
    def debug(self, message: str):
        """Log a debug message."""
        self._internal_logger.debug(message)
    
    def critical(self, message: str):
        """Log a critical message."""
        self._internal_logger.critical(message) 