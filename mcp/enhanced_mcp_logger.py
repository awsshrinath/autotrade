"""
Enhanced MCP Logger for TRON Trading System
===========================================

Comprehensive logging system for Module Context Protocol (MCP) operations including:
- Context building and analysis
- Decision-making processes
- Strategy suggestions and code fixes
- Action execution and outcomes
- Performance attribution and learning

Writes to:
- Firestore: Real-time MCP decisions, context analysis, and action logs
- GCS: Historical MCP decision archives, strategy evolution tracking
"""

import datetime
import json
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Import enhanced logging system
try:
    from runner.enhanced_logging import TradingLogger, LogLevel, LogCategory, LogType
    from runner.enhanced_logging.log_types import LogEntry
    ENHANCED_LOGGING_AVAILABLE = True
except ImportError:
    ENHANCED_LOGGING_AVAILABLE = False

from runner.firestore_client import FirestoreClient


class MCPDecisionType(Enum):
    """Types of MCP decisions"""
    STRATEGY_SUGGESTION = "strategy_suggestion"
    CODE_FIX = "code_fix"
    PARAMETER_UPDATE = "parameter_update"
    RISK_ADJUSTMENT = "risk_adjustment"
    REFLECTION_LOG = "reflection_log"
    CONTEXT_ANALYSIS = "context_analysis"
    PERFORMANCE_ATTRIBUTION = "performance_attribution"


class MCPActionStatus(Enum):
    """Status of MCP actions"""
    PENDING = "pending"
    EXECUTED = "executed"
    FAILED = "failed"
    REJECTED = "rejected"
    PARTIAL = "partial"


@dataclass
class MCPContextLog:
    """MCP context building log"""
    trace_id: str
    session_id: str
    bot_type: str
    context_request: Dict[str, Any]
    context_sources: List[str]
    context_data: Dict[str, Any]
    build_time_ms: float
    context_completeness: float  # 0-1 score
    timestamp: datetime.datetime


@dataclass
class MCPDecisionLog:
    """MCP decision making log"""
    trace_id: str
    context_id: str
    decision_type: MCPDecisionType
    input_analysis: Dict[str, Any]
    decision_reasoning: str
    confidence_score: float  # 0-1
    recommended_actions: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    expected_impact: Dict[str, Any]
    decision_time_ms: float
    timestamp: datetime.datetime


@dataclass
class MCPActionLog:
    """MCP action execution log"""
    trace_id: str
    decision_id: str
    action_type: str
    action_details: Dict[str, Any]
    execution_status: MCPActionStatus
    execution_time_ms: float
    result_data: Dict[str, Any]
    error_details: Optional[str]
    impact_metrics: Dict[str, Any]
    timestamp: datetime.datetime


@dataclass
class MCPReflectionLog:
    """MCP reflection and learning log"""
    trace_id: str
    bot_type: str
    reflection_period: str  # 'daily', 'weekly', 'trade'
    performance_data: Dict[str, Any]
    lessons_learned: List[str]
    strategy_adjustments: List[Dict[str, Any]]
    confidence_evolution: Dict[str, float]
    next_actions: List[str]
    timestamp: datetime.datetime


@dataclass
class MCPStrategyLog:
    """MCP strategy evolution log"""
    trace_id: str
    strategy_name: str
    version: str
    changes_made: List[Dict[str, Any]]
    backtesting_results: Dict[str, Any]
    confidence_metrics: Dict[str, float]
    deployment_status: str
    timestamp: datetime.datetime


