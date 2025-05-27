# runner/cognitive_system.py
# Main cognitive system integrating memory, thoughts, state machine, and metacognition
# Human-like cognitive architecture with bulletproof GCP persistence

import datetime
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
import threading
import time
import traceback

from .gcp_memory_client import GCPMemoryClient
from .cognitive_memory import CognitiveMemory, MemoryType, ImportanceLevel
from .thought_journal import ThoughtJournal, DecisionType, ConfidenceLevel, EmotionalState
from .cognitive_state_machine import CognitiveStateMachine, CognitiveState, StateTransitionTrigger
from .metacognition import MetaCognition, DecisionOutcome


@dataclass
class CognitiveConfig:
    """Configuration for cognitive system"""
    project_id: Optional[str] = None
    enable_background_processing: bool = True
    memory_consolidation_interval: int = 3600  # seconds
    thought_archival_interval: int = 86400  # seconds (daily)
    performance_analysis_interval: int = 7200  # seconds (2 hours)
    auto_state_transitions: bool = True
    emergency_recovery_enabled: bool = True


class CognitiveSystem:
    """
    Main cognitive system integrating all cognitive components.
    Provides human-like decision-making, memory, and self-awareness
    with bulletproof persistence across daily cluster recreations.
    """
    
    def __init__(self, config: CognitiveConfig = None, logger: logging.Logger = None):
        self.config = config or CognitiveConfig()
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize GCP client
        self.gcp_client = GCPMemoryClient(
            project_id=self.config.project_id,
            logger=self.logger
        )
        
        # Initialize cognitive components
        self.memory = CognitiveMemory(self.gcp_client, self.logger)
        self.thoughts = ThoughtJournal(self.gcp_client, self.logger)
        self.state_machine = CognitiveStateMachine(self.gcp_client, self.logger)
        self.metacognition = MetaCognition(self.gcp_client, self.logger)
        
        # System state
        self._initialized = False
        self._background_thread = None
        self._shutdown_event = threading.Event()
        
        # Cognitive metrics
        self._cognitive_metrics = {
            'decisions_made': 0,
            'thoughts_recorded': 0,
            'state_transitions': 0,
            'biases_detected': 0,
            'memory_items_stored': 0,
            'system_uptime': datetime.datetime.utcnow()
        }
        
        # Callbacks for external integration
        self._decision_callbacks: List[Callable] = []
        self._state_change_callbacks: List[Callable] = []
        
        # Initialize system
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize cognitive system with recovery capabilities"""
        try:
            self.logger.info("Initializing cognitive system...")
            
            # Set initial state
            self.state_machine.transition_to(
                CognitiveState.INITIALIZING,
                StateTransitionTrigger.MANUAL_OVERRIDE,
                "System startup initialization"
            )
            
            # Perform health checks
            health_status = self._perform_health_checks()
            
            if not all(health_status.values()):
                self.logger.error(f"Health check failed: {health_status}")
                if self.config.emergency_recovery_enabled:
                    self._emergency_recovery()
                else:
                    raise RuntimeError("Cognitive system health check failed")
            
            # Register state transition callbacks
            self._register_state_callbacks()
            
            # Start background processing
            if self.config.enable_background_processing:
                self._start_background_processing()
            
            # Transition to observing state
            self.state_machine.transition_to(
                CognitiveState.OBSERVING,
                StateTransitionTrigger.MANUAL_OVERRIDE,
                "Initialization complete, beginning observation"
            )
            
            self._initialized = True
            self.logger.info("Cognitive system initialization completed successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cognitive system: {e}")
            self.logger.error(traceback.format_exc())
            
            if self.config.emergency_recovery_enabled:
                self._emergency_recovery()
            else:
                raise
    
    def _perform_health_checks(self) -> Dict[str, bool]:
        """Perform comprehensive health checks"""
        health_status = {}
        
        try:
            # GCP connectivity
            gcp_health = self.gcp_client.health_check()
            health_status.update({f"gcp_{k}": v for k, v in gcp_health.items()})
            
            # Memory system
            memory_summary = self.memory.get_memory_summary()
            health_status['memory_loaded'] = memory_summary['memory_loaded']
            
            # State machine
            state_health = self.state_machine.health_check()
            health_status.update({f"state_{k}": v for k, v in state_health.items()})
            
            # Thought journal
            recent_thoughts = self.thoughts.get_recent_thoughts(hours=1)
            health_status['thoughts_accessible'] = len(recent_thoughts) >= 0  # Should not fail
            
            # Metacognition
            meta_summary = self.metacognition.get_metacognitive_summary()
            health_status['metacognition_working'] = 'error' not in meta_summary
            
        except Exception as e:
            self.logger.error(f"Health check error: {e}")
            health_status['health_check_error'] = False
        
        return health_status
    
    def _emergency_recovery(self):
        """Emergency recovery procedures"""
        self.logger.warning("Initiating emergency recovery procedures")
        
        try:
            # Reset state machine
            self.state_machine.emergency_reset()
            
            # Check if we can restore from backup
            snapshot = self.gcp_client.load_latest_memory_snapshot()
            if snapshot:
                self.logger.info("Memory snapshot found, attempting restoration")
                # Memory restoration is handled in CognitiveMemory initialization
            
            # Clear thought cache and reload
            self.thoughts.clear_thought_cache()
            
            # Create disaster recovery backup
            self.gcp_client.create_disaster_recovery_backup()
            
            self.logger.warning("Emergency recovery completed")
            
        except Exception as e:
            self.logger.critical(f"Emergency recovery failed: {e}")
            # Last resort - minimal functionality mode
            self._minimal_functionality_mode()
    
    def _minimal_functionality_mode(self):
        """Activate minimal functionality mode for critical failures"""
        self.logger.critical("Activating minimal functionality mode")
        
        # Disable background processing
        self.config.enable_background_processing = False
        
        # Set emergency state
        self.state_machine.current_state = CognitiveState.EMERGENCY
        
        # Clear all caches
        try:
            self.memory.emergency_memory_reset()
            self.thoughts.clear_thought_cache()
        except:
            pass
    
    def _register_state_callbacks(self):
        """Register callbacks for state transitions"""
        # Observing -> Analyzing
        self.state_machine.register_transition_callback(
            CognitiveState.OBSERVING,
            CognitiveState.ANALYZING,
            self._on_start_analysis
        )
        
        # Analyzing -> Executing
        self.state_machine.register_transition_callback(
            CognitiveState.ANALYZING,
            CognitiveState.EXECUTING,
            self._on_start_execution
        )
        
        # Executing -> Reflecting
        self.state_machine.register_transition_callback(
            CognitiveState.EXECUTING,
            CognitiveState.REFLECTING,
            self._on_start_reflection
        )
        
        # Any -> Emergency
        for state in CognitiveState:
            if state != CognitiveState.EMERGENCY:
                self.state_machine.register_transition_callback(
                    state,
                    CognitiveState.EMERGENCY,
                    self._on_emergency_state
                )
    
    def _on_start_analysis(self, transition):
        """Callback for entering analysis state"""
        self.record_thought(
            "Starting market analysis",
            "Transitioning from observation to analysis phase",
            DecisionType.MARKET_ANALYSIS,
            ConfidenceLevel.MEDIUM
        )
    
    def _on_start_execution(self, transition):
        """Callback for entering execution state"""
        self.record_thought(
            "Beginning trade execution",
            "Analysis complete, transitioning to execution phase",
            DecisionType.TRADE_ENTRY,
            ConfidenceLevel.HIGH
        )
    
    def _on_start_reflection(self, transition):
        """Callback for entering reflection state"""
        self.record_thought(
            "Starting performance reflection",
            "Trade execution complete, analyzing performance",
            DecisionType.PERFORMANCE_REVIEW,
            ConfidenceLevel.MEDIUM
        )
    
    def _on_emergency_state(self, transition):
        """Callback for entering emergency state"""
        self.record_thought(
            "Emergency state activated",
            f"Emergency triggered by: {transition.reason}",
            DecisionType.METACOGNITIVE,
            ConfidenceLevel.LOW
        )
    
    def _start_background_processing(self):
        """Start background processing thread"""
        if self._background_thread and self._background_thread.is_alive():
            return
        
        self._shutdown_event.clear()
        self._background_thread = threading.Thread(
            target=self._background_worker,
            daemon=True
        )
        self._background_thread.start()
        self.logger.info("Background processing started")
    
    def _background_worker(self):
        """Background worker for periodic tasks"""
        last_memory_consolidation = datetime.datetime.utcnow()
        last_thought_archival = datetime.datetime.utcnow()
        last_performance_analysis = datetime.datetime.utcnow()
        
        while not self._shutdown_event.is_set():
            try:
                current_time = datetime.datetime.utcnow()
                
                # Memory consolidation
                if (current_time - last_memory_consolidation).total_seconds() >= self.config.memory_consolidation_interval:
                    self.memory.consolidate_memories()
                    last_memory_consolidation = current_time
                
                # Thought archival
                if (current_time - last_thought_archival).total_seconds() >= self.config.thought_archival_interval:
                    yesterday = datetime.date.today() - datetime.timedelta(days=1)
                    self.thoughts.archive_daily_thoughts(yesterday)
                    last_thought_archival = current_time
                
                # Performance analysis
                if (current_time - last_performance_analysis).total_seconds() >= self.config.performance_analysis_interval:
                    self.metacognition.generate_performance_attribution()
                    last_performance_analysis = current_time
                
                # State machine validation
                self.state_machine._validate_state_integrity()
                
                # Sleep for a minute before next check
                self._shutdown_event.wait(60)
                
            except Exception as e:
                self.logger.error(f"Background processing error: {e}")
                self._shutdown_event.wait(60)  # Wait before retrying
    
    # === PUBLIC API ===
    
    def record_thought(self, decision: str, reasoning: str,
                      decision_type: DecisionType = DecisionType.MARKET_ANALYSIS,
                      confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                      market_context: Dict[str, Any] = None,
                      strategy_id: str = None, trade_id: str = None,
                      tags: List[str] = None) -> str:
        """Record a thought in the cognitive system"""
        try:
            thought_id = self.thoughts.record_thought(
                decision=decision,
                reasoning=reasoning,
                decision_type=decision_type,
                confidence=confidence,
                market_context=market_context,
                strategy_id=strategy_id,
                trade_id=trade_id,
                tags=tags
            )
            
            # Store in working memory if important
            if confidence.value >= 4 or decision_type in [DecisionType.TRADE_ENTRY, DecisionType.TRADE_EXIT]:
                memory_content = f"Decision: {decision} | Reasoning: {reasoning}"
                self.memory.store_memory(
                    content=memory_content,
                    memory_type=MemoryType.WORKING,
                    importance=ImportanceLevel.HIGH if confidence.value >= 4 else ImportanceLevel.MEDIUM,
                    tags=[decision_type.value] + (tags or []),
                    metadata={
                        'thought_id': thought_id,
                        'confidence': confidence.value,
                        'strategy_id': strategy_id,
                        'trade_id': trade_id
                    }
                )
            
            self._cognitive_metrics['thoughts_recorded'] += 1
            
            # Trigger callbacks
            for callback in self._decision_callbacks:
                try:
                    callback(thought_id, decision, reasoning)
                except Exception as e:
                    self.logger.error(f"Decision callback failed: {e}")
            
            return thought_id
            
        except Exception as e:
            self.logger.error(f"Failed to record thought: {e}")
            return ""
    
    def store_memory(self, content: str, importance: ImportanceLevel = ImportanceLevel.MEDIUM,
                    memory_type: MemoryType = MemoryType.WORKING,
                    tags: List[str] = None, metadata: Dict[str, Any] = None) -> str:
        """Store memory in the cognitive system"""
        try:
            memory_id = self.memory.store_memory(
                content=content,
                memory_type=memory_type,
                importance=importance,
                tags=tags,
                metadata=metadata
            )
            
            self._cognitive_metrics['memory_items_stored'] += 1
            return memory_id
            
        except Exception as e:
            self.logger.error(f"Failed to store memory: {e}")
            return ""
    
    def analyze_decision(self, decision_id: str, decision_type: str,
                        initial_confidence: float, actual_outcome: DecisionOutcome,
                        profit_loss: float = None, strategy_used: str = None,
                        market_context: Dict[str, Any] = None,
                        time_to_outcome: float = None) -> str:
        """Analyze a completed decision for learning"""
        try:
            analysis_id = self.metacognition.analyze_decision(
                decision_id=decision_id,
                decision_type=decision_type,
                initial_confidence=initial_confidence,
                actual_outcome=actual_outcome,
                profit_loss=profit_loss,
                strategy_used=strategy_used,
                market_context=market_context,
                time_to_outcome=time_to_outcome
            )
            
            self._cognitive_metrics['decisions_made'] += 1
            
            # Create episodic memory for significant outcomes
            if profit_loss and abs(profit_loss) > 500:  # Significant trade
                self.memory.create_episodic_memory(
                    event_type="significant_trade",
                    details={
                        'decision_id': decision_id,
                        'profit_loss': profit_loss,
                        'outcome': actual_outcome.value,
                        'strategy': strategy_used
                    },
                    importance=ImportanceLevel.HIGH if abs(profit_loss) > 1000 else ImportanceLevel.MEDIUM
                )
            
            return analysis_id
            
        except Exception as e:
            self.logger.error(f"Failed to analyze decision: {e}")
            return ""
    
    def transition_state(self, new_state: CognitiveState, 
                        trigger: StateTransitionTrigger = StateTransitionTrigger.MANUAL_OVERRIDE,
                        reason: str = "", context: Dict[str, Any] = None) -> bool:
        """Transition to a new cognitive state"""
        try:
            success = self.state_machine.transition_to(
                new_state=new_state,
                trigger=trigger,
                reason=reason,
                context=context
            )
            
            if success:
                self._cognitive_metrics['state_transitions'] += 1
                
                # Trigger callbacks
                for callback in self._state_change_callbacks:
                    try:
                        callback(new_state, trigger, reason)
                    except Exception as e:
                        self.logger.error(f"State change callback failed: {e}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to transition state: {e}")
            return False
    
    def search_memories(self, query: str, memory_types: List[MemoryType] = None,
                       tags: List[str] = None, limit: int = 10):
        """Search cognitive memories"""
        return self.memory.search_memories(
            query=query,
            memory_types=memory_types,
            tags=tags,
            limit=limit
        )
    
    def search_thoughts(self, query: str = None, decision_type: DecisionType = None,
                       hours: int = 24, limit: int = 20):
        """Search thought journal"""
        if decision_type:
            return self.thoughts.search_thoughts(
                query=query,
                decision_type=decision_type,
                limit=limit
            )
        else:
            return self.thoughts.get_recent_thoughts(hours=hours, limit=limit)
    
    def get_current_state(self) -> CognitiveState:
        """Get current cognitive state"""
        return self.state_machine.get_current_state()
    
    def get_state_context(self) -> Dict[str, Any]:
        """Get current state context"""
        return self.state_machine.get_state_context()
    
    def update_emotional_state(self, emotional_state: EmotionalState):
        """Update current emotional state"""
        self.thoughts.update_emotional_state(emotional_state)
        
        # Record emotional state change
        self.record_thought(
            f"Emotional state changed to {emotional_state.value}",
            "Emotional state update recorded",
            DecisionType.METACOGNITIVE,
            ConfidenceLevel.HIGH,
            tags=['emotional_state', emotional_state.value]
        )
    
    def get_cognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive cognitive system summary"""
        try:
            return {
                'system_status': {
                    'initialized': self._initialized,
                    'current_state': self.state_machine.get_current_state().value,
                    'state_duration_minutes': self.state_machine.get_state_duration(),
                    'uptime_hours': (datetime.datetime.utcnow() - self._cognitive_metrics['system_uptime']).total_seconds() / 3600
                },
                'memory_summary': self.memory.get_memory_summary(),
                'thought_summary': self.thoughts.generate_thought_summary(),
                'state_analytics': self.state_machine.get_state_analytics(),
                'metacognitive_summary': self.metacognition.get_metacognitive_summary(),
                'cognitive_metrics': self._cognitive_metrics.copy(),
                'health_status': self._perform_health_checks()
            }
        except Exception as e:
            self.logger.error(f"Failed to generate cognitive summary: {e}")
            return {'error': str(e)}
    
    def register_decision_callback(self, callback: Callable):
        """Register callback for decision events"""
        self._decision_callbacks.append(callback)
    
    def register_state_change_callback(self, callback: Callable):
        """Register callback for state change events"""
        self._state_change_callbacks.append(callback)
    
    def shutdown(self):
        """Graceful shutdown of cognitive system"""
        self.logger.info("Shutting down cognitive system...")
        
        # Stop background processing
        if self._background_thread and self._background_thread.is_alive():
            self._shutdown_event.set()
            self._background_thread.join(timeout=30)
        
        # Final memory consolidation
        try:
            self.memory.consolidate_memories()
        except Exception as e:
            self.logger.error(f"Final memory consolidation failed: {e}")
        
        # Create final backup
        try:
            self.gcp_client.create_disaster_recovery_backup()
        except Exception as e:
            self.logger.error(f"Final backup creation failed: {e}")
        
        # Transition to maintenance state
        try:
            self.state_machine.transition_to(
                CognitiveState.MAINTENANCE,
                StateTransitionTrigger.SCHEDULED_MAINTENANCE,
                "System shutdown initiated"
            )
        except Exception as e:
            self.logger.error(f"Failed to transition to maintenance state: {e}")
        
        self._initialized = False
        self.logger.info("Cognitive system shutdown completed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


# Factory function for easy initialization
def create_cognitive_system(project_id: str = None, 
                           enable_background_processing: bool = True,
                           logger: logging.Logger = None) -> CognitiveSystem:
    """Factory function to create configured cognitive system"""
    config = CognitiveConfig(
        project_id=project_id,
        enable_background_processing=enable_background_processing
    )
    
    return CognitiveSystem(config=config, logger=logger)