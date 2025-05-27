# runner / cognitive_state_machine.py
# Cognitive State Machine with Firestore persistence for state management
# Manages OBSERVING, ANALYZING, EXECUTING states with automatic persistence across cluster recreations

import datetime
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from .gcp_memory_client import GCPMemoryClient


class CognitiveState(Enum):
    INITIALIZING = "initializing"
    OBSERVING = "observing"
    ANALYZING = "analyzing"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    EMERGENCY = "emergency"
    MAINTENANCE = "maintenance"


class StateTransitionTrigger(Enum):
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    NEW_DATA_AVAILABLE = "new_data_available"
    SIGNAL_DETECTED = "signal_detected"
    TRADE_COMPLETED = "trade_completed"
    ERROR_DETECTED = "error_detected"
    MANUAL_OVERRIDE = "manual_override"
    SCHEDULED_MAINTENANCE = "scheduled_maintenance"
    RISK_THRESHOLD_EXCEEDED = "risk_threshold_exceeded"
    PERFORMANCE_REVIEW_TIME = "performance_review_time"


@dataclass
class StateTransition:
    """Record of a state transition with context"""
    id: str
    from_state: str
    to_state: str
    trigger: str
    timestamp: datetime.datetime
    duration_seconds: float
    market_context: Dict[str, Any]
    reason: str
    confidence: float
    success: bool
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateTransition':
        """Create StateTransition from dictionary"""
        return cls(**data)


@dataclass
class StateConfiguration:
    """Configuration for each cognitive state"""
    state: CognitiveState
    max_duration_minutes: Optional[int]
    allowed_transitions: List[CognitiveState]
    entry_actions: List[str]
    exit_actions: List[str]
    periodic_actions: List[str]
    timeout_transition: Optional[CognitiveState]


