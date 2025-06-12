"""
Logging types and enums for the TRON Trading System
"""

import datetime
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


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
    ALERT = "alert"


class LogType(Enum):
    """Determines storage destination and retention"""
    # Firestore - Real-time, queryable
    REAL_TIME = "real_time"           # Live trade status, alerts
    DASHBOARD = "dashboard"           # Dashboard data, current day
    COGNITIVE_LIVE = "cognitive_live" # Live cognitive decisions
    
    # GCS - Archival, bulk storage
    ARCHIVAL = "archival"             # Historical data
    BULK = "bulk"                     # Detailed logs, debug traces
    ANALYTICS = "analytics"           # Performance metrics, analysis


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: datetime.datetime
    level: LogLevel
    category: LogCategory
    log_type: LogType
    message: str
    data: Dict[str, Any]
    source: str
    session_id: str
    bot_type: Optional[str] = None
    trade_id: Optional[str] = None
    position_id: Optional[str] = None
    strategy: Optional[str] = None
    symbol: Optional[str] = None
    
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
            elif hasattr(value, 'value'):  # Enum
                return value.value
            else:
                return value
        
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'category': self.category.value,
            'log_type': self.log_type.value,
            'message': self.message,
            'data': serialize_value(self.data),
            'source': self.source,
            'session_id': self.session_id,
            'bot_type': self.bot_type,
            'trade_id': self.trade_id,
            'position_id': self.position_id,
            'strategy': self.strategy,
            'symbol': self.symbol
        }
    
    def get_firestore_ttl(self) -> Optional[datetime.datetime]:
        """Get TTL for Firestore documents based on log type"""
        now = datetime.datetime.utcnow()
        
        # TTL rules for cost optimization
        if self.log_type == LogType.REAL_TIME:
            return now + datetime.timedelta(days=7)  # 1 week for real-time data
        elif self.log_type == LogType.DASHBOARD:
            return now + datetime.timedelta(days=30)  # 1 month for dashboard data
        elif self.log_type == LogType.COGNITIVE_LIVE:
            return now + datetime.timedelta(days=14)  # 2 weeks for cognitive data
        else:
            return None  # No TTL for other types (they go to GCS anyway)


@dataclass
class TradeLogData:
    """Standard trade log data structure"""
    trade_id: str
    symbol: str
    strategy: str
    bot_type: str
    direction: str
    quantity: int
    entry_price: float
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    exit_price: Optional[float] = None
    status: str = "open"
    pnl: Optional[float] = None
    entry_time: Optional[datetime.datetime] = None
    exit_time: Optional[datetime.datetime] = None
    exit_reason: Optional[str] = None
    confidence_level: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, datetime.datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result


@dataclass 
class CognitiveLogData:
    """Standard cognitive system log data"""
    decision_id: str
    decision_type: str
    confidence_level: float
    reasoning: str
    market_context: Dict[str, Any]
    outcome: Optional[str] = None
    tags: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.__dict__


@dataclass
class ErrorLogData:
    """Standard error log data"""
    error_id: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.__dict__


@dataclass
class SystemMetricsData:
    """System performance metrics data"""
    metric_id: str
    metric_name: str
    metric_value: float
    metric_unit: str
    component: str
    timestamp: datetime.datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = self.__dict__.copy()
        if isinstance(result.get('timestamp'), datetime.datetime):
            result['timestamp'] = result['timestamp'].isoformat()
        return result


@dataclass 
class PerformanceLogData:
    """Performance metrics log data"""
    metric_id: str
    bot_type: str
    metric_type: str
    metric_value: float
    benchmark: Optional[float] = None
    period: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return self.__dict__ 