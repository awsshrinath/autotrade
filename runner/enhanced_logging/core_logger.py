import datetime
import json
import os
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Union

try:
    from .gcs_logger import GCSLogger
except ImportError:
    GCSLogger = None
    
try:
    from .firestore_logger import FirestoreLogger
except ImportError:
    FirestoreLogger = None
from .log_types import (CognitiveLogData, ErrorLogData, LogCategory, LogEntry,
                        LogLevel, LogType, TradeLogData)

# Fallback if dependencies are missing
try:
    from google.api_core.exceptions import GoogleAPICallError
except ImportError:
    class GoogleAPICallError(Exception):
        pass

class TradingLogger:
    """
    Unified logger for trading bots, routing logs to different backends
    based on type and urgency.

    - Firestore: For real-time dashboard data, alerts, and live status.
    - GCS: For long-term archival, analytics, and bulk data storage.
    """

    def __init__(self, session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True):
        self.session_id = session_id or f"session_{int(time.time())}"
        self.bot_type = bot_type or "generic_bot"
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")

        self.enable_firestore = enable_firestore
        self.enable_gcs = enable_gcs

        self.firestore_logger = None
        self.gcs_logger = None

        if self.enable_firestore and FirestoreLogger:
            try:
                self.firestore_logger = FirestoreLogger(project_id=self.project_id)
            except Exception as e:
                print(f"⚠️ Failed to initialize FirestoreLogger: {e}")
                self.enable_firestore = False

        if self.enable_gcs and GCSLogger:
            try:
                self.gcs_logger = GCSLogger(project_id=self.project_id)
            except Exception as e:
                print(f"⚠️ Failed to initialize GCSLogger: {e}")
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
                status_data = {
                    "message": entry.message,
                    "level": entry.level.value,
                    **entry.data
                }
                self.firestore_logger.log_system_status(
                    self.bot_type,
                    status_data
                )

            elif entry.category == LogCategory.COGNITIVE:
                # Live cognitive state
                cognitive_data = CognitiveLogData(**entry.data)
                self.firestore_logger.log_cognitive_state(self.bot_type, cognitive_data)

            self.metrics['firestore_writes'] += 1

        except (TypeError, ValueError) as e:
            print(f"Data validation error for Firestore: {e}, Data: {entry.data}")
            self.metrics['errors'] += 1
        except GoogleAPICallError as e:
            print(f"Google API error logging to Firestore: {e}")
            self.metrics['errors'] += 1
            self.enable_firestore = False # Potentially disable on persistent API errors
        except Exception as e:
            print(f"Unexpected error in _log_to_firestore: {e}")
            self.metrics['errors'] += 1

    def _log_to_gcs(self, entry: LogEntry):
        """Buffer log entry for archival in GCS"""
        if not self.gcs_logger:
            return
        self.gcs_buffer.append(entry)
        if len(self.gcs_buffer) >= self.buffer_size:
            self._flush_gcs_buffer()

    def log_trade_entry(self, trade_data: Union[Dict, TradeLogData], urgent: bool = False):
        """Log the entry of a new trade"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)

        entry = LogEntry(
            timestamp=trade_data.entry_time,
            level=LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=LogType.REAL_TIME, # Goes to both
            message=f"Trade Entry: {trade_data.symbol}",
            data=trade_data.to_dict(),
            source=trade_data.strategy,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def log_trade_exit(self, trade_data: Union[Dict, TradeLogData], exit_reason: str = None):
        """Log the exit of a trade"""
        if isinstance(trade_data, dict):
            trade_data = TradeLogData(**trade_data)

        if exit_reason:
            trade_data.exit_reason = exit_reason

        entry = LogEntry(
            timestamp=trade_data.exit_time,
            level=LogLevel.INFO,
            category=LogCategory.TRADE,
            log_type=LogType.REAL_TIME, # Goes to both
            message=f"Trade Exit: {trade_data.symbol}, PnL: {trade_data.pnl:.2f}",
            data=trade_data.to_dict(),
            source=trade_data.strategy,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def log_cognitive_decision(self, decision_data: Union[Dict, CognitiveLogData]):
        """Log a cognitive decision or state change"""
        if isinstance(decision_data, dict):
            decision_data = CognitiveLogData(**decision_data)

        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.COGNITIVE,
            log_type=LogType.COGNITIVE_LIVE,
            message=f"Cognitive: {decision_data.decision_type}",
            data=decision_data.to_dict(),
            source="cognitive_system",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def log_error(self, error: Exception, context: Dict[str, Any] = None,
                  source: str = "unknown", urgent: bool = True):
        """Log an application error"""
        import uuid
        import traceback
        
        error_data = ErrorLogData(
            error_id=str(uuid.uuid4()),
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            context=context or {},
            recovery_attempted=False
        )

        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.CRITICAL if urgent else LogLevel.ERROR,
            category=LogCategory.ERROR,
            log_type=LogType.REAL_TIME, # Errors go to both
            message=f"Error in {source}: {error_data.error_message}",
            data=error_data.to_dict(),
            source=source,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

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
            print(f"Original Message: {message}")

    def log_performance_metric(self, metric_name: str, metric_value: Any,
                              metadata: Dict[str, Any] = None):
        """Log a performance metric for analytics"""
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
            source="performance_monitor",
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
            log_type=LogType.BULK, # Archival
            message=f"Signal from {strategy} for {symbol}",
            data=signal_data,
            source=strategy,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def log_market_data(self, data_type: str, data: Dict[str, Any]):
        """Log market data snapshots for analysis"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.DEBUG,
            category=LogCategory.MARKET_DATA,
            log_type=LogType.BULK,
            message=f"Market data snapshot: {data_type}",
            data=data,
            source="market_data_fetcher",
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)

    def log_daily_reflection(self, reflection_text: str):
        """
        Logs the daily reflection text to GCS.
        This is intended for qualitative, EOD analysis.
        """
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=LogLevel.INFO,
            category=LogCategory.REFLECTION,
            log_type=LogType.ARCHIVAL,
            message="Daily Reflection",
            data={"reflection": reflection_text},
            source=self.bot_type,
            session_id=self.session_id,
            bot_type=self.bot_type
        )
        self._route_log(entry)
        # Force flush for EOD logs
        self._flush_gcs_buffer()

    def log_daily_summary(self, summary_data: Dict[str, Any]):
        self.firestore_logger.log_daily_summary(self.bot_type, summary_data)

    # Backward compatibility methods
    def log_event(self, event_text: str):
        """Legacy method for backward compatibility"""
        self.log_system_event(event_text)
    
    def error(self, message: str):
        """Legacy method for backward compatibility"""
        self.log_error(Exception(message), source=self.bot_type)

    def get_live_trades(self, status: str = None) -> List[Dict]:
        if self.firestore_logger:
            return self.firestore_logger.get_live_trades(self.bot_type, status=status)
        return []

    def get_live_alerts(self, severity: str = None) -> List[Dict]:
        if self.firestore_logger:
            return self.firestore_logger.get_live_alerts(self.bot_type, severity=severity)
        return []

    def get_system_status(self) -> Dict[str, Dict]:
        if self.firestore_logger:
            return self.firestore_logger.get_system_status()
        return {}

    def get_performance_history(self, days: int = 30) -> List[Dict]:
        if self.gcs_logger:
            return self.gcs_logger.query_performance_logs(self.bot_type, days=days)
        return []

    def get_cost_report(self) -> Dict[str, Any]:
        """Generate a cost report based on logged activities"""
        # This is a simplified example. A real implementation would involve
        # more complex logic based on API calls, data storage size, etc.
        report = {
            "firestore_writes": self.metrics['firestore_writes'],
            "gcs_writes": self.metrics['gcs_writes'],
            "estimated_cost": (self.metrics['firestore_writes'] * 0.0001) + (self.metrics['gcs_writes'] * 0.0005)
        }
        return report

    def run_cleanup(self):
        """Run cleanup tasks on old logs"""
        if self.firestore_logger:
            self.firestore_logger.cleanup_old_data("trades", days_to_keep=90)
            self.firestore_logger.cleanup_old_data("alerts", days_to_keep=30)

    def optimize_costs(self):
        """Analyze logging patterns and suggest optimizations"""
        # Example: if a bot is logging too many system events, suggest reducing verbosity
        pass

    def get_metrics(self) -> Dict[str, Any]:
        """Return performance metrics of the logger itself"""
        self.metrics['uptime_minutes'] = (datetime.datetime.now() - self.metrics['start_time']).total_seconds() / 60
        self.metrics['gcs_buffer_size'] = len(self.gcs_buffer)
        return self.metrics

    def flush_all(self):
        """Manually flush all buffers"""
        if self.gcs_logger:
            self._flush_gcs_buffer()
        if self.firestore_logger:
            self.firestore_logger.flush_batch()

    def force_upload_to_gcs(self):
        self._flush_gcs_buffer()

    def shutdown(self):
        """Gracefully shutdown the logger, flushing all buffers."""
        self.log_system_event("Logger shutting down.")
        self.flush_all()
        # Give a moment for background threads to finish
        time.sleep(2)

    def __del__(self):
        # Ensure buffers are flushed on object deletion
        try:
            self.flush_all()
        except Exception:
            # Suppress errors during deletion
            pass


