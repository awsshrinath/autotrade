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
    
    def __init__(self, session_id: str = None, bot_type: str = None, project_id: str = None):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.bot_type = bot_type or "unknown"
        self.project_id = project_id
        
        # Initialize specialized loggers
        self.firestore_logger = FirestoreLogger(project_id)
        self.gcs_logger = GCSLogger(project_id)
        self.lifecycle_manager = LogLifecycleManager(project_id)
        
        # Buffering for efficient batch operations
        self.gcs_buffer = []
        self.buffer_size = 50
        self.last_gcs_flush = time.time()
        self.gcs_flush_interval = 300  # 5 minutes
        
        # Background thread for periodic tasks
        self.background_thread = threading.Thread(target=self._background_tasks, daemon=True)
        self.background_thread.start()
        
        # Performance metrics
        self.metrics = {
            'firestore_writes': 0,
            'gcs_writes': 0,
            'errors': 0,
            'start_time': datetime.datetime.now()
        }
        
        # Log initialization
        self.log_system_event("Trading logger initialized", {
            'session_id': self.session_id,
            'bot_type': self.bot_type
        })
    
    def _background_tasks(self):
        """Background thread for periodic maintenance tasks"""
        while True:
            try:
                # Flush GCS buffer periodically
                if (time.time() - self.last_gcs_flush > self.gcs_flush_interval or 
                    len(self.gcs_buffer) >= self.buffer_size):
                    self._flush_gcs_buffer()
                
                # Flush Firestore batch
                self.firestore_logger.flush_batch()
                
                # Sleep before next check
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in background tasks: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _flush_gcs_buffer(self):
        """Flush buffered entries to GCS"""
        if not self.gcs_buffer:
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
        try:
            # Always log to Firestore for real-time data
            if entry.log_type in [LogType.REAL_TIME, LogType.DASHBOARD, LogType.COGNITIVE_LIVE]:
                self._log_to_firestore(entry)
            
            # Always archive to GCS for bulk/archival data
            if entry.log_type in [LogType.ARCHIVAL, LogType.BULK, LogType.ANALYTICS]:
                self._log_to_gcs(entry)
            
            # Some entries go to both (e.g., critical errors)
            if (entry.level in [LogLevel.ERROR, LogLevel.CRITICAL] or 
                entry.category == LogCategory.TRADE):
                # Critical data goes to both for redundancy
                self._log_to_firestore(entry)
                self._log_to_gcs(entry)
                
        except Exception as e:
            print(f"Error routing log: {e}")
            self.metrics['errors'] += 1
    
    def _log_to_firestore(self, entry: LogEntry):
        """Log entry to Firestore for real-time access"""
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
                
            elif entry.category == LogCategory.COGNITIVE:
                # Cognitive decisions
                cognitive_data = CognitiveLogData(**entry.data)
                self.firestore_logger.log_cognitive_decision(cognitive_data, self.bot_type)
                
            elif entry.category == LogCategory.SYSTEM:
                # System status
                self.firestore_logger.log_system_status(self.bot_type, entry.data)
                
            elif entry.category == LogCategory.PERFORMANCE:
                # Dashboard metrics
                metric_name = entry.data.get('metric_name', 'unknown')
                metric_value = entry.data.get('metric_value')
                self.firestore_logger.log_dashboard_metric(metric_name, metric_value, self.bot_type)
            
            self.metrics['firestore_writes'] += 1
            
        except Exception as e:
            print(f"Error logging to Firestore: {e}")
            self.metrics['errors'] += 1
    
    def _log_to_gcs(self, entry: LogEntry):
        """Buffer entry for GCS archival"""
        self.gcs_buffer.append(entry)
        
        # Auto-flush if buffer is full
        if len(self.gcs_buffer) >= self.buffer_size:
            self._flush_gcs_buffer()
    
    # High-level logging methods
    
    def log_trade_entry(self, trade_data: Union[Dict, TradeLogData], urgent: bool = False):
        """Log trade entry (goes to both Firestore and GCS)"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)
        
        log_type = LogType.REAL_TIME if urgent else LogType.DASHBOARD
        
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=log_type,
            message=f"Trade entry: {trade_data.symbol}",
            data=trade_data.to_dict(),
            source="trade_manager",
            session_id=self.session_id,
            bot_type=self.bot_type,
            trade_id=trade_data.trade_id,
            symbol=trade_data.symbol,
            strategy=trade_data.strategy
        )
        
        self._route_log(entry)
    
    def log_trade_exit(self, trade_data: Union[Dict, TradeLogData], exit_reason: str = None):
        """Log trade exit"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)
        
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=LogType.REAL_TIME,  # Exits are always urgent for dashboards
            message=f"Trade exit: {trade_data.symbol} - {exit_reason or 'Unknown reason'}",
            data={**trade_data.to_dict(), 'exit_reason': exit_reason},
            source="trade_manager",
            session_id=self.session_id,
            bot_type=self.bot_type,
            trade_id=trade_data.trade_id,
            symbol=trade_data.symbol,
            strategy=trade_data.strategy
        )
        
        self._route_log(entry)
    
    def log_cognitive_decision(self, decision_data: Union[Dict, CognitiveLogData]):
        """Log cognitive system decision"""
        if isinstance(decision_data, dict):
            decision_data = CognitiveLogData(**decision_data)
        
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.COGNITIVE,
            log_type=LogType.COGNITIVE_LIVE,
            message=f"Cognitive decision: {decision_data.decision_type}",
            data=decision_data.to_dict(),
            source="cognitive_system",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        
        self._route_log(entry)
    
    def log_error(self, error: Exception, context: Dict[str, Any] = None, 
                  source: str = "unknown", urgent: bool = True):
        """Log error with full context"""
        import traceback
        
        error_data = ErrorLogData(
            error_id=f"error_{int(time.time())}",
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {}
        )
        
        log_type = LogType.REAL_TIME if urgent else LogType.ARCHIVAL
        
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.ERROR,
            category=LogCategory.ERROR,
            log_type=log_type,
            message=f"Error: {error_data.error_type} - {error_data.error_message}",
            data=error_data.to_dict(),
            source=source,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        
        self._route_log(entry)
    
    def log_system_event(self, message: str, data: Dict[str, Any] = None, 
                        level: LogLevel = LogLevel.INFO):
        """Log system events"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level,
            category=LogCategory.SYSTEM,
            log_type=LogType.DASHBOARD,
            message=message,
            data=data or {},
            source="system",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        
        self._route_log(entry)
    
    def log_performance_metric(self, metric_name: str, metric_value: Any, 
                              metadata: Dict[str, Any] = None):
        """Log performance metrics"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.PERFORMANCE,
            log_type=LogType.ANALYTICS,
            message=f"Performance metric: {metric_name} = {metric_value}",
            data={
                'metric_name': metric_name,
                'metric_value': metric_value,
                'metadata': metadata or {}
            },
            source="performance_monitor",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        
        self._route_log(entry)
    
    def log_strategy_signal(self, strategy: str, symbol: str, signal_data: Dict[str, Any]):
        """Log strategy signals"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.STRATEGY,
            log_type=LogType.DASHBOARD,
            message=f"Strategy signal: {strategy} for {symbol}",
            data=signal_data,
            source="strategy_engine",
            session_id=self.session_id,
            bot_type=self.bot_type,
            strategy=strategy,
            symbol=symbol
        )
        
        self._route_log(entry)
    
    def log_market_data(self, data_type: str, data: Dict[str, Any]):
        """Log market data updates"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.DEBUG,
            category=LogCategory.MARKET_DATA,
            log_type=LogType.BULK,  # Market data goes to GCS
            message=f"Market data: {data_type}",
            data=data,
            source="market_data",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        
        self._route_log(entry)
    
    def log_daily_reflection(self, reflection_text: str):
        """Log GPT daily reflection"""
        # Store in Firestore for current day dashboard
        self.firestore_logger.log_daily_reflection(self.bot_type, reflection_text)
        
        # Also archive to GCS for historical analysis
        reflection_data = [{
            'date': datetime.datetime.now().strftime("%Y-%m-%d"),
            'bot_type': self.bot_type,
            'reflection': reflection_text,
            'timestamp': datetime.datetime.now().isoformat()
        }]
        
        self.gcs_logger.archive_gpt_reflections(reflection_data, self.bot_type)
    
    def log_daily_summary(self, summary_data: Dict[str, Any]):
        """Log daily performance summary"""
        self.firestore_logger.log_daily_summary(self.bot_type, summary_data)
        
        # Also archive performance metrics to GCS
        self.gcs_logger.archive_performance_metrics(summary_data, self.bot_type)
    
    # Query methods (delegate to appropriate logger)
    
    def get_live_trades(self, status: str = None) -> List[Dict]:
        """Get live trades from Firestore"""
        return self.firestore_logger.get_live_trades(self.bot_type, status)
    
    def get_live_alerts(self, severity: str = None) -> List[Dict]:
        """Get live alerts from Firestore"""
        return self.firestore_logger.get_live_alerts(severity)
    
    def get_system_status(self) -> Dict[str, Dict]:
        """Get current system status"""
        return self.firestore_logger.get_system_status()
    
    def get_performance_history(self, days: int = 30) -> List[Dict]:
        """Get performance history from GCS"""
        return self.gcs_logger.get_performance_history(self.bot_type, days)
    
    def get_cost_report(self) -> Dict[str, Any]:
        """Get comprehensive cost report"""
        return self.lifecycle_manager.get_cost_report()
    
    # Lifecycle management
    
    def run_cleanup(self):
        """Run manual cleanup"""
        self.lifecycle_manager.run_daily_cleanup()
    
    def optimize_costs(self):
        """Run cost optimization"""
        self.lifecycle_manager.optimize_storage_costs()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get logger performance metrics"""
        uptime = datetime.datetime.now() - self.metrics['start_time']
        
        return {
            **self.metrics,
            'uptime_seconds': uptime.total_seconds(),
            'gcs_buffer_size': len(self.gcs_buffer),
            'firestore_batch_size': len(self.firestore_logger.pending_writes),
            'gcs_pending_uploads': sum(len(uploads) for uploads in self.gcs_logger.pending_uploads.values())
        }
    
    def flush_all(self):
        """Flush all pending data to storage"""
        try:
            self._flush_gcs_buffer()
            self.firestore_logger.flush_batch()
        except Exception as e:
            print(f"Error flushing all logs: {e}")
            self.metrics['errors'] += 1

    def force_upload_to_gcs(self):
        """Force immediate upload of all buffered data to GCS"""
        try:
            if self.gcs_buffer:
                self._flush_gcs_buffer()
                print(f"Force uploaded {len(self.gcs_buffer)} entries to GCS")
            else:
                print("No buffered entries to upload to GCS")
        except Exception as e:
            print(f"Error in force upload to GCS: {e}")
            self.metrics['errors'] += 1

    def shutdown(self):
        """Clean shutdown - flush all data and stop background tasks"""
        try:
            # Flush all pending data
            self.flush_all()
            
            # Stop background thread gracefully (note: daemon thread will stop with main program)
            
            # Final cleanup
            self.run_cleanup()
            
            print(f"Trading logger shutdown complete. Final metrics: {self.get_metrics()}")
            
        except Exception as e:
            print(f"Error during logger shutdown: {e}")
            self.metrics['errors'] += 1
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            if hasattr(self, 'gcs_buffer'):
                self.shutdown()
        except Exception:
            pass  # Ignore errors during shutdown


# Backward compatibility functions for existing code

def create_trading_logger(session_id: str = None, bot_type: str = None) -> TradingLogger:
    """Create a trading logger instance"""
    return TradingLogger(session_id=session_id, bot_type=bot_type)


# Legacy compatibility wrapper
class Logger:
    """Legacy logger wrapper for backward compatibility"""
    
    def __init__(self, today_date: str):
        self.today_date = today_date
        self.trading_logger = TradingLogger(bot_type="legacy")
    
    def log_event(self, event_text: str):
        """Legacy log_event method"""
        self.trading_logger.log_system_event(event_text)
        
        # Also print to console for backward compatibility
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} {event_text}")
    
    # Add standard logging interface methods for compatibility
    def error(self, message: str):
        """Standard logging error method"""
        self.trading_logger.log_system_event(f"❌ [ERROR] {message}")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} ERROR: {message}")
    
    def warning(self, message: str):
        """Standard logging warning method"""
        self.trading_logger.log_system_event(f"⚠️ [WARNING] {message}")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} WARNING: {message}")
    
    def info(self, message: str):
        """Standard logging info method"""
        self.trading_logger.log_system_event(f"ℹ️ [INFO] {message}")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} INFO: {message}")
    
    def debug(self, message: str):
        """Standard logging debug method"""
        self.trading_logger.log_system_event(f"🔍 [DEBUG] {message}")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} DEBUG: {message}")
    
    def critical(self, message: str):
        """Standard logging critical method"""
        self.trading_logger.log_system_event(f"🚨 [CRITICAL] {message}")
        timestamp = datetime.datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
        print(f"{timestamp} CRITICAL: {message}") 