class EnhancedMCPLogger:
    """Enhanced logger specifically for MCP operations"""
    
    def __init__(self, session_id: str = None, bot_type: str = "mcp"):
        self.session_id = session_id or f"mcp_{int(time.time())}"
        self.bot_type = bot_type
        
        # Initialize enhanced logging if available
        if ENHANCED_LOGGING_AVAILABLE:
            self.trading_logger = TradingLogger(
                session_id=self.session_id,
                bot_type=self.bot_type,
                project_id="autotrade-453303"
            )
            self.use_enhanced = True
        else:
            self.use_enhanced = False
            
        # Initialize Firestore client for MCP-specific collections
        try:
            self.firestore_client = FirestoreClient()
        except Exception as e:
            print(f"Warning: Could not initialize Firestore client: {e}")
            self.firestore_client = None
            
        # Performance tracking
        self.mcp_metrics = {
            'total_contexts': 0,
            'total_decisions': 0,
            'total_actions': 0,
            'successful_actions': 0,
            'avg_decision_time_ms': 0,
            'avg_context_build_time_ms': 0,
            'decision_confidence_avg': 0
        }
        
        print(f"Enhanced MCP Logger initialized - Session: {self.session_id}")
    
    def generate_trace_id(self) -> str:
        """Generate unique trace ID for correlation"""
        return f"mcp_{uuid.uuid4().hex[:8]}_{int(time.time())}"
    
    def log_mcp_context(self, context_request: Dict[str, Any], 
                       context_sources: List[str], context_data: Dict[str, Any],
                       build_time_ms: float, completeness_score: float = 1.0) -> str:
        """Log MCP context building operation"""
        
        trace_id = self.generate_trace_id()
        
        context_log = MCPContextLog(
            trace_id=trace_id,
            session_id=self.session_id,
            bot_type=self.bot_type,
            context_request=context_request,
            context_sources=context_sources,
            context_data=context_data,
            build_time_ms=build_time_ms,
            context_completeness=completeness_score,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="mcp_contexts",
                    document_id=trace_id,
                    data=asdict(context_log)
                )
            except Exception as e:
                print(f"Error logging MCP context to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"MCP Context Built: {len(context_sources)} sources in {build_time_ms:.1f}ms",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data={
                    'trace_id': trace_id,
                    'sources_count': len(context_sources),
                    'context_completeness': completeness_score,
                    'build_time_ms': build_time_ms,
                    'bot_type': self.bot_type
                },
                source="mcp_context"
            )
        
        # Update metrics
        self.mcp_metrics['total_contexts'] += 1
        self.mcp_metrics['avg_context_build_time_ms'] = (
            (self.mcp_metrics['avg_context_build_time_ms'] * (self.mcp_metrics['total_contexts'] - 1) + 
             build_time_ms) / self.mcp_metrics['total_contexts']
        )
        
        return trace_id
    
    def log_mcp_decision(self, context_id: str, decision_type: MCPDecisionType,
                        input_analysis: Dict[str, Any], reasoning: str,
                        confidence: float, actions: List[Dict[str, Any]],
                        risk_assessment: Dict[str, Any], expected_impact: Dict[str, Any],
                        decision_time_ms: float) -> str:
        """Log MCP decision making process"""
        
        trace_id = self.generate_trace_id()
        
        decision_log = MCPDecisionLog(
            trace_id=trace_id,
            context_id=context_id,
            decision_type=decision_type,
            input_analysis=input_analysis,
            decision_reasoning=reasoning,
            confidence_score=confidence,
            recommended_actions=actions,
            risk_assessment=risk_assessment,
            expected_impact=expected_impact,
            decision_time_ms=decision_time_ms,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="mcp_decisions",
                    document_id=trace_id,
                    data=asdict(decision_log)
                )
            except Exception as e:
                print(f"Error logging MCP decision to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"MCP Decision: {decision_type.value} (confidence: {confidence:.2f})",
                LogLevel.INFO,
                LogCategory.STRATEGY,
                data={
                    'trace_id': trace_id,
                    'context_id': context_id,
                    'decision_type': decision_type.value,
                    'confidence_score': confidence,
                    'actions_count': len(actions),
                    'decision_time_ms': decision_time_ms,
                    'reasoning_snippet': reasoning[:100] + "..." if len(reasoning) > 100 else reasoning
                },
                source="mcp_decision"
            )
        
        # Update metrics
        self.mcp_metrics['total_decisions'] += 1
        self.mcp_metrics['avg_decision_time_ms'] = (
            (self.mcp_metrics['avg_decision_time_ms'] * (self.mcp_metrics['total_decisions'] - 1) + 
             decision_time_ms) / self.mcp_metrics['total_decisions']
        )
        self.mcp_metrics['decision_confidence_avg'] = (
            (self.mcp_metrics['decision_confidence_avg'] * (self.mcp_metrics['total_decisions'] - 1) + 
             confidence) / self.mcp_metrics['total_decisions']
        )
        
        return trace_id
    
    def log_mcp_action(self, decision_id: str, action_type: str, 
                      action_details: Dict[str, Any], execution_status: MCPActionStatus,
                      execution_time_ms: float, result_data: Dict[str, Any],
                      error_details: str = None, impact_metrics: Dict[str, Any] = None) -> str:
        """Log MCP action execution"""
        
        trace_id = self.generate_trace_id()
        
        action_log = MCPActionLog(
            trace_id=trace_id,
            decision_id=decision_id,
            action_type=action_type,
            action_details=action_details,
            execution_status=execution_status,
            execution_time_ms=execution_time_ms,
            result_data=result_data,
            error_details=error_details,
            impact_metrics=impact_metrics or {},
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="mcp_actions",
                    document_id=trace_id,
                    data=asdict(action_log)
                )
            except Exception as e:
                print(f"Error logging MCP action to Firestore: {e}")
        
        # Determine log level based on status
        log_level = LogLevel.INFO
        if execution_status == MCPActionStatus.FAILED:
            log_level = LogLevel.ERROR
        elif execution_status == MCPActionStatus.PARTIAL:
            log_level = LogLevel.WARNING
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"MCP Action: {action_type} - {execution_status.value}",
                log_level,
                LogCategory.TRADE,
                data={
                    'trace_id': trace_id,
                    'decision_id': decision_id,
                    'action_type': action_type,
                    'execution_status': execution_status.value,
                    'execution_time_ms': execution_time_ms,
                    'has_error': error_details is not None,
                    'impact_metrics': impact_metrics
                },
                source="mcp_action"
            )
        
        # Update metrics
        self.mcp_metrics['total_actions'] += 1
        if execution_status == MCPActionStatus.EXECUTED:
            self.mcp_metrics['successful_actions'] += 1
        
        return trace_id
    
    def log_mcp_reflection(self, reflection_period: str, performance_data: Dict[str, Any],
                          lessons_learned: List[str], strategy_adjustments: List[Dict[str, Any]],
                          confidence_evolution: Dict[str, float], next_actions: List[str]) -> str:
        """Log MCP reflection and learning process"""
        
        trace_id = self.generate_trace_id()
        
        reflection_log = MCPReflectionLog(
            trace_id=trace_id,
            bot_type=self.bot_type,
            reflection_period=reflection_period,
            performance_data=performance_data,
            lessons_learned=lessons_learned,
            strategy_adjustments=strategy_adjustments,
            confidence_evolution=confidence_evolution,
            next_actions=next_actions,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="mcp_reflections",
                    document_id=trace_id,
                    data=asdict(reflection_log)
                )
            except Exception as e:
                print(f"Error logging MCP reflection to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"MCP Reflection: {reflection_period} - {len(lessons_learned)} lessons",
                LogLevel.INFO,
                LogCategory.PERFORMANCE,
                data={
                    'trace_id': trace_id,
                    'reflection_period': reflection_period,
                    'lessons_count': len(lessons_learned),
                    'adjustments_count': len(strategy_adjustments),
                    'next_actions_count': len(next_actions),
                    'avg_confidence': sum(confidence_evolution.values()) / len(confidence_evolution) if confidence_evolution else 0
                },
                source="mcp_reflection"
            )
        
        return trace_id
    
    def log_mcp_strategy_evolution(self, strategy_name: str, version: str,
                                  changes_made: List[Dict[str, Any]],
                                  backtesting_results: Dict[str, Any],
                                  confidence_metrics: Dict[str, float],
                                  deployment_status: str) -> str:
        """Log MCP strategy evolution and deployment"""
        
        trace_id = self.generate_trace_id()
        
        strategy_log = MCPStrategyLog(
            trace_id=trace_id,
            strategy_name=strategy_name,
            version=version,
            changes_made=changes_made,
            backtesting_results=backtesting_results,
            confidence_metrics=confidence_metrics,
            deployment_status=deployment_status,
            timestamp=datetime.datetime.now()
        )
        
        # Log to Firestore
        if self.firestore_client:
            try:
                self.firestore_client.log_document(
                    collection="mcp_strategies",
                    document_id=trace_id,
                    data=asdict(strategy_log)
                )
            except Exception as e:
                print(f"Error logging MCP strategy to Firestore: {e}")
        
        # Log to enhanced system
        if self.use_enhanced:
            self.trading_logger.log_event(
                f"MCP Strategy: {strategy_name} v{version} - {deployment_status}",
                LogLevel.INFO,
                LogCategory.STRATEGY,
                data={
                    'trace_id': trace_id,
                    'strategy_name': strategy_name,
                    'version': version,
                    'changes_count': len(changes_made),
                    'deployment_status': deployment_status,
                    'confidence_metrics': confidence_metrics
                },
                source="mcp_strategy"
            )
        
        return trace_id
    
    def get_mcp_performance_summary(self) -> Dict[str, Any]:
        """Get MCP performance metrics summary"""
        success_rate = (self.mcp_metrics['successful_actions'] / 
                       self.mcp_metrics['total_actions']) if self.mcp_metrics['total_actions'] > 0 else 0
        
        return {
            'session_id': self.session_id,
            'metrics': {
                **self.mcp_metrics,
                'action_success_rate': success_rate
            },
            'timestamp': datetime.datetime.now().isoformat()
        }
    
    def archive_mcp_session_logs(self) -> bool:
        """Archive current session's MCP logs to GCS"""
        if not self.use_enhanced:
            return False
            
        try:
            # Get session summary
            summary = self.get_mcp_performance_summary()
            
            # Archive via enhanced logger
            self.trading_logger.log_event(
                "MCP Session Complete - Archiving Logs",
                LogLevel.INFO,
                LogCategory.SYSTEM,
                data=summary,
                source="mcp_session_archive"
            )
            
            return True
        except Exception as e:
            print(f"Error archiving MCP session logs: {e}")
            return False


# Global MCP logger instance
_mcp_logger = None

def get_mcp_logger(session_id: str = None, bot_type: str = "mcp") -> EnhancedMCPLogger:
    """Get or create global MCP logger instance"""
    global _mcp_logger
    if _mcp_logger is None:
        _mcp_logger = EnhancedMCPLogger(session_id, bot_type)
    return _mcp_logger

def create_mcp_logger(session_id: str = None, bot_type: str = "mcp") -> EnhancedMCPLogger:
    """Create new MCP logger instance"""
    return EnhancedMCPLogger(session_id, bot_type) 