class EnhancedLogger(TradingLogger):
    """
    A simplified wrapper around TradingLogger providing a classic logging interface.
    This is for easy integration with existing code that uses standard log levels.
    """
    def __init__(self, session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True):
        super().__init__(session_id, bot_type, project_id, enable_firestore, enable_gcs)

    def log(self, level: LogLevel, message: str, category: LogCategory = LogCategory.SYSTEM, data: Dict[str, Any] = None):
        """Generic log method"""
        entry = LogEntry(
            timestamp=datetime.datetime.now(),
            level=level, category=category, log_type=LogType.REAL_TIME,
            message=message, data=data or {}, source=self.bot_type,
            session_id=self.session_id, bot_type=self.bot_type
        )
        self._route_log(entry)

    def debug(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.DEBUG, message, data=data)

    def info(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.INFO, message, data=data)

    def warning(self, message: str, data: Dict[str, Any] = None):
        self.log(LogLevel.WARNING, message, data=data)

    def error(self, message: str, data: Dict[str, Any] = None):
        # Errors are logged with more detail
        super().log_error(Exception(message), context=data, source=self.bot_type)

    def critical(self, message: str, data: Dict[str, Any] = None):
        super().log_error(Exception(message), context=data, source=self.bot_type, urgent=True)

# Factory function for easy logger creation
def create_trading_logger(session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True) -> TradingLogger:
    """
    Factory function to create a new trading logger instance.
    - `session_id`: A unique identifier for the current bot session.
    - `bot_type`: The name of the bot (e.g., 'stock-trader', 'options-trader').
    - `project_id`: GCP project ID.
    """
    return TradingLogger(session_id, bot_type, project_id, enable_firestore, enable_gcs)

