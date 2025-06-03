import logging
import datetime
from typing import Optional, Dict, Any
from enum import Enum

# Safe imports with fallbacks
try:
    from runner.cognitive_system import CognitiveSystem, DecisionType, ConfidenceLevel, CognitiveState, StateTransitionTrigger
    COGNITIVE_AVAILABLE = True
except ImportError:
    COGNITIVE_AVAILABLE = False
    
    # Fallback enums
    class DecisionType(Enum):
        MARKET_ANALYSIS = "market_analysis"
        STRATEGY_SELECTION = "strategy_selection"
        METACOGNITIVE = "metacognitive"
        PERFORMANCE_REVIEW = "performance_review"
    
    class ConfidenceLevel(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"
    
    class CognitiveState(Enum):
        OBSERVING = "observing"
        REFLECTING = "reflecting"
    
    class StateTransitionTrigger(Enum):
        MARKET_OPEN = "market_open"
        MARKET_CLOSE = "market_close"


class LoggerAdapter:
    """Adapter to handle different logger interfaces"""
    
    def __init__(self, logger):
        self.logger = logger
        
    def error(self, message):
        if hasattr(self.logger, 'error'):
            self.logger.error(message)
        elif hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"❌ [ERROR] {message}")
        else:
            print(f"ERROR: {message}")
    
    def warning(self, message):
        if hasattr(self.logger, 'warning'):
            self.logger.warning(message)
        elif hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"⚠️ [WARNING] {message}")
        else:
            print(f"WARNING: {message}")
    
    def info(self, message):
        if hasattr(self.logger, 'info'):
            self.logger.info(message)
        elif hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"ℹ️ [INFO] {message}")
        else:
            print(f"INFO: {message}")
    
    def debug(self, message):
        if hasattr(self.logger, 'debug'):
            self.logger.debug(message)
        elif hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"🔍 [DEBUG] {message}")
        else:
            print(f"DEBUG: {message}")
    
    def critical(self, message):
        if hasattr(self.logger, 'critical'):
            self.logger.critical(message)
        elif hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"🚨 [CRITICAL] {message}")
        else:
            print(f"CRITICAL: {message}")
    
    def log_event(self, message):
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(message)
        elif hasattr(self.logger, 'info'):
            self.logger.info(message)
        else:
            print(message)


class EnhancedCognitiveSystem:
    """Enhanced cognitive system with robust error handling and fallbacks"""
    
    def __init__(self, logger=None, enhanced_logger=None):
        self.logger = LoggerAdapter(logger or logging.getLogger(__name__))
        self.enhanced_logger = enhanced_logger
        self.cognitive_system = None
        self.available = False
        
        # Try to initialize the real cognitive system
        self._initialize_cognitive_system()
    
    def _initialize_cognitive_system(self):
        """Initialize cognitive system with error handling"""
        
        if not COGNITIVE_AVAILABLE:
            self.logger.warning("Cognitive system modules not available - using fallback mode")
            return
            
        try:
            # Try to create the real cognitive system
            # CognitiveSystem only accepts 'config' and 'logger' parameters
            self.cognitive_system = CognitiveSystem(
                logger=self.logger  # Remove the enhanced_logger parameter that doesn't exist
            )
            self.available = True
            self.logger.info("Cognitive system initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize cognitive system: {e}")
            self.cognitive_system = None
            self.available = False
    
    def record_thought(self, decision: str, reasoning: str, decision_type: DecisionType, 
                      confidence: ConfidenceLevel, market_context: Dict[str, Any] = None, 
                      tags: list = None):
        """Record a cognitive thought with fallback logging"""
        
        if self.available and self.cognitive_system:
            try:
                self.cognitive_system.record_thought(
                    decision=decision,
                    reasoning=reasoning,
                    decision_type=decision_type,
                    confidence=confidence,
                    market_context=market_context or {},
                    tags=tags or []
                )
                return
                
            except Exception as e:
                self.logger.error(f"Failed to record cognitive thought: {e}")
        
        # Fallback: Log as regular event
        thought_summary = {
            "decision": decision,
            "reasoning": reasoning,
            "decision_type": decision_type.value if hasattr(decision_type, 'value') else str(decision_type),
            "confidence": confidence.value if hasattr(confidence, 'value') else str(confidence),
            "market_context": market_context or {},
            "tags": tags or [],
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.logger.log_event(f"🧠 [COGNITIVE] {thought_summary}")
    
    def transition_state(self, new_state: CognitiveState, trigger: StateTransitionTrigger, reason: str):
        """Transition cognitive state with fallback logging"""
        
        if self.available and self.cognitive_system:
            try:
                self.cognitive_system.transition_state(new_state, trigger, reason)
                return
                
            except Exception as e:
                self.logger.error(f"Failed to transition cognitive state: {e}")
        
        # Fallback: Log as regular event
        transition_info = {
            "new_state": new_state.value if hasattr(new_state, 'value') else str(new_state),
            "trigger": trigger.value if hasattr(trigger, 'value') else str(trigger),
            "reason": reason,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        self.logger.log_event(f"🔄 [COGNITIVE STATE] {transition_info}")
    
    def get_cognitive_summary(self) -> Dict[str, Any]:
        """Get cognitive summary with fallback"""
        
        if self.available and self.cognitive_system:
            try:
                return self.cognitive_system.get_cognitive_summary()
            except Exception as e:
                self.logger.error(f"Failed to get cognitive summary: {e}")
        
        # Fallback summary
        return {
            "status": "fallback_mode",
            "available": self.available,
            "timestamp": datetime.datetime.now().isoformat(),
            "summary": "Cognitive system operating in fallback mode"
        }
    
    def shutdown(self):
        """Shutdown cognitive system gracefully"""
        
        if self.available and self.cognitive_system:
            try:
                self.cognitive_system.shutdown()
                self.logger.info("Cognitive system shutdown completed")
            except Exception as e:
                self.logger.error(f"Error during cognitive system shutdown: {e}")
        else:
            self.logger.info("Cognitive system shutdown (fallback mode)")
    
    @property
    def metacognition(self):
        """Access metacognition component with fallback"""
        
        if self.available and self.cognitive_system and hasattr(self.cognitive_system, 'metacognition'):
            return self.cognitive_system.metacognition
        
        # Return fallback metacognition object
        return FallbackMetacognition(self.logger)


class FallbackMetacognition:
    """Fallback metacognition for when the real system is unavailable"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def generate_performance_attribution(self, period_days: int = 1) -> str:
        """Generate fallback performance attribution"""
        
        analysis_id = f"fallback_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.logger.log_event(
            f"📊 [METACOGNITION FALLBACK] Performance analysis generated: {analysis_id} "
            f"(Period: {period_days} days)"
        )
        
        return analysis_id


def initialize_enhanced_cognitive_system(logger, enhanced_logger=None) -> Optional[EnhancedCognitiveSystem]:
    """Initialize enhanced cognitive system with error handling"""
    
    try:
        cognitive_system = EnhancedCognitiveSystem(logger=logger, enhanced_logger=enhanced_logger)
        
        if cognitive_system.available:
            logger_adapter = LoggerAdapter(logger)
            logger_adapter.info("Enhanced cognitive system initialized successfully")
        else:
            logger_adapter = LoggerAdapter(logger)
            logger_adapter.warning("Enhanced cognitive system running in fallback mode")
        
        return cognitive_system
        
    except Exception as e:
        logger_adapter = LoggerAdapter(logger)
        logger_adapter.error(f"Failed to initialize enhanced cognitive system: {e}")
        return None 