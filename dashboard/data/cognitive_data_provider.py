#!/usr/bin/env python3
"""
Cognitive Data Provider

Provides cognitive insights data for the dashboard.
Supports three modes:
1. Full mode: GCP cognitive system + AI processing
2. Hybrid mode: OpenAI processing only (no GCP storage)
3. Unavailable mode: Clear unavailable status (NO MOCK DATA)
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configuration
OFFLINE_MODE = os.getenv('OFFLINE_MODE', 'false').lower() == 'true'

# Check cognitive system availability
try:
    from runner.production_manager import ProductionManager
    from runner.cognitive_state_types import DecisionType
    COGNITIVE_AVAILABLE = True
except ImportError:
    COGNITIVE_AVAILABLE = False
    DecisionType = None

# Import OpenAI for direct AI processing
try:
    from openai import OpenAI
    OPENAI_PACKAGE_AVAILABLE = True
    
    # Multi-source API key detection with GCP Secret Manager priority
    def get_openai_api_key():
        """Get OpenAI API key from multiple sources in priority order"""
        
        # 1. GCP Secret Manager (highest priority for production)
        try:
            from runner.k8s_native_gcp_client import get_k8s_gcp_client
            client = get_k8s_gcp_client()
            if client and hasattr(client, 'get_secret'):
                secret_value = client.get_secret('OPENAI_API_KEY')
                if secret_value and secret_value.strip():
                    return secret_value.strip(), "GCP Secret Manager"
        except Exception as e:
            logging.getLogger(__name__).debug(f"GCP Secret Manager API key retrieval failed: {e}")
        
        # 2. Environment variables (development fallback)
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key and api_key.strip():
            return api_key.strip(), "Environment Variable"
        
        # 3. Streamlit secrets (final fallback - only when running in Streamlit)
        try:
            import streamlit as st
            if hasattr(st, 'secrets') and 'OPENAI_API_KEY' in st.secrets:
                api_key = st.secrets['OPENAI_API_KEY']
                if api_key and api_key.strip():
                    return api_key.strip(), "Streamlit Secrets"
        except (ImportError, AttributeError, Exception):
            pass  # Silent fallback - streamlit may not be available
        
        return None, "Not Found"
    
    OPENAI_API_KEY, API_KEY_SOURCE = get_openai_api_key()
    OPENAI_AVAILABLE = bool(OPENAI_API_KEY)
    
    # Initialize OpenAI client if API key is available
    if OPENAI_AVAILABLE:
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    else:
        openai_client = None
        
except ImportError:
    OPENAI_PACKAGE_AVAILABLE = False
    OPENAI_AVAILABLE = False
    OPENAI_API_KEY = None
    openai_client = None
    API_KEY_SOURCE = "OpenAI package not installed"


class CognitiveDataProvider:
    """Data provider for cognitive insights with hybrid online/offline mode support"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.offline_mode = OFFLINE_MODE
        
        # Defer initialization of production_manager
        self._production_manager = None
        self._cognitive_system = None
        
        # Determine mode based on available capabilities
        self.mode = self._determine_mode()
    
    @property
    def production_manager(self):
        """Lazy-loaded production manager"""
        if self._production_manager is None and not self.offline_mode and COGNITIVE_AVAILABLE:
            try:
                from runner.production_manager import ProductionManager
                self._production_manager = ProductionManager()
            except Exception as e:
                self.logger.warning(f"Failed to initialize ProductionManager on demand: {e}")
                self._production_manager = None  # Explicitly set to None on failure
        return self._production_manager
    
    @property
    def cognitive_system(self):
        """Lazy-loaded cognitive system"""
        if self._cognitive_system is None and self.production_manager:
            self._cognitive_system = self.production_manager.cognitive_system
        return self._cognitive_system

    def _determine_mode(self):
        """Determine operating mode based on available components"""
        # Try to initialize cognitive system with GCP (full mode)
        if not self.offline_mode and COGNITIVE_AVAILABLE:
            # Check availability without full initialization
            try:
                from runner.production_manager import ProductionManager # Quick check
                # A more lightweight check should be implemented in ProductionManager
                # For now, we assume if the import works, we can attempt full mode.
                self.logger.info("✅ Full Cognitive Mode available (GCP + AI)")
                return "full"
            except Exception:
                pass # Fallback to hybrid

        # Fall back to hybrid mode if OpenAI is available
        if OPENAI_AVAILABLE and openai_client and not self.offline_mode:
            self.logger.info(f"🧠 Hybrid Mode: Using OpenAI for AI processing (API key from {API_KEY_SOURCE})")
            return "hybrid"
        
        self.logger.info(f"❌ Cognitive Services Unavailable: OpenAI API key {API_KEY_SOURCE}")
        return "unavailable"
    
    def _query_openai(self, prompt: str, system_prompt: str = None) -> str:
        """Query OpenAI directly for AI insights"""
        if not OPENAI_AVAILABLE or not openai_client:
            return "AI processing unavailable - OpenAI API key not configured"
            
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            self.logger.warning(f"OpenAI query failed: {e}")
            return f"AI processing error: {str(e)}"
    
    def get_cognitive_summary(self) -> Dict[str, Any]:
        """Get comprehensive cognitive system summary"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                return self.cognitive_system.get_cognitive_summary()
            elif self.mode == "hybrid":
                return self._get_hybrid_cognitive_summary()
            else:
                return self._get_unavailable_cognitive_summary()
        except Exception as e:
            self.logger.warning(f"Error getting cognitive summary: {e}")
            return self._get_unavailable_cognitive_summary()
    
    def _get_hybrid_cognitive_summary(self) -> Dict[str, Any]:
        """Get cognitive summary using hybrid mode (OpenAI without GCP)"""
        try:
            # Query OpenAI for current market analysis
            system_prompt = "You are an AI trading assistant. Provide a brief analysis of current market conditions and trading system status."
            market_analysis = self._query_openai(
                "Analyze the current market conditions for Indian stock markets (NIFTY). Consider recent trends, volatility, and overall sentiment.",
                system_prompt
            )
            
            return {
                'system_status': {
                    'initialized': True,
                    'current_state': 'hybrid',
                    'last_update': datetime.now().isoformat(),
                    'mode': 'hybrid',
                    'ai_available': True,
                    'storage_available': False,
                    'uptime_hours': 'N/A'  # Not tracked in hybrid mode
                },
                'thought_summary': {
                    'total_thoughts': 'N/A',  # No GCP storage
                    'recent_thoughts': 'N/A',
                    'ai_analysis': market_analysis
                },
                'memory_summary': {
                    'total_memories': 'N/A',  # No GCP storage
                    'working_memory_count': 'N/A',
                    'recent_consolidations': 'N/A'
                },
                'cognitive_metrics': {
                    'decisions_made': 'N/A',  # No GCP storage
                    'thoughts_recorded': 'N/A',
                    'state_transitions': 'N/A'
                },
                'state_analytics': {
                    'status': 'AI processing available via OpenAI'
                }
            }
        except Exception as e:
            self.logger.warning(f"Hybrid mode failed: {e}")
            return self._get_unavailable_cognitive_summary()
    
    def _get_unavailable_cognitive_summary(self) -> Dict[str, Any]:
        """Get summary when cognitive services are unavailable"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return {
            'system_status': {
                'initialized': False,
                'current_state': 'unavailable',
                'last_update': datetime.now().isoformat(),
                'mode': 'unavailable',
                'ai_available': False,
                'storage_available': False,
                'unavailable_reason': reason
            },
            'thought_summary': {
                'status': 'Service unavailable',
                'reason': reason
            },
            'memory_summary': {
                'status': 'Service unavailable', 
                'reason': reason
            },
            'cognitive_metrics': {
                'status': 'Service unavailable',
                'reason': reason
            },
            'state_analytics': {
                'status': 'Service unavailable',
                'reason': reason
            }
        }

    def get_market_sentiment(self) -> Dict[str, Any]:
        """Get AI-powered market sentiment analysis"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                # Get recent market analysis thoughts
                recent_thoughts = self.cognitive_system.get_recent_thoughts(
                    hours=24, 
                    decision_types=[DecisionType.MARKET_ANALYSIS]
                )
                
                # Get memories related to market sentiment
                sentiment_memories = self.cognitive_system.search_memories(
                    query="market sentiment analysis", 
                    limit=5
                )
                
                # Analyze sentiment from thoughts and memories
                sentiment_data = self._analyze_sentiment_from_thoughts(recent_thoughts)
                
                return {
                    **sentiment_data,
                    'data_source': 'GCP cognitive system',
                    'thoughts_analyzed': len(recent_thoughts),
                    'memories_analyzed': len(sentiment_memories)
                }
            elif self.mode == "hybrid":
                return self._get_hybrid_market_sentiment()
            else:
                return self._get_unavailable_market_sentiment()
        except Exception as e:
            self.logger.warning(f"Error getting market sentiment: {e}")
            return self._get_unavailable_market_sentiment()

    def _get_hybrid_market_sentiment(self) -> Dict[str, Any]:
        """Get market sentiment using OpenAI analysis"""
        try:
            system_prompt = "You are a financial market analyst. Analyze current market sentiment and provide a structured assessment."
            
            sentiment_analysis = self._query_openai(
                "Analyze the current sentiment of Indian stock markets (NIFTY 50). Consider market volatility, trading volumes, and overall investor sentiment. Provide a sentiment classification (bullish/bearish/neutral) and confidence level.",
                system_prompt
            )
            
            return {
                'overall_sentiment': 'ai_analyzed',
                'confidence': 'ai_generated',
                'analysis': sentiment_analysis,
                'data_source': f'OpenAI via {API_KEY_SOURCE}',
                'last_analysis': datetime.now().isoformat(),
                'trend': 'ai_analyzed'
            }
        except Exception as e:
            self.logger.warning(f"Hybrid market sentiment failed: {e}")
            return self._get_unavailable_market_sentiment()

    def _get_unavailable_market_sentiment(self) -> Dict[str, Any]:
        """Return unavailable status for market sentiment"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return {
            'status': 'Service unavailable',
            'reason': reason,
            'last_attempt': datetime.now().isoformat()
        }

    def get_trade_insights(self) -> List[Dict[str, Any]]:
        """Get AI-powered trade insights"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                recent_thoughts = self.cognitive_system.get_recent_thoughts(
                    hours=24, 
                    decision_types=[DecisionType.TRADE_ENTRY, DecisionType.TRADE_EXIT, DecisionType.RISK_MANAGEMENT]
                )
                
                insights = []
                for thought in recent_thoughts:
                    insight = self._generate_trade_insight(thought)
                    if insight:
                        insights.append(insight)
                
                # Add pattern analysis
                pattern_insights = self._analyze_trade_patterns(recent_thoughts)
                insights.extend(pattern_insights)
                
                return insights[:10]  # Limit to top 10 insights
            elif self.mode == "hybrid":
                return self._get_hybrid_trade_insights()
            else:
                return self._get_unavailable_trade_insights()
        except Exception as e:
            self.logger.warning(f"Error getting trade insights: {e}")
            return self._get_unavailable_trade_insights()

    def _get_hybrid_trade_insights(self) -> List[Dict[str, Any]]:
        """Get trade insights using OpenAI analysis"""
        try:
            system_prompt = "You are a professional trading analyst. Provide actionable trading insights based on current market conditions."
            
            insights_text = self._query_openai(
                "Provide 3 key trading insights for Indian stock markets today. Focus on actionable recommendations for retail traders.",
                system_prompt
            )
            
            return [
                {
                    'type': 'ai_insight',
                    'message': insights_text,
                    'confidence': 'ai_generated',
                    'action': 'Review AI analysis',
                    'timestamp': datetime.now().isoformat(),
                    'source': f'OpenAI via {API_KEY_SOURCE}'
                }
            ]
        except Exception as e:
            self.logger.warning(f"Hybrid trade insights failed: {e}")
            return self._get_unavailable_trade_insights()

    def _get_unavailable_trade_insights(self) -> List[Dict[str, Any]]:
        """Return unavailable status for trade insights"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return [
            {
                'type': 'service_status',
                'message': f'Trade insights unavailable: {reason}',
                'timestamp': datetime.now().isoformat(),
                'action': 'Configure cognitive services to enable AI insights'
            }
        ]

    def get_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """Get AI-powered strategy recommendations"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                recent_thoughts = self.cognitive_system.get_recent_thoughts(
                    hours=48, 
                    decision_types=[DecisionType.STRATEGY_OPTIMIZATION, DecisionType.PORTFOLIO_REBALANCING]
                )
                
                recommendations = []
                for thought in recent_thoughts:
                    rec = self._generate_strategy_recommendation(thought)
                    if rec:
                        recommendations.append(rec)
                
                return recommendations[:5]  # Limit to top 5 recommendations
            elif self.mode == "hybrid":
                return self._get_hybrid_strategy_recommendations()
            else:
                return self._get_unavailable_strategy_recommendations()
        except Exception as e:
            self.logger.warning(f"Error getting strategy recommendations: {e}")
            return self._get_unavailable_strategy_recommendations()

    def _get_hybrid_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """Get strategy recommendations using OpenAI analysis"""
        try:
            system_prompt = "You are a quantitative trading strategist. Provide strategic recommendations for algorithmic trading."
            
            strategy_text = self._query_openai(
                "Suggest 2 key trading strategy adjustments for current Indian market conditions. Focus on risk management and position sizing.",
                system_prompt
            )
            
            return [
                {
                    'strategy': 'ai_generated',
                    'recommendation': strategy_text,
                    'reason': 'AI analysis of current market conditions',
                    'confidence': 'ai_generated',
                    'priority': 'medium',
                    'source': f'OpenAI via {API_KEY_SOURCE}'
                }
            ]
        except Exception as e:
            self.logger.warning(f"Hybrid strategy recommendations failed: {e}")
            return self._get_unavailable_strategy_recommendations()

    def _get_unavailable_strategy_recommendations(self) -> List[Dict[str, Any]]:
        """Return unavailable status for strategy recommendations"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return [
            {
                'strategy': 'service_status',
                'recommendation': f'Strategy recommendations unavailable: {reason}',
                'reason': 'Cognitive services not configured',
                'priority': 'high',
                'action': 'Configure cognitive services to enable AI recommendations'
            }
        ]

    def get_risk_predictions(self) -> List[Dict[str, Any]]:
        """Get AI-powered risk predictions"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                recent_thoughts = self.cognitive_system.get_recent_thoughts(
                    hours=24, 
                    decision_types=[DecisionType.RISK_MANAGEMENT, DecisionType.MARKET_ANALYSIS]
                )
                
                predictions = self._analyze_risk_patterns(recent_thoughts)
                
                # Add state-based risk assessments
                cognitive_summary = self.cognitive_system.get_cognitive_summary()
                state_risks = self._assess_state_based_risks(cognitive_summary)
                predictions.extend(state_risks)
                
                return predictions[:5]  # Limit to top 5 predictions
            elif self.mode == "hybrid":
                return self._get_hybrid_risk_predictions()
            else:
                return self._get_unavailable_risk_predictions()
        except Exception as e:
            self.logger.warning(f"Error getting risk predictions: {e}")
            return self._get_unavailable_risk_predictions()

    def _get_hybrid_risk_predictions(self) -> List[Dict[str, Any]]:
        """Get risk predictions using OpenAI analysis"""
        try:
            system_prompt = "You are a risk management specialist. Analyze potential market risks and provide structured risk assessments."
            
            risk_analysis = self._query_openai(
                "Identify 2 key risk factors for Indian stock markets in the next 24-48 hours. Consider market volatility, economic indicators, and global factors.",
                system_prompt
            )
            
            return [
                {
                    'type': 'ai_risk_analysis',
                    'prediction': risk_analysis,
                    'confidence': 'ai_generated',
                    'impact': 'medium',
                    'timeframe': '24-48h',
                    'mitigation': 'Review AI analysis and adjust position sizing accordingly',
                    'source': f'OpenAI via {API_KEY_SOURCE}'
                }
            ]
        except Exception as e:
            self.logger.warning(f"Hybrid risk predictions failed: {e}")
            return self._get_unavailable_risk_predictions()

    def _get_unavailable_risk_predictions(self) -> List[Dict[str, Any]]:
        """Return unavailable status for risk predictions"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return [
            {
                'type': 'service_status',
                'prediction': f'Risk predictions unavailable: {reason}',
                'impact': 'medium',
                'timeframe': 'current',
                'mitigation': 'Configure cognitive services to enable AI-powered risk analysis'
            }
        ]

    def get_performance_insights(self) -> Dict[str, Any]:
        """Get AI-powered performance insights"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                metacognitive_summary = self.cognitive_system.get_metacognitive_summary()
                performance_recommendations = self._generate_performance_recommendations(metacognitive_summary)
                
                return {
                    'decision_accuracy': metacognitive_summary.get('decision_accuracy', 0.0),
                    'confidence_calibration': metacognitive_summary.get('confidence_calibration', 0.0),
                    'learning_rate': metacognitive_summary.get('learning_rate', 0.0),
                    'bias_detection': metacognitive_summary.get('identified_biases', []),
                    'improvement_areas': performance_recommendations,
                    'memory_efficiency': metacognitive_summary.get('memory_efficiency', 0.0),
                    'thought_quality': self._assess_thought_quality(),
                    'adaptation_score': metacognitive_summary.get('adaptation_score', 0.0),
                    'data_source': 'GCP cognitive system'
                }
            elif self.mode == "hybrid":
                return self._get_hybrid_performance_insights()
            else:
                return self._get_unavailable_performance_insights()
        except Exception as e:
            self.logger.warning(f"Error getting performance insights: {e}")
            return self._get_unavailable_performance_insights()

    def _get_hybrid_performance_insights(self) -> Dict[str, Any]:
        """Get performance insights using OpenAI analysis"""
        try:
            system_prompt = "You are a performance analyst for algorithmic trading systems. Provide insights on system optimization."
            
            performance_analysis = self._query_openai(
                "Analyze key performance optimization areas for algorithmic trading systems. Focus on decision making, risk management, and adaptation.",
                system_prompt
            )
            
            return {
                'analysis': performance_analysis,
                'data_source': f'OpenAI via {API_KEY_SOURCE}',
                'last_analysis': datetime.now().isoformat(),
                'improvement_areas': ['Review AI analysis for optimization recommendations']
            }
        except Exception as e:
            self.logger.warning(f"Hybrid performance insights failed: {e}")
            return self._get_unavailable_performance_insights()

    def _get_unavailable_performance_insights(self) -> Dict[str, Any]:
        """Return unavailable status for performance insights"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return {
            'status': 'Service unavailable',
            'reason': reason,
            'improvement_areas': ['Configure cognitive services to enable performance analysis'],
            'last_attempt': datetime.now().isoformat()
        }

    def get_cognitive_health(self) -> Dict[str, Any]:
        """Get cognitive system health status"""
        try:
            if self.mode == "full" and self.cognitive_system and hasattr(self.cognitive_system, 'available') and self.cognitive_system.available:
                health_data = self.cognitive_system.get_health_status()
                return {
                    **health_data,
                    'mode': 'full',
                    'data_source': 'GCP cognitive system'
                }
            elif self.mode == "hybrid":
                return self._get_hybrid_cognitive_health()
            else:
                return self._get_unavailable_cognitive_health()
        except Exception as e:
            self.logger.warning(f"Error getting cognitive health: {e}")
            return self._get_unavailable_cognitive_health()

    def _get_hybrid_cognitive_health(self) -> Dict[str, Any]:
        """Get cognitive health in hybrid mode"""
        return {
            'system_status': {
                'initialized': True,
                'current_state': 'hybrid'
            },
            'mode': 'hybrid',
            'ai_processing': {
                'available': True,
                'provider': 'OpenAI',
                'api_key_source': API_KEY_SOURCE
            },
            'storage': {
                'available': False,
                'reason': 'Using hybrid mode without GCP storage'
            },
            'health_checks': {
                'cognitive_available': False,
                'ai_processing': True,
                'overall_status': 'partial'
            },
            'data_source': f'OpenAI via {API_KEY_SOURCE}'
        }

    def _get_unavailable_cognitive_health(self) -> Dict[str, Any]:
        """Return unavailable status for cognitive health"""
        reason = f"OpenAI API key {API_KEY_SOURCE}" if not OPENAI_AVAILABLE else "Cognitive system offline"
        
        return {
            'system_status': {
                'initialized': False,
                'current_state': 'unavailable',
                'reason': reason
            },
            'mode': 'unavailable',
            'health_checks': {
                'cognitive_available': False,
                'ai_processing': False,
                'overall_status': 'unavailable'
            },
            'last_attempt': datetime.now().isoformat()
        }

    # Helper methods for analysis (only used in full mode)
    def _analyze_sentiment_from_thoughts(self, thoughts: List[Dict]) -> Dict[str, Any]:
        """Analyze market sentiment from cognitive thoughts"""
        if not thoughts:
            return {
                'overall_sentiment': 'neutral',
                'confidence': 0.5,
                'factors': ['No recent thoughts available'],
                'trend': 'stable'
            }
        
        # Simplified sentiment analysis based on decision types and confidence
        positive_indicators = 0
        negative_indicators = 0
        
        for thought in thoughts:
            decision_type = thought.get('decision_type', '')
            confidence = thought.get('confidence', 'medium')
            decision = thought.get('decision', '').lower()
            
            # Analyze decision content for sentiment
            if any(word in decision for word in ['buy', 'bullish', 'opportunity', 'growth']):
                positive_indicators += 1
            elif any(word in decision for word in ['sell', 'bearish', 'risk', 'decline']):
                negative_indicators += 1
            
            # Weight by confidence
            if confidence == 'high':
                if 'buy' in decision or 'bullish' in decision:
                    positive_indicators += 0.5
                elif 'sell' in decision or 'bearish' in decision:
                    negative_indicators += 0.5
        
        total_indicators = positive_indicators + negative_indicators
        if total_indicators == 0:
            sentiment = 'neutral'
            confidence = 0.5
        else:
            sentiment_score = positive_indicators / total_indicators
            if sentiment_score > 0.6:
                sentiment = 'bullish'
                confidence = min(0.9, sentiment_score)
            elif sentiment_score < 0.4:
                sentiment = 'bearish'
                confidence = min(0.9, 1 - sentiment_score)
            else:
                sentiment = 'neutral'
                confidence = 0.5
        
        return {
            'overall_sentiment': sentiment,
            'confidence': confidence,
            'factors': [f'Analyzed {len(thoughts)} cognitive decisions'],
            'recent_thoughts_count': len(thoughts),
            'last_analysis': datetime.now().isoformat(),
            'trend': 'dynamic' if total_indicators > 3 else 'stable'
        }

    def _generate_trade_insight(self, thought: Dict) -> Optional[Dict[str, Any]]:
        """Generate trade insight from cognitive thought (full mode only)"""
        try:
            decision = thought.get('decision', '')
            reasoning = thought.get('reasoning', '')
            confidence = thought.get('confidence', 'medium')
            timestamp = thought.get('timestamp', datetime.now())
            
            if not decision or not reasoning:
                return None
            
            # Assess insight quality
            reasoning_quality = self._assess_reasoning_quality(reasoning)
            if reasoning_quality < 0.3:  # Filter low-quality insights
                return None
            
            # Classify insight type
            insight_type = self._classify_insight_type(decision, thought.get('decision_type', ''))
            
            # Generate action recommendation
            action = self._generate_action_recommendation(decision, confidence, {})
            
            return {
                'type': insight_type,
                'message': f"{decision} - {reasoning[:200]}{'...' if len(reasoning) > 200 else ''}",
                'confidence': confidence,
                'quality_score': reasoning_quality,
                'action': action,
                'timestamp': timestamp.isoformat() if hasattr(timestamp, 'isoformat') else str(timestamp),
                'patterns': self._extract_decision_patterns(decision, reasoning)
            }
        except Exception as e:
            self.logger.warning(f"Failed to generate trade insight: {e}")
            return None

    def _analyze_trade_patterns(self, thoughts: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze patterns in trading thoughts (full mode only)"""
        patterns = []
        
        if len(thoughts) < 3:  # Need minimum thoughts for pattern analysis
            return patterns
        
        try:
            # Pattern 1: Frequency of decision types
            decision_types = {}
            for thought in thoughts:
                dt = thought.get('decision_type', 'unknown')
                decision_types[dt] = decision_types.get(dt, 0) + 1
            
            most_common = max(decision_types, key=decision_types.get)
            if decision_types[most_common] >= 3:
                patterns.append({
                    'type': 'frequency_pattern',
                    'message': f'High frequency of {most_common} decisions ({decision_types[most_common]} times)',
                    'confidence': 'medium',
                    'action': f'Review {most_common} strategy effectiveness',
                    'timestamp': datetime.now().isoformat()
                })
            
            # Pattern 2: Confidence trends
            high_confidence_count = sum(1 for t in thoughts if t.get('confidence') == 'high')
            if high_confidence_count / len(thoughts) > 0.7:
                patterns.append({
                    'type': 'confidence_pattern',
                    'message': f'High confidence in recent decisions ({high_confidence_count}/{len(thoughts)})',
                    'confidence': 'high',
                    'action': 'Monitor for overconfidence bias',
                    'timestamp': datetime.now().isoformat()
                })
            
        except Exception as e:
            self.logger.warning(f"Pattern analysis failed: {e}")
        
        return patterns

    def _assess_reasoning_quality(self, reasoning: str) -> float:
        """Assess the quality of reasoning text (full mode only)"""
        if not reasoning:
            return 0.0
        
        quality_score = 0.0
        
        # Length indicates depth of reasoning
        if len(reasoning) > 50:
            quality_score += 0.3
        if len(reasoning) > 150:
            quality_score += 0.2
        
        # Presence of analytical keywords
        analytical_keywords = ['because', 'analysis', 'trend', 'indicator', 'data', 'pattern', 'risk', 'probability']
        keyword_count = sum(1 for keyword in analytical_keywords if keyword in reasoning.lower())
        quality_score += min(0.3, keyword_count * 0.1)
        
        # Structured reasoning indicators
        structure_indicators = ['first', 'second', 'therefore', 'however', 'additionally', 'furthermore']
        structure_count = sum(1 for indicator in structure_indicators if indicator in reasoning.lower())
        quality_score += min(0.2, structure_count * 0.1)
        
        return min(1.0, quality_score)

    def _classify_insight_type(self, decision: str, decision_type: str) -> str:
        """Classify the type of insight (full mode only)"""
        decision_lower = decision.lower()
        
        if 'buy' in decision_lower or 'long' in decision_lower:
            return 'entry_signal'
        elif 'sell' in decision_lower or 'short' in decision_lower:
            return 'exit_signal'
        elif 'risk' in decision_lower or 'stop' in decision_lower:
            return 'risk_management'
        elif 'strategy' in decision_lower or 'optimize' in decision_lower:
            return 'strategy_optimization'
        else:
            return 'market_analysis'

    def _generate_action_recommendation(self, decision: str, confidence: str, market_context: Dict) -> str:
        """Generate action recommendation based on decision (full mode only)"""
        base_actions = {
            'high': 'Consider implementing',
            'medium': 'Monitor and validate',
            'low': 'Further analysis needed for'
        }
        
        base_action = base_actions.get(confidence, 'Review')
        return f"{base_action} this decision"

    def _extract_decision_patterns(self, decision: str, reasoning: str) -> List[str]:
        """Extract patterns from decision and reasoning (full mode only)"""
        patterns = []
        combined_text = f"{decision} {reasoning}".lower()
        
        # Market condition patterns
        if any(word in combined_text for word in ['volatile', 'volatility', 'unstable']):
            patterns.append('high_volatility_context')
        
        if any(word in combined_text for word in ['trend', 'trending', 'momentum']):
            patterns.append('trend_following')
        
        if any(word in combined_text for word in ['support', 'resistance', 'level']):
            patterns.append('technical_analysis')
        
        return patterns

    def _generate_performance_recommendations(self, metacognitive_summary: Dict) -> List[str]:
        """Generate performance recommendations (full mode only)"""
        recommendations = []
        
        try:
            decision_accuracy = metacognitive_summary.get('decision_accuracy', 0.5)
            confidence_calibration = metacognitive_summary.get('confidence_calibration', 0.5)
            learning_rate = metacognitive_summary.get('learning_rate', 0.5)
            
            if decision_accuracy < 0.6:
                recommendations.append("Improve decision-making models and validation processes")
            
            if confidence_calibration < 0.6:
                recommendations.append("Recalibrate confidence scoring mechanisms")
            
            if learning_rate < 0.4:
                recommendations.append("Enhance learning algorithms and feedback loops")
            
            # Add bias-specific recommendations
            biases = metacognitive_summary.get('identified_biases', [])
            for bias in biases:
                recommendations.append(f"Address {bias} bias in decision-making process")
            
        except Exception as e:
            self.logger.warning(f"Failed to generate performance recommendations: {e}")
            recommendations.append("Enable comprehensive cognitive monitoring for detailed recommendations")
        
        return recommendations if recommendations else ["System performing within normal parameters"]

    def _analyze_risk_patterns(self, risk_thoughts: List[Dict]) -> List[Dict[str, Any]]:
        """Analyze risk patterns from thoughts (full mode only)"""
        predictions = []
        
        if not risk_thoughts:
            return predictions
        
        try:
            # Pattern analysis for risk predictions
            risk_decisions = [t.get('decision', '') for t in risk_thoughts]
            
            # Pattern 1: Repeated risk concerns
            risk_keywords = ['volatile', 'risk', 'uncertainty', 'loss', 'drawdown']
            risk_mentions = sum(1 for decision in risk_decisions 
                              for keyword in risk_keywords 
                              if keyword in decision.lower())
            
            if risk_mentions >= len(risk_decisions) * 0.5:  # 50% of decisions mention risk
                predictions.append({
                    'type': 'increased_risk_awareness',
                    'prediction': f'Elevated risk awareness in {risk_mentions} recent decisions',
                    'confidence': 0.8,
                    'impact': 'medium',
                    'timeframe': '24h',
                    'mitigation': 'Review position sizing and implement stricter risk controls'
                })
            
        except Exception as e:
            self.logger.warning(f"Risk pattern analysis failed: {e}")
        
        return predictions

    def _assess_state_based_risks(self, cognitive_summary: Dict) -> List[Dict[str, Any]]:
        """Assess risks based on cognitive state (full mode only)"""
        predictions = []
        
        try:
            system_status = cognitive_summary.get('system_status', {})
            current_state = system_status.get('current_state', 'unknown')
            
            if current_state == 'emergency':
                predictions.append({
                    'type': 'system_risk',
                    'prediction': 'Cognitive system in emergency state',
                    'confidence': 0.9,
                    'impact': 'high',
                    'timeframe': 'immediate',
                    'mitigation': 'Review system health and resolve issues'
                })
        except Exception as e:
            self.logger.warning(f"State-based risk assessment failed: {e}")
        
        return predictions

    def _assess_thought_quality(self) -> float:
        """Assess the quality of recent thoughts (full mode only)"""
        try:
            if self.cognitive_system and self.cognitive_system.available:
                recent_thoughts = self.cognitive_system.get_recent_thoughts(hours=24)
                
                if not recent_thoughts:
                    return 0.5
                
                # Simple quality assessment based on reasoning length and confidence
                quality_scores = []
                for thought in recent_thoughts:
                    reasoning_length = len(thought.get('reasoning', ''))
                    confidence = thought.get('confidence', 'medium')
                    
                    # Score based on reasoning depth and confidence
                    score = min(1.0, reasoning_length / 100)  # Longer reasoning = higher quality
                    if confidence == 'high':
                        score += 0.2
                    elif confidence == 'low':
                        score -= 0.1
                    
                    quality_scores.append(max(0.0, min(1.0, score)))
                
                return sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
            else:
                return 0.5
        except Exception:
            return 0.5

    def _generate_strategy_recommendation(self, thought: Dict) -> Optional[Dict[str, Any]]:
        """Generate strategy recommendation from thought (full mode only)"""
        try:
            decision = thought.get('decision', '')
            reasoning = thought.get('reasoning', '')
            confidence = thought.get('confidence', 'medium')
            
            if not decision or not reasoning:
                return None
            
            return {
                'strategy': 'cognitive_derived',
                'recommendation': decision,
                'reason': reasoning[:150] + '...' if len(reasoning) > 150 else reasoning,
                'confidence': confidence,
                'priority': 'high' if confidence == 'high' else 'medium',
                'timestamp': thought.get('timestamp', datetime.now()).isoformat()
            }
        except Exception as e:
            self.logger.warning(f"Failed to generate strategy recommendation: {e}")
            return None