def create_enhanced_logger(session_id: str = None, bot_type: str = None, project_id: str = None, enable_firestore: bool = True, enable_gcs: bool = True) -> TradingLogger:
    """
    Legacy compatibility function - creates a new trading logger instance.
    - `session_id`: A unique identifier for the current bot session.
    - `bot_type`: The name of the bot (e.g., 'stock-trader', 'options-trader').
    - `project_id`: GCP project ID.
    """
    return TradingLogger(session_id, bot_type, project_id, enable_firestore, enable_gcs)

# Simple logger for use when advanced features are not needed
class Logger:
    """A simple file-based logger."""

    def __init__(self, today_date: str):
        self.log_file = f"logs/log-{today_date}.log"
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

    def log_event(self, event_text: str):
        """Appends a log entry to the daily log file."""
        with open(self.log_file, "a") as f:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {event_text}\n"
            f.write(log_entry)

    # Convenience methods for different log levels
    def error(self, message: str):
        self.log_event(f"ERROR: {message}")

    def warning(self, message: str):
        self.log_event(f"WARNING: {message}")

    def info(self, message: str):
        self.log_event(f"INFO: {message}")

    def debug(self, message: str):
        self.log_event(f"DEBUG: {message}")

    def critical(self, message: str):
        self.log_event(f"CRITICAL: {message}")