class CognitiveStateMachine:
    """
    Persistent cognitive state machine for managing trading bot mental states.
    Maintains state across daily Kubernetes cluster recreations using Firestore.
    """
    
    def __init__(self, gcp_client: GCPMemoryClient, logger: logging.Logger = None):
        self.gcp_client = gcp_client
        self.logger = logger or logging.getLogger(__name__)
        
        # Current state tracking
        self.current_state: CognitiveState = CognitiveState.INITIALIZING
        self.state_entry_time: datetime.datetime = datetime.datetime.utcnow()
        self.previous_state: Optional[CognitiveState] = None
        self.state_context: Dict[str, Any] = {}
        
        # State machine configuration
        self.state_configs = self._initialize_state_configs()
        self.transition_callbacks: Dict[str, List[Callable]] = {}
        
        # State persistence
        self._state_document_id = "current_cognitive_state"
        
        # State history for analysis
        self._recent_transitions: List[StateTransition] = []
        
        # Initialize state machine
        self._load_persistent_state()
        self._validate_state_integrity()
    
    def _initialize_state_configs(self) -> Dict[CognitiveState, StateConfiguration]:
        """Initialize state machine configuration"""
        return {
            CognitiveState.INITIALIZING: StateConfiguration(
                        state=CognitiveState.INITIALIZING,
                        max_duration_minutes=5,
                        allowed_transitions=[CognitiveState.OBSERVING, CognitiveState.EMERGENCY],
                        entry_actions=["load_memory", "check_systems", "validate_config"],
                        exit_actions=["log_initialization_complete"],
                    periodic_actions=[],
                timeout_transition=CognitiveState.EMERGENCY
            ),
            
            CognitiveState.OBSERVING: StateConfiguration(
                        state=CognitiveState.OBSERVING,
                        max_duration_minutes=30,
                        allowed_transitions=[CognitiveState.ANALYZING, CognitiveState.REFLECTING, CognitiveState.EMERGENCY],
                        entry_actions=["start_market_monitoring", "reset_analysis_context"],
                        exit_actions=["save_observation_summary"],
                    periodic_actions=["fetch_market_data", "monitor_signals"],
                timeout_transition=CognitiveState.ANALYZING
            ),
            
            CognitiveState.ANALYZING: StateConfiguration(
                        state=CognitiveState.ANALYZING,
                        max_duration_minutes=10,
                        allowed_transitions=[CognitiveState.EXECUTING, CognitiveState.OBSERVING, CognitiveState.EMERGENCY],
                        entry_actions=["start_analysis", "load_strategy_context"],
                        exit_actions=["save_analysis_results"],
                    periodic_actions=["run_strategy_analysis", "check_risk_parameters"],
                timeout_transition=CognitiveState.OBSERVING
            ),
            
            CognitiveState.EXECUTING: StateConfiguration(
                        state=CognitiveState.EXECUTING,
                        max_duration_minutes=15,
                        allowed_transitions=[CognitiveState.OBSERVING, CognitiveState.REFLECTING, CognitiveState.EMERGENCY],
                        entry_actions=["prepare_execution", "validate_trade_params"],
                        exit_actions=["log_execution_complete", "update_positions"],
                    periodic_actions=["monitor_execution", "check_exit_conditions"],
                timeout_transition=CognitiveState.OBSERVING
            ),
            
            CognitiveState.REFLECTING: StateConfiguration(
                        state=CognitiveState.REFLECTING,
                        max_duration_minutes=20,
                        allowed_transitions=[CognitiveState.OBSERVING, CognitiveState.MAINTENANCE, CognitiveState.EMERGENCY],
                        entry_actions=["start_reflection", "gather_performance_data"],
                        exit_actions=["save_reflection_results", "update_learning"],
                    periodic_actions=["analyze_performance", "identify_improvements"],
                timeout_transition=CognitiveState.OBSERVING
            ),
            
            CognitiveState.EMERGENCY: StateConfiguration(
                        state=CognitiveState.EMERGENCY,
                        max_duration_minutes=60,
                        allowed_transitions=[CognitiveState.OBSERVING, CognitiveState.MAINTENANCE],
                        entry_actions=["emergency_procedures", "alert_handlers"],
                        exit_actions=["log_emergency_resolution"],
                    periodic_actions=["monitor_critical_systems", "attempt_recovery"],
                timeout_transition=CognitiveState.MAINTENANCE
            ),
            
            CognitiveState.MAINTENANCE: StateConfiguration(
                    state=CognitiveState.MAINTENANCE,
                max_duration_minutes=None,  # No timeout
                        allowed_transitions=[CognitiveState.INITIALIZING],
                        entry_actions=["start_maintenance_mode"],
                        exit_actions=["complete_maintenance"],
                    periodic_actions=["system_health_checks"],
                timeout_transition=None
            )
        }
    
    def _load_persistent_state(self):
        """Load cognitive state from Firestore on startup"""
        try:
            state_data = self.gcp_client.get_memory_item(
                    'cognitive_state',
                self._state_document_id
            )
            
            if state_data:
                self.current_state = CognitiveState(state_data['current_state'])
                self.state_entry_time = state_data['state_entry_time']
                self.previous_state = CognitiveState(state_data['previous_state']) if state_data.get('previous_state') else None
                self.state_context = state_data.get('state_context', {})
                
                self.logger.info(f"Restored cognitive state: {self.current_state.value}")
                
                # Check if state has been running too long (potential crash recovery)
                current_duration = (datetime.datetime.utcnow() - self.state_entry_time).total_seconds() / 60
                max_duration = self.state_configs[self.current_state].max_duration_minutes
                
                if max_duration and current_duration > max_duration * 2:  # Double the max duration
                    self.logger.warning(f"State {self.current_state.value} exceeded duration, transitioning to recovery")
                    self._force_state_transition(CognitiveState.OBSERVING, StateTransitionTrigger.ERROR_DETECTED)
            else:
                self.logger.info("No persistent state found, starting fresh")
                self._persist_current_state()
        
        except Exception as e:
            self.logger.error(f"Failed to load persistent state: {e}")
            self.current_state = CognitiveState.INITIALIZING
            self.state_entry_time = datetime.datetime.utcnow()
    
    def _persist_current_state(self):
        """Persist current state to Firestore"""
        try:
            state_data = {
                        'current_state': self.current_state.value,
                        'state_entry_time': self.state_entry_time,
                        'previous_state': self.previous_state.value if self.previous_state else None,
                    'state_context': self.state_context,
                'last_updated': datetime.datetime.utcnow()
            }
            
            success = self.gcp_client.store_memory_item(
                        'cognitive_state',
                    self._state_document_id,
                state_data
            )
            
            if not success:
                self.logger.error("Failed to persist cognitive state")
        
        except Exception as e:
            self.logger.error(f"Error persisting state: {e}")
    
    def _validate_state_integrity(self):
        """Validate state machine integrity and fix issues"""
        try:
            # Check if current state is valid
            if self.current_state not in self.state_configs:
                self.logger.error(f"Invalid state detected: {self.current_state}")
                self._force_state_transition(CognitiveState.INITIALIZING, StateTransitionTrigger.ERROR_DETECTED)
                return
            
            # Check state duration
            config = self.state_configs[self.current_state]
            if config.max_duration_minutes:
                duration_minutes = (datetime.datetime.utcnow() - self.state_entry_time).total_seconds() / 60
                
                if duration_minutes > config.max_duration_minutes:
                    self.logger.warning(f"State timeout detected for {self.current_state.value}")
                    if config.timeout_transition:
                        self.transition_to(config.timeout_transition, StateTransitionTrigger.MANUAL_OVERRIDE)
                    else:
                        self._force_state_transition(CognitiveState.OBSERVING, StateTransitionTrigger.ERROR_DETECTED)
            
            self.logger.debug("State integrity validation passed")
        
        except Exception as e:
            self.logger.error(f"State integrity validation failed: {e}")
            self._force_state_transition(CognitiveState.EMERGENCY, StateTransitionTrigger.ERROR_DETECTED)
    
    def transition_to(self, new_state: CognitiveState, trigger: StateTransitionTrigger,
                         reason: str = "", confidence: float = 1.0, 
                     context: Dict[str, Any] = None) -> bool:
        """Transition to new cognitive state with validation and persistence"""
        
        # Validate transition
        if not self._is_valid_transition(self.current_state, new_state):
            self.logger.warning(f"Invalid transition: {self.current_state.value} -> {new_state.value}")
            return False
        
        # Calculate duration in current state
        current_time = datetime.datetime.utcnow()
        duration_seconds = (current_time - self.state_entry_time).total_seconds()
        
        # Execute exit actions for current state
        self._execute_state_actions(self.current_state, "exit_actions")
        
        # Create transition record
        transition = StateTransition(
                    id=f"transition_{int(current_time.timestamp())}",
                    from_state=self.current_state.value,
                    to_state=new_state.value,
                    trigger=trigger.value,
                    timestamp=current_time,
                    duration_seconds=duration_seconds,
                    market_context=context or {},
                    reason=reason,
                    confidence=confidence,
                success=True,
            metadata={}
        )
        
        # Update state
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_entry_time = current_time
        self.state_context = context or {}
        
        # Persist state and transition
        self._persist_current_state()
        self._record_state_transition(transition)
        
        # Execute entry actions for new state
        self._execute_state_actions(new_state, "entry_actions")
        
        # Trigger callbacks
        self._trigger_transition_callbacks(transition)
        
        self.logger.info(f"State transition: {transition.from_state} -> {transition.to_state} (trigger: {trigger.value})")
        return True
    
    def _is_valid_transition(self, from_state: CognitiveState, to_state: CognitiveState) -> bool:
        """Check if state transition is valid according to configuration"""
        if from_state not in self.state_configs:
            return False
        
        config = self.state_configs[from_state]
        return to_state in config.allowed_transitions
    
    def _force_state_transition(self, new_state: CognitiveState, trigger: StateTransitionTrigger):
        """Force state transition without validation (for error recovery)"""
        current_time = datetime.datetime.utcnow()
        duration_seconds = (current_time - self.state_entry_time).total_seconds()
        
        transition = StateTransition(
                    id=f"forced_transition_{int(current_time.timestamp())}",
                    from_state=self.current_state.value,
                    to_state=new_state.value,
                    trigger=trigger.value,
                    timestamp=current_time,
                    duration_seconds=duration_seconds,
                    market_context={},
                    reason="Forced transition for error recovery",
                    confidence=0.5,
                success=True,
            metadata={'forced': True}
        )
        
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_entry_time = current_time
        self.state_context = {}
        
        self._persist_current_state()
        self._record_state_transition(transition)
        
        self.logger.warning(f"Forced state transition: {transition.from_state} -> {transition.to_state}")
    
    def _execute_state_actions(self, state: CognitiveState, action_type: str):
        """Execute configured actions for state entry / exit"""
        try:
            config = self.state_configs[state]
            actions = getattr(config, action_type, [])
            
            for action in actions:
                self.logger.debug(f"Executing {action_type} action: {action}")
                # Action execution would be implemented by the cognitive system
                # This is just logging for now
        
        except Exception as e:
            self.logger.error(f"Failed to execute {action_type} for {state.value}: {e}")
    
    def _record_state_transition(self, transition: StateTransition):
        """Record state transition in Firestore"""
        try:
            success = self.gcp_client.store_memory_item(
                        'state_transitions',
                    transition.id,
                transition.to_dict()
            )
            
            if success:
                # Add to recent transitions cache
                self._recent_transitions.append(transition)
                
                # Keep only recent transitions in memory
                if len(self._recent_transitions) > 50:
                    self._recent_transitions.pop(0)
            
        except Exception as e:
            self.logger.error(f"Failed to record state transition: {e}")
    
    def _trigger_transition_callbacks(self, transition: StateTransition):
        """Trigger registered callbacks for state transitions"""
        callback_key = f"{transition.from_state}_{transition.to_state}"
        
        if callback_key in self.transition_callbacks:
            for callback in self.transition_callbacks[callback_key]:
                try:
                    callback(transition)
                except Exception as e:
                    self.logger.error(f"State transition callback failed: {e}")
    
    def register_transition_callback(self, from_state: CognitiveState, to_state: CognitiveState,
                                   callback: Callable[[StateTransition], None]):
        """Register callback for specific state transition"""
        callback_key = f"{from_state.value}_{to_state.value}"
        
        if callback_key not in self.transition_callbacks:
            self.transition_callbacks[callback_key] = []
        
        self.transition_callbacks[callback_key].append(callback)
    
    def get_current_state(self) -> CognitiveState:
        """Get current cognitive state"""
        return self.current_state
    
    def get_state_duration(self) -> float:
        """Get duration in current state (minutes)"""
        return (datetime.datetime.utcnow() - self.state_entry_time).total_seconds() / 60
    
    def get_state_context(self) -> Dict[str, Any]:
        """Get current state context"""
        return self.state_context.copy()
    
    def update_state_context(self, updates: Dict[str, Any]):
        """Update current state context"""
        self.state_context.update(updates)
        self._persist_current_state()
    
    def get_recent_transitions(self, limit: int = 10) -> List[StateTransition]:
        """Get recent state transitions"""
        return self._recent_transitions[-limit:]
    
    def get_state_history(self, hours: int = 24) -> List[StateTransition]:
        """Get state transition history from Firestore"""
        try:
            cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
            
            transitions_data = self.gcp_client.query_memory_collection(
                        'state_transitions',
                        filters=[('timestamp', '>=', cutoff_time)],
                    order_by='timestamp',
                limit=100
            )
            
            return [StateTransition.from_dict(data) for data in transitions_data]
        
        except Exception as e:
            self.logger.error(f"Failed to get state history: {e}")
            return []
    
    def get_state_analytics(self) -> Dict[str, Any]:
        """Get analytics on state machine performance"""
        recent_transitions = self.get_state_history(hours=24)
        
        if not recent_transitions:
            return {
                        'total_transitions': 0,
                        'average_state_duration': 0,
                    'state_distribution': {},
                'most_common_trigger': None
            }
        
        # Calculate analytics
        state_durations = {}
        state_counts = {}
        trigger_counts = {}
        
        for transition in recent_transitions:
            # State duration
            state = transition.from_state
            if state not in state_durations:
                state_durations[state] = []
            state_durations[state].append(transition.duration_seconds / 60)  # Convert to minutes
            
            # State counts
            state_counts[state] = state_counts.get(state, 0) + 1
            
            # Trigger counts
            trigger_counts[transition.trigger] = trigger_counts.get(transition.trigger, 0) + 1
        
        # Calculate averages
        avg_durations = {
            state: sum(durations) / len(durations)
            for state, durations in state_durations.items()
        }
        
        return {
                    'total_transitions': len(recent_transitions),
                    'average_state_duration': sum(avg_durations.values()) / len(avg_durations) if avg_durations else 0,
                    'state_distribution': state_counts,
                    'average_state_durations': avg_durations,
                    'trigger_distribution': trigger_counts,
                    'most_common_trigger': max(trigger_counts.items(), key=lambda x: x[1])[0] if trigger_counts else None,
                'current_state': self.current_state.value,
            'current_state_duration': self.get_state_duration()
        }
    
    def emergency_reset(self):
        """Emergency reset of state machine"""
        self.logger.warning("Performing emergency state machine reset")
        
        self.current_state = CognitiveState.INITIALIZING
        self.state_entry_time = datetime.datetime.utcnow()
        self.previous_state = None
        self.state_context = {}
        
        self._persist_current_state()
        
        # Record emergency reset
        emergency_transition = StateTransition(
                    id=f"emergency_reset_{int(datetime.datetime.utcnow().timestamp())}",
                    from_state="unknown",
                    to_state=CognitiveState.INITIALIZING.value,
                    trigger=StateTransitionTrigger.ERROR_DETECTED.value,
                    timestamp=datetime.datetime.utcnow(),
                    duration_seconds=0,
                    market_context={},
                    reason="Emergency state machine reset",
                    confidence=0.0,
                success=True,
            metadata={'emergency_reset': True}
        )
        
        self._record_state_transition(emergency_transition)
        self.logger.warning("Emergency state machine reset completed")
    
    def health_check(self) -> Dict[str, bool]:
        """Perform health check on state machine"""
        health = {
                    'state_valid': False,
                    'duration_valid': False,
                'persistence_working': False,
            'transitions_recorded': False
        }
        
        try:
            # Check if current state is valid
            health['state_valid'] = self.current_state in self.state_configs
            
            # Check state duration
            config = self.state_configs[self.current_state]
            if config.max_duration_minutes:
                duration = self.get_state_duration()
                health['duration_valid'] = duration <= config.max_duration_minutes * 1.5  # 50% tolerance
            else:
                health['duration_valid'] = True
            
            # Test persistence
            test_data = {'test': True, 'timestamp': datetime.datetime.utcnow()}
            success = self.gcp_client.store_memory_item('cognitive_state', 'health_test', test_data)
            if success:
                self.gcp_client.delete_memory_item('cognitive_state', 'health_test')
            health['persistence_working'] = success
            
            # Check recent transitions
            health['transitions_recorded'] = len(self._recent_transitions) > 0
        
        except Exception as e:
            self.logger.error(f"State machine health check failed: {e}")
        
        return health
