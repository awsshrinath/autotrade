# runner / metacognition.py
# Metacognition system for self - awareness and performance analysis
# Implements decision tracking, bias detection, and learning progress with Firestore analytics

import uuid
import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import statistics
import logging
from .k8s_native_gcp_client import get_k8s_gcp_client


class BiasType(Enum):
    CONFIRMATION_BIAS = "confirmation_bias"
    OVERCONFIDENCE_BIAS = "overconfidence_bias"
    ANCHORING_BIAS = "anchoring_bias"
    AVAILABILITY_BIAS = "availability_bias"
    LOSS_AVERSION = "loss_aversion"
    RECENCY_BIAS = "recency_bias"
    PATTERN_SEEKING = "pattern_seeking"
    OVERTRADING = "overtrading"


class DecisionOutcome(Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    PENDING = "pending"
    CANCELLED = "cancelled"


class LearningType(Enum):
    STRATEGY_IMPROVEMENT = "strategy_improvement"
    RISK_MANAGEMENT = "risk_management"
    MARKET_ANALYSIS = "market_analysis"
    EMOTIONAL_REGULATION = "emotional_regulation"
    DECISION_MAKING = "decision_making"
    PATTERN_RECOGNITION = "pattern_recognition"


@dataclass
class DecisionAnalysis:
    """Analysis record of a trading decision"""
    id: str
    decision_id: str
    timestamp: datetime.datetime
    decision_type: str
    initial_confidence: float
    actual_outcome: str
    outcome_confidence: float
    profit_loss: Optional[float]
    market_context: Dict[str, Any]
    strategy_used: str
    time_to_outcome: float  # minutes
    accuracy_score: float
    bias_indicators: List[str]
    learning_opportunities: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DecisionAnalysis':
        return cls(**data)


@dataclass
class BiasDetection:
    """Record of detected cognitive bias"""
    id: str
    bias_type: str
    confidence: float
    evidence: List[str]
    impact_assessment: str
    severity: float
    timestamp: datetime.datetime
    related_decisions: List[str]
    suggested_mitigation: List[str]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BiasDetection':
        return cls(**data)


@dataclass
class LearningMetric:
    """Learning progress measurement"""
    id: str
    learning_type: str
    timestamp: datetime.datetime
    skill_level: float  # 0 - 10 scale
    improvement_rate: float
    accuracy_trend: float
    confidence_calibration: float
    key_learnings: List[str]
    areas_for_improvement: List[str]
    evidence: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningMetric':
        return cls(**data)


@dataclass
class PerformanceAttribution:
    """Attribution analysis of performance to specific factors"""
    id: str
    period_start: datetime.datetime
    period_end: datetime.datetime
    total_pnl: float
    strategy_attribution: Dict[str, float]
    market_attribution: Dict[str, float]
    skill_attribution: float
    luck_attribution: float
    bias_impact: float
    decision_quality_score: float
    areas_of_strength: List[str]
    areas_for_improvement: List[str]
    confidence_accuracy: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceAttribution':
        return cls(**data)


class MetaCognition:
    """
    Advanced metacognitive system for self - awareness and continuous improvement.
    Analyzes decision quality, detects biases, and tracks learning progress.
    """
    
    def __init__(self, gcp_client, logger: logging.Logger = None):
        self.gcp_client = gcp_client
        self.logger = logger or logging.getLogger(__name__)
        
        # Decision tracking
        self._decision_history: List[DecisionAnalysis] = []
        self._performance_cache: Dict[str, Any] = {}
        
        # Bias detection thresholds
        self.bias_thresholds = {
                    BiasType.OVERCONFIDENCE_BIAS: 0.7,
                    BiasType.CONFIRMATION_BIAS: 0.6,
                    BiasType.ANCHORING_BIAS: 0.5,
                    BiasType.LOSS_AVERSION: 0.8,
                BiasType.RECENCY_BIAS: 0.6,
            BiasType.OVERTRADING: 0.5
        }
        
        # Learning tracking
        self._learning_baselines: Dict[str, float] = {}
        self._skill_progression: Dict[str, List[float]] = {}
        
        # Performance analysis configuration
        self.analysis_lookback_days = 30
        self.min_decisions_for_analysis = 10
        
        # Load recent data
        self._load_recent_data()
    
    def _load_recent_data(self):
        """Load recent decision data for analysis"""
        try:
            cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=7)
            
            # Load recent decision analyses
            recent_decisions = self.gcp_client.query_memory_collection(
                        'decision_analysis',
                        filters=[('timestamp', '>=', cutoff_time)],
                    order_by='timestamp',
                limit=100
            )
            
            self._decision_history = [
                DecisionAnalysis.from_dict(data) for data in recent_decisions
            ]
            
            self.logger.info(f"Loaded {len(self._decision_history)} recent decision analyses")
        
        except Exception as e:
            self.logger.error(f"Failed to load recent metacognitive data: {e}")
            self._decision_history = []
    
    def analyze_decision(self, decision_id: str, decision_type: str, 
                                initial_confidence: float, actual_outcome: DecisionOutcome,
                                profit_loss: float = None, strategy_used: str = None,
                            market_context: Dict[str, Any] = None, 
                        time_to_outcome: float = None) -> str:
        """Analyze a completed decision for learning and bias detection"""
        
        analysis_id = str(uuid.uuid4())
        now = datetime.datetime.utcnow()
        
        # Calculate outcome confidence based on profit / loss
        outcome_confidence = self._calculate_outcome_confidence(actual_outcome, profit_loss)
        
        # Calculate accuracy score
        accuracy_score = self._calculate_accuracy_score(initial_confidence, actual_outcome)
        
        # Detect potential biases
        bias_indicators = self._detect_decision_biases(
            initial_confidence, actual_outcome, profit_loss, market_context
        )
        
        # Identify learning opportunities
        learning_opportunities = self._identify_learning_opportunities(
            decision_type, initial_confidence, actual_outcome, accuracy_score
        )
        
        decision_analysis = DecisionAnalysis(
                    id=analysis_id,
                    decision_id=decision_id,
                    timestamp=now,
                    decision_type=decision_type,
                    initial_confidence=initial_confidence,
                    actual_outcome=actual_outcome.value,
                    outcome_confidence=outcome_confidence,
                    profit_loss=profit_loss,
                    market_context=market_context or {},
                    strategy_used=strategy_used or "unknown",
                    time_to_outcome=time_to_outcome or 0.0,
                    accuracy_score=accuracy_score,
                    bias_indicators=bias_indicators,
                learning_opportunities=learning_opportunities,
            metadata={}
        )
        
        # Store analysis
        success = self.gcp_client.store_memory_item(
                    'decision_analysis',
                analysis_id,
            decision_analysis.to_dict()
        )
        
        if success:
            self._decision_history.append(decision_analysis)
            
            # Trigger bias analysis if enough decisions
            if len(self._decision_history) >= self.min_decisions_for_analysis:
                self._analyze_systematic_biases()
            
            # Update learning metrics
            self._update_learning_metrics(decision_analysis)
            
            self.logger.debug(f"Decision analysis completed: {analysis_id}")
        
        return analysis_id
    
    def _calculate_outcome_confidence(self, outcome: DecisionOutcome, profit_loss: float = None) -> float:
        """Calculate confidence in outcome assessment"""
        base_confidence = {
                    DecisionOutcome.SUCCESS: 1.0,
                    DecisionOutcome.FAILURE: 1.0,
                    DecisionOutcome.PARTIAL_SUCCESS: 0.7,
                DecisionOutcome.PENDING: 0.3,
            DecisionOutcome.CANCELLED: 0.5
        }.get(outcome, 0.5)
        
        # Adjust based on profit / loss magnitude
        if profit_loss is not None:
            magnitude_factor = min(abs(profit_loss) / 1000.0, 1.0)  # Normalize to 1000 units
            base_confidence = base_confidence * (0.7 + 0.3 * magnitude_factor)
        
        return min(base_confidence, 1.0)
    
    def _calculate_accuracy_score(self, initial_confidence: float, 
                                actual_outcome: DecisionOutcome) -> float:
        """Calculate decision accuracy score"""
        outcome_success = {
                    DecisionOutcome.SUCCESS: 1.0,
                    DecisionOutcome.PARTIAL_SUCCESS: 0.6,
                    DecisionOutcome.FAILURE: 0.0,
                DecisionOutcome.CANCELLED: 0.3,
            DecisionOutcome.PENDING: 0.5
        }.get(actual_outcome, 0.5)
        
        # Perfect calibration would have confidence match outcome
        calibration_error = abs(initial_confidence - outcome_success)
        calibration_score = 1.0 - calibration_error
        
        # Combine outcome success and calibration
        accuracy_score = 0.7 * outcome_success + 0.3 * calibration_score
        
        return max(0.0, min(1.0, accuracy_score))
    
    def _detect_decision_biases(self, initial_confidence: float, actual_outcome: DecisionOutcome,
                              profit_loss: float = None, market_context: Dict[str, Any] = None) -> List[str]:
        """Detect potential biases in individual decision"""
        detected_biases = []
        
        # Overconfidence bias
        if initial_confidence > 0.8 and actual_outcome == DecisionOutcome.FAILURE:
            detected_biases.append(BiasType.OVERCONFIDENCE_BIAS.value)
        
        # Loss aversion (holding losing positions too long)
        if (profit_loss is not None and profit_loss < 0 and 
            market_context and market_context.get('time_in_position', 0) > 60):  # > 1 hour
            detected_biases.append(BiasType.LOSS_AVERSION.value)
        
        # Pattern seeking (high confidence without strong fundamentals)
        if (initial_confidence > 0.7 and 
            market_context and market_context.get('fundamental_score', 0.5) < 0.4):
            detected_biases.append(BiasType.PATTERN_SEEKING.value)
        
        return detected_biases
    
    def _identify_learning_opportunities(self, decision_type: str, initial_confidence: float,
                                       actual_outcome: DecisionOutcome, accuracy_score: float) -> List[str]:
        """Identify learning opportunities from decision"""
        opportunities = []
        
        # Low accuracy suggests learning needed
        if accuracy_score < 0.5:
            opportunities.append(f"Improve {decision_type} decision accuracy")
        
        # Poor calibration
        if abs(initial_confidence - accuracy_score) > 0.3:
            opportunities.append("Improve confidence calibration")
        
        # Failed high - confidence decisions
        if initial_confidence > 0.7 and actual_outcome == DecisionOutcome.FAILURE:
            opportunities.append("Review high - confidence failure patterns")
        
        # Successful low - confidence decisions
        if initial_confidence < 0.4 and actual_outcome == DecisionOutcome.SUCCESS:
            opportunities.append("Understand factors that increase confidence")
        
        return opportunities
    
    def _analyze_systematic_biases(self):
        """Analyze decision history for systematic biases"""
        try:
            recent_decisions = self._decision_history[-50:]  # Last 50 decisions
            
            # Overconfidence analysis
            self._analyze_overconfidence_bias(recent_decisions)
            
            # Confirmation bias analysis
            self._analyze_confirmation_bias(recent_decisions)
            
            # Recency bias analysis
            self._analyze_recency_bias(recent_decisions)
            
            # Overtrading analysis
            self._analyze_overtrading_bias(recent_decisions)
        
        except Exception as e:
            self.logger.error(f"Failed to analyze systematic biases: {e}")
    
    def _analyze_overconfidence_bias(self, decisions: List[DecisionAnalysis]):
        """Analyze for overconfidence bias"""
        high_confidence_decisions = [
            d for d in decisions if d.initial_confidence > 0.8
        ]
        
        if len(high_confidence_decisions) < 5:
            return
        
        success_rate = len([
            d for d in high_confidence_decisions 
            if d.actual_outcome == DecisionOutcome.SUCCESS.value
        ]) / len(high_confidence_decisions)
        
        # Overconfidence if success rate significantly lower than confidence
        expected_success_rate = statistics.mean([d.initial_confidence for d in high_confidence_decisions])
        overconfidence_score = expected_success_rate - success_rate
        
        if overconfidence_score > self.bias_thresholds[BiasType.OVERCONFIDENCE_BIAS]:
            self._record_bias_detection(
                        BiasType.OVERCONFIDENCE_BIAS,
                    overconfidence_score,
                [
                            f"High confidence decisions success rate: {success_rate:.2%}",
                        f"Expected success rate: {expected_success_rate:.2%}",
                    f"Overconfidence gap: {overconfidence_score:.2%}"
                    ],
                [d.id for d in high_confidence_decisions]
            )
    
    def _analyze_confirmation_bias(self, decisions: List[DecisionAnalysis]):
        """Analyze for confirmation bias"""
        # Look for patterns where similar market conditions lead to similar decisions
        # regardless of varying fundamentals
        
        decision_patterns = {}
        for decision in decisions:
            market_sentiment = decision.market_context.get('market_sentiment', 'neutral')
            if market_sentiment not in decision_patterns:
                decision_patterns[market_sentiment] = []
            decision_patterns[market_sentiment].append(decision)
        
        for sentiment, sentiment_decisions in decision_patterns.items():
            if len(sentiment_decisions) < 5:
                continue
            
            # Check if decisions are too similar despite varying conditions
            strategy_diversity = len(set(d.strategy_used for d in sentiment_decisions))
            confidence_variance = statistics.variance([d.initial_confidence for d in sentiment_decisions])
            
            if strategy_diversity <= 2 and confidence_variance < 0.1:  # Low diversity
                confirmation_score = 1.0 - (strategy_diversity / len(sentiment_decisions))
                
                if confirmation_score > self.bias_thresholds[BiasType.CONFIRMATION_BIAS]:
                    self._record_bias_detection(
                                BiasType.CONFIRMATION_BIAS,
                            confirmation_score,
                        [
                                    f"Low strategy diversity in {sentiment} market",
                                f"Strategy count: {strategy_diversity}",
                            f"Confidence variance: {confidence_variance:.3f}"
                            ],
                        [d.id for d in sentiment_decisions]
                    )
    
    def _analyze_recency_bias(self, decisions: List[DecisionAnalysis]):
        """Analyze for recency bias"""
        if len(decisions) < 10:
            return
        
        # Compare influence of recent vs distant decisions on current patterns
        recent_decisions = decisions[-5:]
        older_decisions = decisions[-15:-5]
        
        recent_avg_confidence = statistics.mean([d.initial_confidence for d in recent_decisions])
        older_avg_confidence = statistics.mean([d.initial_confidence for d in older_decisions])
        
        # Check if recent performance overly influences confidence
        recent_success_rate = len([
            d for d in recent_decisions 
            if d.actual_outcome == DecisionOutcome.SUCCESS.value
        ]) / len(recent_decisions)
        
        confidence_bias = abs(recent_avg_confidence - older_avg_confidence)
        
        if confidence_bias > self.bias_thresholds[BiasType.RECENCY_BIAS]:
            self._record_bias_detection(
                        BiasType.RECENCY_BIAS,
                    confidence_bias,
                [
                            f"Recent confidence: {recent_avg_confidence:.2f}",
                        f"Historical confidence: {older_avg_confidence:.2f}",
                    f"Recent success rate: {recent_success_rate:.2%}"
                    ],
                [d.id for d in recent_decisions]
            )
    
    def _analyze_overtrading_bias(self, decisions: List[DecisionAnalysis]):
        """Analyze for overtrading bias"""
        # Check decision frequency and quality correlation
        decision_times = [d.timestamp for d in decisions]
        
        # Calculate decision frequency (decisions per hour)
        if len(decision_times) < 2:
            return
        
        time_span = (decision_times[-1] - decision_times[0]).total_seconds() / 3600  # hours
        decision_frequency = len(decisions) / time_span if time_span > 0 else 0
        
        # Check if high frequency correlates with lower accuracy
        avg_accuracy = statistics.mean([d.accuracy_score for d in decisions])
        
        # Overtrading if high frequency with low accuracy
        if decision_frequency > 2.0 and avg_accuracy < 0.6:  # More than 2 decisions / hour with low accuracy
            overtrading_score = decision_frequency * (1.0 - avg_accuracy)
            
            if overtrading_score > self.bias_thresholds[BiasType.OVERTRADING]:
                self._record_bias_detection(
                            BiasType.OVERTRADING,
                        overtrading_score,
                    [
                                f"Decision frequency: {decision_frequency:.1f} per hour",
                            f"Average accuracy: {avg_accuracy:.2%}",
                        f"Overtrading score: {overtrading_score:.2f}"
                        ],
                    [d.id for d in decisions]
                )
    
    def _record_bias_detection(self, bias_type: BiasType, confidence: float,
                             evidence: List[str], related_decisions: List[str]):
        """Record detected bias in Firestore"""
        bias_id = str(uuid.uuid4())
        
        # Generate mitigation suggestions
        mitigation_suggestions = self._get_bias_mitigation_suggestions(bias_type)
        
        bias_detection = BiasDetection(
                    id=bias_id,
                    bias_type=bias_type.value,
                    confidence=confidence,
                    evidence=evidence,
                impact_assessment=self._assess_bias_impact(bias_type, confidence),
            severity=min(confidence * 2.0, 1.0),  # Scale to 0 - 1
                    timestamp=datetime.datetime.utcnow(),
                    related_decisions=related_decisions,
                suggested_mitigation=mitigation_suggestions,
            metadata={}
        )
        
        success = self.gcp_client.store_memory_item(
                    'bias_tracking',
                bias_id,
            bias_detection.to_dict()
        )
        
        if success:
            self.logger.warning(f"Bias detected: {bias_type.value} (confidence: {confidence:.2f})")
    
    def _get_bias_mitigation_suggestions(self, bias_type: BiasType) -> List[str]:
        """Get mitigation suggestions for specific bias"""
        suggestions = {
            BiasType.OVERCONFIDENCE_BIAS: [
                        "Implement pre - mortem analysis before high - confidence decisions",
                    "Track confidence vs actual outcomes more closely",
                "Seek contrarian viewpoints before major decisions"
                ],
            BiasType.CONFIRMATION_BIAS: [
                        "Actively seek disconfirming evidence",
                    "Use structured decision frameworks",
                "Implement devil's advocate processes"
                ],
            BiasType.RECENCY_BIAS: [
                        "Review longer - term performance patterns",
                    "Weight historical data appropriately",
                "Use systematic decision criteria"
                ],
            BiasType.OVERTRADING: [
                        "Implement cooling - off periods between trades",
                    "Set daily trade limits",
                "Focus on quality over quantity"
                ],
            BiasType.LOSS_AVERSION: [
                        "Set strict stop - loss rules",
                    "Practice position sizing discipline",
                "Review risk - reward ratios regularly"
            ]
        }
        
        return suggestions.get(bias_type, ["Review decision - making process"])
    
    def _assess_bias_impact(self, bias_type: BiasType, confidence: float) -> str:
        """Assess impact of detected bias"""
        if confidence > 0.8:
            return "High impact - immediate attention required"
        elif confidence > 0.6:
            return "Medium impact - monitor and adjust"
        else:
            return "Low impact - track for patterns"
    
    def _update_learning_metrics(self, decision_analysis: DecisionAnalysis):
        """Update learning progress metrics"""
        try:
            # Identify learning type based on decision
            learning_type = self._map_decision_to_learning_type(decision_analysis.decision_type)
            
            # Calculate current skill level
            skill_level = self._calculate_skill_level(learning_type, decision_analysis)
            
            # Update skill progression
            if learning_type not in self._skill_progression:
                self._skill_progression[learning_type] = []
            
            self._skill_progression[learning_type].append(skill_level)
            
            # Calculate improvement rate
            improvement_rate = self._calculate_improvement_rate(learning_type)
            
            # Calculate confidence calibration
            confidence_calibration = self._calculate_confidence_calibration(learning_type)
            
            learning_metric = LearningMetric(
                        id=str(uuid.uuid4()),
                        learning_type=learning_type,
                        timestamp=datetime.datetime.utcnow(),
                        skill_level=skill_level,
                        improvement_rate=improvement_rate,
                        accuracy_trend=decision_analysis.accuracy_score,
                        confidence_calibration=confidence_calibration,
                        key_learnings=decision_analysis.learning_opportunities,
                    areas_for_improvement=self._identify_improvement_areas(learning_type),
                evidence={'recent_decision': decision_analysis.id}
            )
            
            # Store learning metric
            self.gcp_client.store_memory_item(
                        'learning_metrics',
                    learning_metric.id,
                learning_metric.to_dict()
            )
        
        except Exception as e:
            self.logger.error(f"Failed to update learning metrics: {e}")
    
    def _map_decision_to_learning_type(self, decision_type: str) -> str:
        """Map decision type to learning category"""
        mapping = {
                    'trade_entry': LearningType.STRATEGY_IMPROVEMENT.value,
                    'trade_exit': LearningType.STRATEGY_IMPROVEMENT.value,
                    'risk_assessment': LearningType.RISK_MANAGEMENT.value,
                'market_analysis': LearningType.MARKET_ANALYSIS.value,
            'strategy_selection': LearningType.DECISION_MAKING.value
        }
        
        return mapping.get(decision_type, LearningType.DECISION_MAKING.value)
    
    def _calculate_skill_level(self, learning_type: str, decision_analysis: DecisionAnalysis) -> float:
        """Calculate current skill level for learning type"""
        # Base skill on recent accuracy and confidence calibration
        accuracy_component = decision_analysis.accuracy_score * 5.0  # Scale to 0 - 5
        
        # Get recent decisions of same type for trend analysis
        same_type_decisions = [
            d for d in self._decision_history[-20:]
            if self._map_decision_to_learning_type(d.decision_type) == learning_type
        ]
        
        if len(same_type_decisions) >= 3:
            trend_component = statistics.mean([d.accuracy_score for d in same_type_decisions]) * 5.0
            skill_level = 0.7 * accuracy_component + 0.3 * trend_component
        else:
            skill_level = accuracy_component
        
        return min(10.0, max(0.0, skill_level))
    
    def _calculate_improvement_rate(self, learning_type: str) -> float:
        """Calculate improvement rate for learning type"""
        if learning_type not in self._skill_progression:
            return 0.0
        
        progression = self._skill_progression[learning_type]
        if len(progression) < 2:
            return 0.0
        
        # Calculate slope of recent progression
        recent_progression = progression[-10:]  # Last 10 measurements
        if len(recent_progression) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(recent_progression)
        sum_x = sum(range(n))
        sum_y = sum(recent_progression)
        sum_xy = sum(i * y for i, y in enumerate(recent_progression))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        return slope
    
    def _calculate_confidence_calibration(self, learning_type: str) -> float:
        """Calculate confidence calibration for learning type"""
        # Find decisions matching learning type
        matching_decisions = [
            d for d in self._decision_history[-20:]
            if self._map_decision_to_learning_type(d.decision_type) == learning_type
        ]
        
        if len(matching_decisions) < 3:
            return 0.5  # Neutral calibration
        
        # Calculate average calibration error
        calibration_errors = [
            abs(d.initial_confidence - d.accuracy_score) 
            for d in matching_decisions
        ]
        
        avg_error = statistics.mean(calibration_errors)
        calibration_score = 1.0 - avg_error  # Higher score = better calibration
        
        return max(0.0, min(1.0, calibration_score))
    
    def _identify_improvement_areas(self, learning_type: str) -> List[str]:
        """Identify areas for improvement in learning type"""
        areas = []
        
        # Get recent performance for this learning type
        matching_decisions = [
            d for d in self._decision_history[-10:]
            if self._map_decision_to_learning_type(d.decision_type) == learning_type
        ]
        
        if not matching_decisions:
            return ["Need more practice in this area"]
        
        avg_accuracy = statistics.mean([d.accuracy_score for d in matching_decisions])
        avg_confidence = statistics.mean([d.initial_confidence for d in matching_decisions])
        
        if avg_accuracy < 0.6:
            areas.append("Improve decision accuracy")
        
        if abs(avg_confidence - avg_accuracy) > 0.3:
            areas.append("Improve confidence calibration")
        
        # Check for consistent biases
        common_biases = []
        for decision in matching_decisions:
            common_biases.extend(decision.bias_indicators)
        
        if common_biases:
            bias_counts = {}
            for bias in common_biases:
                bias_counts[bias] = bias_counts.get(bias, 0) + 1
            
            frequent_biases = [bias for bias, count in bias_counts.items() if count >= 2]
            for bias in frequent_biases:
                areas.append(f"Address {bias}")
        
        return areas if areas else ["Continue current approach"]
    
    def generate_performance_attribution(self, period_days: int = 7) -> str:
        """Generate comprehensive performance attribution analysis"""
        try:
            cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(days=period_days)
            
            # Get decisions in period
            period_decisions = [
                d for d in self._decision_history
                if d.timestamp >= cutoff_time and d.profit_loss is not None
            ]
            
            if not period_decisions:
                return "insufficient_data"
            
            # Calculate total P&L
            total_pnl = sum(d.profit_loss for d in period_decisions)
            
            # Strategy attribution
            strategy_pnl = {}
            for decision in period_decisions:
                strategy = decision.strategy_used
                if strategy not in strategy_pnl:
                    strategy_pnl[strategy] = 0
                strategy_pnl[strategy] += decision.profit_loss
            
            # Market attribution (simplified)
            market_conditions = {}
            for decision in period_decisions:
                market = decision.market_context.get('market_sentiment', 'neutral')
                if market not in market_conditions:
                    market_conditions[market] = 0
                market_conditions[market] += decision.profit_loss
            
            # Skill vs luck estimation
            accuracy_scores = [d.accuracy_score for d in period_decisions]
            avg_accuracy = statistics.mean(accuracy_scores)
            
            # High accuracy suggests skill, low accuracy suggests luck (or bad luck)
            skill_attribution = min(avg_accuracy * total_pnl, total_pnl)
            luck_attribution = total_pnl - skill_attribution
            
            # Bias impact estimation
            decisions_with_bias = [d for d in period_decisions if d.bias_indicators]
            bias_impact = len(decisions_with_bias) / len(period_decisions) * abs(total_pnl) * -0.1
            
            # Decision quality score
            decision_quality_score = statistics.mean([d.accuracy_score for d in period_decisions])
            
            # Confidence accuracy
            confidence_errors = [
                abs(d.initial_confidence - d.accuracy_score) 
                for d in period_decisions
            ]
            confidence_accuracy = 1.0 - statistics.mean(confidence_errors)
            
            attribution = PerformanceAttribution(
                        id=str(uuid.uuid4()),
                        period_start=cutoff_time,
                        period_end=datetime.datetime.utcnow(),
                        total_pnl=total_pnl,
                        strategy_attribution=strategy_pnl,
                        market_attribution=market_conditions,
                        skill_attribution=skill_attribution,
                        luck_attribution=luck_attribution,
                        bias_impact=bias_impact,
                        decision_quality_score=decision_quality_score,
                        areas_of_strength=self._identify_strengths(period_decisions),
                    areas_for_improvement=self._identify_weaknesses(period_decisions),
                confidence_accuracy=confidence_accuracy
            )
            
            # Store attribution analysis
            attribution_id = attribution.id
            success = self.gcp_client.store_memory_item(
                        'performance_attribution',
                    attribution_id,
                attribution.to_dict()
            )
            
            if success:
                self.logger.info(f"Performance attribution completed: {attribution_id}")
            
            return attribution_id
        
        except Exception as e:
            self.logger.error(f"Failed to generate performance attribution: {e}")
            return "error"
    
    def _identify_strengths(self, decisions: List[DecisionAnalysis]) -> List[str]:
        """Identify performance strengths from decision analysis"""
        strengths = []
        
        # High accuracy decisions
        high_accuracy = [d for d in decisions if d.accuracy_score > 0.8]
        if len(high_accuracy) / len(decisions) > 0.3:
            strengths.append("Consistent high - accuracy decisions")
        
        # Good confidence calibration
        well_calibrated = [
            d for d in decisions 
            if abs(d.initial_confidence - d.accuracy_score) < 0.2
        ]
        if len(well_calibrated) / len(decisions) > 0.7:
            strengths.append("Well - calibrated confidence")
        
        # Profitable strategies
        profitable_decisions = [d for d in decisions if d.profit_loss > 0]
        if len(profitable_decisions) / len(decisions) > 0.6:
            strengths.append("Strong win rate")
        
        return strengths if strengths else ["Areas for improvement identified"]
    
    def _identify_weaknesses(self, decisions: List[DecisionAnalysis]) -> List[str]:
        """Identify performance weaknesses from decision analysis"""
        weaknesses = []
        
        # Low accuracy decisions
        low_accuracy = [d for d in decisions if d.accuracy_score < 0.4]
        if len(low_accuracy) / len(decisions) > 0.3:
            weaknesses.append("Too many low - accuracy decisions")
        
        # Poor confidence calibration
        poorly_calibrated = [
            d for d in decisions 
            if abs(d.initial_confidence - d.accuracy_score) > 0.4
        ]
        if len(poorly_calibrated) / len(decisions) > 0.4:
            weaknesses.append("Poor confidence calibration")
        
        # Frequent biases
        biased_decisions = [d for d in decisions if d.bias_indicators]
        if len(biased_decisions) / len(decisions) > 0.5:
            weaknesses.append("Frequent cognitive biases")
        
        return weaknesses if weaknesses else ["Performance appears solid"]
    
    def get_metacognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive metacognitive system summary"""
        try:
            # Recent decision analysis
            recent_decisions = self._decision_history[-20:] if self._decision_history else []
            
            # Learning progress
            learning_metrics = self.gcp_client.query_memory_collection(
                        'learning_metrics',
                    order_by='timestamp',
                limit=10
            )
            
            # Bias tracking
            recent_biases = self.gcp_client.query_memory_collection(
                        'bias_tracking',
                    filters=[('timestamp', '>=', datetime.datetime.utcnow() - datetime.timedelta(days=7))],
                limit=20
            )
            
            summary = {
                        'total_decisions_analyzed': len(self._decision_history),
                        'recent_decision_count': len(recent_decisions),
                        'average_accuracy': statistics.mean([d.accuracy_score for d in recent_decisions]) if recent_decisions else 0,
                        'recent_biases_detected': len(recent_biases),
                        'learning_areas_tracked': len(set(lm.get('learning_type') for lm in learning_metrics)),
                        'confidence_calibration': self._calculate_overall_calibration(),
                        'improvement_trend': self._calculate_overall_improvement_trend(),
                    'top_bias_types': self._get_top_bias_types(recent_biases),
                'skill_levels': self._get_current_skill_levels()
            }
            
            return summary
        
        except Exception as e:
            self.logger.error(f"Failed to generate metacognitive summary: {e}")
            return {'error': str(e)}
    
    def _calculate_overall_calibration(self) -> float:
        """Calculate overall confidence calibration"""
        if not self._decision_history:
            return 0.5
        
        calibration_errors = [
            abs(d.initial_confidence - d.accuracy_score) 
            for d in self._decision_history[-50:]
        ]
        
        avg_error = statistics.mean(calibration_errors)
        return max(0.0, min(1.0, 1.0 - avg_error))
    
    def _calculate_overall_improvement_trend(self) -> str:
        """Calculate overall improvement trend"""
        if len(self._decision_history) < 10:
            return "insufficient_data"
        
        recent_accuracy = statistics.mean([
            d.accuracy_score for d in self._decision_history[-10:]
        ])
        
        older_accuracy = statistics.mean([
            d.accuracy_score for d in self._decision_history[-20:-10]
        ]) if len(self._decision_history) >= 20 else recent_accuracy
        
        improvement = recent_accuracy - older_accuracy
        
        if improvement > 0.1:
            return "improving"
        elif improvement < -0.1:
            return "declining"
        else:
            return "stable"
    
    def _get_top_bias_types(self, bias_detections: List[Dict]) -> List[str]:
        """Get most common bias types"""
        bias_counts = {}
        for bias in bias_detections:
            bias_type = bias.get('bias_type', 'unknown')
            bias_counts[bias_type] = bias_counts.get(bias_type, 0) + 1
        
        return sorted(bias_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    def _get_current_skill_levels(self) -> Dict[str, float]:
        """Get current skill levels across all learning types"""
        skill_levels = {}
        
        for learning_type, progression in self._skill_progression.items():
            if progression:
                skill_levels[learning_type] = progression[-1]
        
        return skill_levels
