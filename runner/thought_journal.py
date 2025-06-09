# runner / thought_journal.py
# Persistent thought journaling system for cognitive self - awareness
# Captures every decision, reasoning process, and emotional state with Firestore persistence

import uuid
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import logging
from .k8s_native_gcp_client import get_k8s_gcp_client


class EmotionalState(Enum):
    CALM = "calm"
    EXCITED = "excited"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    FRUSTRATED = "frustrated"
    OPTIMISTIC = "optimistic"
    CAUTIOUS = "cautious"


class DecisionType(Enum):
    TRADE_ENTRY = "trade_entry"
    TRADE_EXIT = "trade_exit"
    STRATEGY_SELECTION = "strategy_selection"
    RISK_ASSESSMENT = "risk_assessment"
    MARKET_ANALYSIS = "market_analysis"
    PERFORMANCE_REVIEW = "performance_review"
    LEARNING = "learning"
    METACOGNITIVE = "metacognitive"


class ConfidenceLevel(Enum):
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5


@dataclass
class ThoughtEntry:
    """Individual thought entry with comprehensive metadata"""
    id: str
    timestamp: datetime.datetime
    decision: str
    reasoning: str
    confidence: float
    emotional_state: str
    market_context: Dict[str, Any]
    strategy_id: Optional[str]
    trade_id: Optional[str]
    decision_type: str
    importance_score: float
    follow_up_required: bool
    tags: List[str]
    related_thoughts: List[str]
    outcome: Optional[str]
    reflection: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Firestore storage"""
        return {
                    'id': self.id,
                    'timestamp': self.timestamp,
                    'decision': self.decision,
                    'reasoning': self.reasoning,
                    'confidence': self.confidence,
                    'emotional_state': self.emotional_state,
                    'market_context': self.market_context,
                    'strategy_id': self.strategy_id,
                    'trade_id': self.trade_id,
                    'decision_type': self.decision_type,
                    'importance_score': self.importance_score,
                    'follow_up_required': self.follow_up_required,
                    'tags': self.tags,
                    'related_thoughts': self.related_thoughts,
                'outcome': self.outcome,
            'reflection': self.reflection
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThoughtEntry':
        """Create ThoughtEntry from dictionary"""
        return cls(
                    id=data['id'],
                    timestamp=data['timestamp'],
                    decision=data['decision'],
                    reasoning=data['reasoning'],
                    confidence=data['confidence'],
                    emotional_state=data['emotional_state'],
                    market_context=data.get('market_context', {}),
                    strategy_id=data.get('strategy_id'),
                    trade_id=data.get('trade_id'),
                    decision_type=data['decision_type'],
                    importance_score=data.get('importance_score', 1.0),
                    follow_up_required=data.get('follow_up_required', False),
                    tags=data.get('tags', []),
                    related_thoughts=data.get('related_thoughts', []),
                outcome=data.get('outcome'),
            reflection=data.get('reflection')
        )


@dataclass
class ThoughtPattern:
    """Identified pattern in thinking processes"""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    confidence_impact: float
    success_rate: float
    examples: List[str]
    suggested_improvements: List[str]


class ThoughtJournal:
    """
    Persistent thought journaling system for cognitive self - awareness.
    Captures every decision, reasoning process, and learning moment.
    """
    
    def __init__(self, gcp_client, logger: logging.Logger = None):
        self.gcp_client = gcp_client
        self.logger = logger or logging.getLogger(__name__)
        
        # Current emotional and cognitive state
        self.current_emotional_state = EmotionalState.CALM
        self.current_confidence_baseline = 3.0
        
        # Thought analysis cache
        self._recent_thoughts_cache: List[ThoughtEntry] = []
        self._thought_patterns: Dict[str, ThoughtPattern] = {}
        
        # Configuration
        self.max_cache_size = 50
        self.pattern_analysis_threshold = 10  # Min thoughts to identify patterns
        
        # Load recent thoughts on startup
        self._load_recent_thoughts()
    
    def _load_recent_thoughts(self):
        """Load recent thoughts from Firestore on startup"""
        try:
            # Load thoughts from last 24 hours
            recent_cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
            
            recent_thoughts = self.gcp_client.query_memory_collection(
                        'thought_journal',
                        filters=[('timestamp', '>=', recent_cutoff)],
                    order_by='timestamp',
                limit=self.max_cache_size
            )
            
            self._recent_thoughts_cache = [
                ThoughtEntry.from_dict(thought) for thought in recent_thoughts
            ]
            
            self.logger.info(f"Loaded {len(self._recent_thoughts_cache)} recent thoughts")
        except Exception as e:
            self.logger.error(f"Failed to load recent thoughts: {e}")
            self._recent_thoughts_cache = []
    
    def record_thought(self, decision: str, reasoning: str, 
                              decision_type: DecisionType = DecisionType.MARKET_ANALYSIS,
                              confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM,
                              market_context: Dict[str, Any] = None,
                          strategy_id: str = None, trade_id: str = None,
                      tags: List[str] = None) -> str:
        """Record a new thought with comprehensive metadata"""
        
        thought_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        
        # Calculate importance score based on decision type and confidence
        importance_score = self._calculate_importance_score(decision_type, confidence)
        
        # Determine if follow - up is required
        follow_up_required = self._requires_follow_up(decision_type, confidence)
        
        thought_entry = ThoughtEntry(
                    id=thought_id,
                    timestamp=now,
                    decision=decision,
                    reasoning=reasoning,
                    confidence=confidence.value,
                    emotional_state=self.current_emotional_state.value,
                    market_context=market_context or {},
                    strategy_id=strategy_id,
                    trade_id=trade_id,
                    decision_type=decision_type.value,
                    importance_score=importance_score,
                    follow_up_required=follow_up_required,
                    tags=tags or [],
                    related_thoughts=self._find_related_thoughts(decision, reasoning),
                outcome=None,
            reflection=None
        )
        
        # Store to Firestore
        success = self.gcp_client.store_memory_item(
                    'thought_journal',
                thought_id,
            thought_entry.to_dict()
        )
        
        if success:
            # Add to cache
            self._recent_thoughts_cache.append(thought_entry)
            self._maintain_cache_size()
            
            # Trigger pattern analysis if enough thoughts
            if len(self._recent_thoughts_cache) >= self.pattern_analysis_threshold:
                self._analyze_thought_patterns()
            
            self.logger.debug(f"Recorded thought: {decision_type.value} - {decision[:50]}...")
        else:
            self.logger.error(f"Failed to record thought: {thought_id}")
        
        return thought_id
    
    def update_thought_outcome(self, thought_id: str, outcome: str, reflection: str = None):
        """Update thought with actual outcome and reflection"""
        try:
            updates = {
                        'outcome': outcome,
                    'reflection': reflection,
                'outcome_timestamp': datetime.datetime.utcnow()
            }
            
            success = self.gcp_client.update_memory_item(
                        'thought_journal',
                    thought_id,
                updates
            )
            
            # Update cache if present
            for thought in self._recent_thoughts_cache:
                if thought.id == thought_id:
                    thought.outcome = outcome
                    thought.reflection = reflection
                    break
            
            if success:
                self.logger.debug(f"Updated thought outcome: {thought_id}")
            
            return success
        except Exception as e:
            self.logger.error(f"Failed to update thought outcome: {e}")
            return False
    
    def _calculate_importance_score(self, decision_type: DecisionType, 
                                  confidence: ConfidenceLevel) -> float:
        """Calculate importance score for thought prioritization"""
        type_weights = {
                    DecisionType.TRADE_ENTRY: 4.0,
                    DecisionType.TRADE_EXIT: 4.0,
                    DecisionType.STRATEGY_SELECTION: 3.5,
                    DecisionType.RISK_ASSESSMENT: 3.0,
                    DecisionType.MARKET_ANALYSIS: 2.0,
                    DecisionType.PERFORMANCE_REVIEW: 3.5,
                DecisionType.LEARNING: 2.5,
            DecisionType.METACOGNITIVE: 2.0
        }
        
        base_score = type_weights.get(decision_type, 1.0)
        confidence_multiplier = confidence.value / 5.0  # Normalize to 0 - 1
        
        return base_score * (0.5 + confidence_multiplier)
    
    def _requires_follow_up(self, decision_type: DecisionType, 
                          confidence: ConfidenceLevel) -> bool:
        """Determine if thought requires follow - up tracking"""
        high_priority_types = [
                    DecisionType.TRADE_ENTRY,
                DecisionType.STRATEGY_SELECTION,
            DecisionType.RISK_ASSESSMENT
        ]
        
        return (decision_type in high_priority_types or 
                confidence in [ConfidenceLevel.VERY_LOW, ConfidenceLevel.LOW])
    
    def _find_related_thoughts(self, decision: str, reasoning: str) -> List[str]:
        """Find related thoughts based on content similarity"""
        related_ids = []
        decision_words = set(decision.lower().split())
        reasoning_words = set(reasoning.lower().split())
        search_words = decision_words.union(reasoning_words)
        
        for thought in self._recent_thoughts_cache[-20:]:  # Check recent thoughts
            thought_words = set(thought.decision.lower().split())
            thought_words.update(thought.reasoning.lower().split())
            
            # Simple word overlap similarity
            overlap = len(search_words.intersection(thought_words))
            if overlap >= 3:  # Minimum word overlap threshold
                related_ids.append(thought.id)
        
        return related_ids[:5]  # Limit to 5 related thoughts
    
    def _maintain_cache_size(self):
        """Maintain cache size by removing oldest thoughts"""
        while len(self._recent_thoughts_cache) > self.max_cache_size:
            self._recent_thoughts_cache.pop(0)
    
    def _analyze_thought_patterns(self):
        """Analyze recent thoughts for patterns and biases"""
        try:
            # Analyze decision types frequency
            decision_type_counts = {}
            confidence_trends = []
            
            for thought in self._recent_thoughts_cache[-20:]:
                # Count decision types
                dt = thought.decision_type
                decision_type_counts[dt] = decision_type_counts.get(dt, 0) + 1
                
                # Track confidence trends
                confidence_trends.append(thought.confidence)
            
            # Identify patterns
            self._identify_confidence_patterns(confidence_trends)
            self._identify_decision_biases(decision_type_counts)
            
        except Exception as e:
            self.logger.error(f"Failed to analyze thought patterns: {e}")
    
    def _identify_confidence_patterns(self, confidence_trends: List[float]):
        """Identify patterns in confidence levels"""
        if len(confidence_trends) < 5:
            return
        
        # Calculate moving average
        window_size = 5
        moving_avg = []
        for i in range(len(confidence_trends) - window_size + 1):
            avg = sum(confidence_trends[i:i + window_size]) / window_size
            moving_avg.append(avg)
        
        # Detect trends
        if len(moving_avg) >= 2:
            trend = moving_avg[-1] - moving_avg[0]
            
            if trend < -0.5:
                pattern = ThoughtPattern(
                            pattern_id="decreasing_confidence",
                            pattern_type="confidence_trend",
                            description="Confidence levels are decreasing over recent decisions",
                            frequency=1,
                        confidence_impact=trend,
                    success_rate=0.0,  # To be calculated with outcomes
                        examples=[],
                    suggested_improvements=["Review recent successful decisions", "Practice confidence - building exercises"]
                )
                self._thought_patterns["decreasing_confidence"] = pattern
                
            elif trend > 0.5:
                pattern = ThoughtPattern(
                            pattern_id="increasing_confidence",
                            pattern_type="confidence_trend", 
                            description="Confidence levels are increasing over recent decisions",
                            frequency=1,
                            confidence_impact=trend,
                            success_rate=0.0,
                        examples=[],
                    suggested_improvements=["Monitor for overconfidence", "Maintain risk awareness"]
                )
                self._thought_patterns["increasing_confidence"] = pattern
    
    def _identify_decision_biases(self, decision_type_counts: Dict[str, int]):
        """Identify potential decision - making biases"""
        total_decisions = sum(decision_type_counts.values())
        
        for decision_type, count in decision_type_counts.items():
            frequency = count / total_decisions
            
            # Flag if over - reliance on certain decision types
            if frequency > 0.6:  # More than 60% of decisions
                pattern = ThoughtPattern(
                            pattern_id=f"bias_{decision_type}",
                            pattern_type="decision_bias",
                            description=f"Over - reliance on {decision_type} decisions ({frequency:.1%})",
                            frequency=count,
                            confidence_impact=0.0,
                            success_rate=0.0,
                        examples=[],
                    suggested_improvements=[
                                f"Diversify decision types beyond {decision_type}",
                            "Consider alternative approaches",
                        "Review decision - making framework"
                    ]
                )
                self._thought_patterns[f"bias_{decision_type}"] = pattern
    
    def get_recent_thoughts(self, hours: int = 24, limit: int = 50) -> List[ThoughtEntry]:
        """Get recent thoughts within specified time window"""
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=hours)
        
        # First check cache
        recent_from_cache = [
            thought for thought in self._recent_thoughts_cache
            if thought.timestamp >= cutoff_time
        ]
        
        if len(recent_from_cache) >= limit:
            return recent_from_cache[-limit:]
        
        # Query Firestore for more thoughts if needed
        try:
            thoughts_data = self.gcp_client.query_memory_collection(
                        'thought_journal',
                        filters=[('timestamp', '>=', cutoff_time)],
                    order_by='timestamp',
                limit=limit
            )
            
            return [ThoughtEntry.from_dict(data) for data in thoughts_data]
        except Exception as e:
            self.logger.error(f"Failed to get recent thoughts: {e}")
            return recent_from_cache
    
    def search_thoughts(self, query: str = None, decision_type: DecisionType = None,
                               emotional_state: EmotionalState = None, confidence_range: Tuple[int, int] = None,
                           date_range: Tuple[datetime.datetime, datetime.datetime] = None,
                       limit: int = 20) -> List[ThoughtEntry]:
        """Advanced thought search with multiple filters"""
        try:
            filters = []
            
            # Add filters based on parameters
            if decision_type:
                filters.append(('decision_type', '==', decision_type.value))
            
            if emotional_state:
                filters.append(('emotional_state', '==', emotional_state.value))
            
            if confidence_range:
                filters.append(('confidence', '>=', confidence_range[0]))
                filters.append(('confidence', '<=', confidence_range[1]))
            
            if date_range:
                filters.append(('timestamp', '>=', date_range[0]))
                filters.append(('timestamp', '<=', date_range[1]))
            
            thoughts_data = self.gcp_client.query_memory_collection(
                        'thought_journal',
                        filters=filters,
                    order_by='timestamp',
                limit=limit
            )
            
            thoughts = [ThoughtEntry.from_dict(data) for data in thoughts_data]
            
            # Apply text search if query provided
            if query:
                query_lower = query.lower()
                thoughts = [
                    thought for thought in thoughts
                    if (query_lower in thought.decision.lower() or
                        query_lower in thought.reasoning.lower())
                ]
            
            return thoughts
        
        except Exception as e:
            self.logger.error(f"Failed to search thoughts: {e}")
            return []
    
    def get_thoughts_requiring_followup(self) -> List[ThoughtEntry]:
        """Get thoughts that require follow - up tracking"""
        try:
            thoughts_data = self.gcp_client.query_memory_collection(
                        'thought_journal',
                        filters=[('follow_up_required', '==', True), ('outcome', '==', None)],
                    order_by='timestamp',
                limit=50
            )
            
            return [ThoughtEntry.from_dict(data) for data in thoughts_data]
        
        except Exception as e:
            self.logger.error(f"Failed to get follow - up thoughts: {e}")
            return []
    
    def generate_thought_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive summary of recent thinking patterns"""
        recent_thoughts = self.get_recent_thoughts(hours=hours)
        
        if not recent_thoughts:
            return {
                        'period_hours': hours,
                    'total_thoughts': 0,
                'summary': 'No thoughts recorded in this period'
            }
        
        # Analyze recent thoughts
        decision_types = [thought.decision_type for thought in recent_thoughts]
        emotional_states = [thought.emotional_state for thought in recent_thoughts]
        confidence_levels = [thought.confidence for thought in recent_thoughts]
        
        summary = {
                    'period_hours': hours,
                    'total_thoughts': len(recent_thoughts),
                    'decision_type_distribution': self._count_distribution(decision_types),
                    'emotional_state_distribution': self._count_distribution(emotional_states),
                    'average_confidence': sum(confidence_levels) / len(confidence_levels),
                    'confidence_trend': self._calculate_trend(confidence_levels),
                    'high_importance_thoughts': len([t for t in recent_thoughts if t.importance_score > 3.0]),
                    'thoughts_requiring_followup': len([t for t in recent_thoughts if t.follow_up_required]),
                'identified_patterns': list(self._thought_patterns.keys()),
            'most_recent_thought': recent_thoughts[-1].decision if recent_thoughts else None
        }
        
        return summary
    
    def _count_distribution(self, items: List[str]) -> Dict[str, int]:
        """Count distribution of items"""
        distribution = {}
        for item in items:
            distribution[item] = distribution.get(item, 0) + 1
        return distribution
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for numeric values"""
        if len(values) < 2:
            return "insufficient_data"
        
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        diff = second_avg - first_avg
        
        if diff > 0.3:
            return "increasing"
        elif diff < -0.3:
            return "decreasing"
        else:
            return "stable"
    
    def archive_daily_thoughts(self, date: datetime.date = None) -> bool:
        """Archive thoughts for a specific day to Cloud Storage"""
        if date is None:
            date = datetime.date.today() - datetime.timedelta(days=1)  # Previous day
        
        try:
            # Get all thoughts for the day
            start_time = datetime.datetime.combine(date, datetime.time.min)
            end_time = datetime.datetime.combine(date, datetime.time.max)
            
            daily_thoughts = self.search_thoughts(
                    date_range=(start_time, end_time),
                limit=1000
            )
            
            if daily_thoughts:
                # Convert to serializable format
                thoughts_data = [thought.to_dict() for thought in daily_thoughts]
                
                # Store in Cloud Storage
                date_str = date.strftime("%Y-%m-%d")
                success = self.gcp_client.store_thought_archive(thoughts_data, date_str)
                
                if success:
                    self.logger.info(f"Archived {len(daily_thoughts)} thoughts for {date_str}")
                
                return success
            
            return True  # No thoughts to archive is success
        
        except Exception as e:
            self.logger.error(f"Failed to archive daily thoughts: {e}")
            return False
    
    def update_emotional_state(self, new_state: EmotionalState):
        """Update current emotional state"""
        self.current_emotional_state = new_state
        self.logger.debug(f"Emotional state updated to: {new_state.value}")
    
    def get_thought_patterns(self) -> Dict[str, ThoughtPattern]:
        """Get identified thought patterns"""
        return self._thought_patterns.copy()
    
    def clear_thought_cache(self):
        """Clear in - memory thought cache"""
        self._recent_thoughts_cache.clear()
        self._thought_patterns.clear()
        self.logger.info("Thought cache cleared")
