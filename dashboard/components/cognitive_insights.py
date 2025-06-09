"""
Cognitive Insights Page Component
AI-powered trading insights and analysis
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dashboard.data.cognitive_data_provider import CognitiveDataProvider


class CognitiveInsightsPage:
    """Cognitive insights page component"""
    
    def __init__(self, cognitive_data_provider):
        self.cognitive_data = cognitive_data_provider
    
    def render(self):
        """Render the cognitive insights page"""
        st.title("🧠 Cognitive Insights")
        st.markdown("*AI-powered trading analysis and decision support*")
        
        # Get cognitive system status first
        cognitive_summary = self.cognitive_data.get_cognitive_summary()
        system_available = cognitive_summary.get('system_status', {}).get('initialized', False)
        
        # Show appropriate status message based on mode
        if hasattr(self.cognitive_data, 'mode'):
            if self.cognitive_data.mode == "hybrid":
                st.success("✨ Cognitive system is currently in hybrid mode. AI insights available!")
            elif self.cognitive_data.mode == "full":
                st.success("🚀 Cognitive system is fully operational with GCP storage.")
            elif not system_available:
                from dashboard.data.cognitive_data_provider import OPENAI_AVAILABLE
                if OPENAI_AVAILABLE:
                    st.warning("⚠️ Cognitive system is currently offline but OpenAI is available. Showing AI-enhanced insights.")
                else:
                    st.warning("⚠️ Cognitive system is currently offline. Showing limited insights.")
        elif not system_available:
            st.warning("⚠️ Cognitive system is currently offline. Showing limited insights.")
        
        # Main layout with tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Overview",
            "💭 Market Sentiment", 
            "🎯 Trade Insights",
            "🛡️ Risk Analysis",
            "📈 Performance",
            "⚙️ System Health"
        ])
        
        with tab1:
            self._render_overview_tab(cognitive_summary)
        
        with tab2:
            self._render_sentiment_tab()
        
        with tab3:
            self._render_insights_tab()
        
        with tab4:
            self._render_risk_tab()
        
        with tab5:
            self._render_performance_tab()
        
        with tab6:
            self._render_health_tab(cognitive_summary)
    
    def _render_overview_tab(self, cognitive_summary: Dict[str, Any]):
        """Render the cognitive overview tab"""
        st.subheader("🎯 Cognitive System Overview")
        
        # System metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            system_status = cognitive_summary.get('system_status', {})
            current_state = system_status.get('current_state', 'offline')
            uptime_hours = system_status.get('uptime_hours', 0)
            
            st.metric(
                label="System State",
                value=current_state.title(),
                delta=f"{uptime_hours:.1f}h uptime"
            )
        
        with col2:
            cognitive_metrics = cognitive_summary.get('cognitive_metrics', {})
            decisions_made = cognitive_metrics.get('decisions_made', 0)
            thoughts_recorded = cognitive_metrics.get('thoughts_recorded', 0)
            
            st.metric(
                label="Decisions Made",
                value=decisions_made,
                delta=f"{thoughts_recorded} thoughts"
            )
        
        with col3:
            memory_summary = cognitive_summary.get('memory_summary', {})
            working_memory = memory_summary.get('working_memory_count', 0)
            total_memories = memory_summary.get('total_memories', 0)
            
            st.metric(
                label="Working Memory",
                value=f"{working_memory} items",
                delta=f"{total_memories} total"
            )
        
        with col4:
            thought_summary = cognitive_summary.get('thought_summary', {})
            recent_thoughts = thought_summary.get('recent_thoughts', 0)
            
            st.metric(
                label="Recent Thoughts",
                value=recent_thoughts,
                delta="24h period"
            )
        
        # Cognitive state timeline
        st.subheader("🔄 Cognitive State Analytics")
        
        state_analytics = cognitive_summary.get('state_analytics', {})
        if state_analytics:
            # Create a simple state transition chart
            states = list(state_analytics.keys())
            durations = list(state_analytics.values())
            
            if states and durations:
                fig = px.pie(
                    values=durations,
                    names=states,
                    title="Time Distribution Across Cognitive States (24h)"
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("State analytics not available - cognitive system may be offline")
        
        # Recent activity summary
        st.subheader("📋 Recent Activity Summary")
        
        if system_status.get('initialized', False):
            st.success("✅ Cognitive system is operational and learning from trading activity")
            
            activity_data = [
                {"Component": "Memory System", "Status": "Active", "Items": working_memory},
                {"Component": "Thought Journal", "Status": "Recording", "Items": recent_thoughts},
                {"Component": "Decision Analysis", "Status": "Learning", "Items": decisions_made},
                {"Component": "Pattern Recognition", "Status": "Analyzing", "Items": "Ongoing"}
            ]
            
            df = pd.DataFrame(activity_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            # Check cognitive data provider mode for better status display
            if hasattr(self.cognitive_data, 'mode'):
                if self.cognitive_data.mode == "hybrid":
                    st.success("🧠 **Cognitive System in Hybrid Mode**")
                    st.info("✨ **Status**: Using OpenAI for real AI analysis without GCP storage. Full AI insights available!")
                elif self.cognitive_data.mode == "full":
                    st.success("✅ **Cognitive System Fully Online**") 
                    st.info("🚀 **Status**: Full cognitive system with GCP storage and AI processing active.")
                else:
                    st.warning("⚠️ **Cognitive System in Offline Mode**")
                    from dashboard.data.cognitive_data_provider import OPENAI_AVAILABLE
                    if OPENAI_AVAILABLE:
                        st.info("📝 **Status**: OpenAI available but system initializing. Please wait or check logs.")
                    else:
                        st.info("📝 **Status**: Using mock data. OpenAI API key required for hybrid mode.")
            else:
                st.warning("⚠️ **Cognitive System Status Unknown**")
                st.info("📝 **Status**: Unable to determine system state.")
    
    def _render_sentiment_tab(self):
        """Render the market sentiment analysis tab"""
        st.subheader("💭 AI-Powered Market Sentiment Analysis")
        
        sentiment_data = self.cognitive_data.get_market_sentiment()
        
        # Main sentiment display
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            sentiment = sentiment_data.get('overall_sentiment', 'neutral')
            confidence = sentiment_data.get('confidence', 0.5)
            
            # Sentiment indicator with color coding
            sentiment_color = {
                'bullish': '🟢',
                'bearish': '🔴',
                'neutral': '🟡'
            }.get(sentiment, '⚪')
            
            st.markdown(f"""
            <div style="text-align: center; padding: 2rem; border: 2px solid #e0e0e0; border-radius: 10px;">
                <h2>{sentiment_color} Market Sentiment: {sentiment.title()}</h2>
                <h3>Confidence: {confidence:.1%}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.metric(
                label="Analysis Period",
                value="24 hours",
                delta=f"{sentiment_data.get('recent_thoughts_count', 0)} thoughts"
            )
        
        with col3:
            trend = sentiment_data.get('trend', 'stable')
            trend_icon = '📈' if trend == 'improving' else '📉' if trend == 'declining' else '➡️'
            
            st.metric(
                label="Trend",
                value=f"{trend_icon} {trend.title()}",
                delta=sentiment_data.get('last_analysis', '')[-8:]  # Time only
            )
        
        # Sentiment factors
        st.subheader("🔍 Key Factors Influencing Sentiment")
        
        factors = sentiment_data.get('factors', [])
        if factors:
            for i, factor in enumerate(factors[:5], 1):
                st.write(f"{i}. {factor}")
        else:
            st.info("No specific sentiment factors identified in recent analysis")
        
        # Confidence meter
        st.subheader("📊 Confidence Distribution")
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=confidence * 100,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Sentiment Confidence %"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "gray"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 80
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_insights_tab(self):
        """Render the trade insights and pattern recognition tab"""
        st.subheader("🎯 AI Trade Insights & Pattern Recognition")
        
        trade_insights = self.cognitive_data.get_trade_insights()
        
        if trade_insights:
            st.success(f"Found {len(trade_insights)} AI-powered insights")
            
            for insight in trade_insights:
                insight_type = insight.get('type', 'general')
                message = insight.get('message', 'No message')
                confidence = insight.get('confidence', 0.0)
                action = insight.get('action', 'Monitor')
                timestamp = insight.get('timestamp', datetime.now().isoformat())
                
                # Color code by confidence
                if confidence >= 0.8:
                    border_color = "#28a745"  # Green
                    confidence_label = "High Confidence"
                elif confidence >= 0.6:
                    border_color = "#ffc107"  # Yellow
                    confidence_label = "Medium Confidence"
                else:
                    border_color = "#dc3545"  # Red
                    confidence_label = "Low Confidence"
                
                # Type icon
                type_icon = {
                    'pattern_recognition': '🔍',
                    'ai_analysis': '🤖',
                    'system_message': '⚙️',
                    'risk_alert': '⚠️'
                }.get(insight_type, '💡')
                
                st.markdown(f"""
                <div style="border-left: 4px solid {border_color}; padding: 1rem; margin: 1rem 0; background: white; border-radius: 5px;">
                    <h4>{type_icon} {insight_type.replace('_', ' ').title()}</h4>
                    <p><strong>Insight:</strong> {message}</p>
                    <p><strong>Recommended Action:</strong> {action}</p>
                    <p><strong>Confidence:</strong> {confidence:.1%} ({confidence_label})</p>
                    <small>Generated: {timestamp[-8:]}</small>
                </div>
                """, unsafe_allow_html=True)
                
                # Additional details if available
                if 'reasoning' in insight:
                    with st.expander("View AI Reasoning"):
                        st.write(insight['reasoning'])
        else:
            st.info("No trade insights available. This may be due to:")
            st.write("• Cognitive system offline")
            st.write("• No recent trading activity")
            st.write("• Insufficient data for pattern recognition")
        
        # Strategy recommendations
        st.subheader("📋 Strategy Optimization Recommendations")
        
        strategy_recommendations = self.cognitive_data.get_strategy_recommendations()
        
        if strategy_recommendations:
            for rec in strategy_recommendations:
                strategy = rec.get('strategy', 'general')
                recommendation = rec.get('recommendation', 'No recommendation')
                reason = rec.get('reason', 'No reason provided')
                confidence = rec.get('confidence', 0.0)
                priority = rec.get('priority', 'medium')
                
                # Priority color coding
                priority_colors = {
                    'high': '#dc3545',
                    'medium': '#ffc107',
                    'low': '#6c757d'
                }
                
                priority_color = priority_colors.get(priority, '#6c757d')
                
                st.markdown(f"""
                <div style="border: 1px solid {priority_color}; padding: 1rem; margin: 0.5rem 0; border-radius: 5px;">
                    <h5>📈 {strategy.title()} Strategy</h5>
                    <p><strong>Recommendation:</strong> {recommendation}</p>
                    <p><strong>Reasoning:</strong> {reason}</p>
                    <p><strong>Priority:</strong> <span style="color: {priority_color};">{priority.title()}</span> | 
                       <strong>Confidence:</strong> {confidence:.1%}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No strategy recommendations available at this time")
    
    def _render_risk_tab(self):
        """Render the risk analysis and predictions tab"""
        st.subheader("🛡️ AI-Powered Risk Analysis")
        
        risk_predictions = self.cognitive_data.get_risk_predictions()
        
        if risk_predictions:
            st.warning(f"⚠️ {len(risk_predictions)} risk factors identified")
            
            for prediction in risk_predictions:
                risk_type = prediction.get('type', 'general_risk')
                prediction_text = prediction.get('prediction', 'No prediction')
                confidence = prediction.get('confidence', 0.0)
                impact = prediction.get('impact', 'unknown')
                timeframe = prediction.get('timeframe', 'unknown')
                mitigation = prediction.get('mitigation', 'No mitigation suggested')
                
                # Impact color coding
                impact_colors = {
                    'high': '#dc3545',
                    'medium': '#ffc107',
                    'low': '#28a745',
                    'unknown': '#6c757d'
                }
                
                impact_color = impact_colors.get(impact, '#6c757d')
                
                # Risk type icon
                risk_icons = {
                    'system_risk': '⚙️',
                    'market_risk': '📊',
                    'strategy_risk': '🎯',
                    'liquidity_risk': '💧',
                    'technical_risk': '🔧'
                }
                
                risk_icon = risk_icons.get(risk_type, '⚠️')
                
                st.markdown(f"""
                <div style="border-left: 4px solid {impact_color}; padding: 1rem; margin: 1rem 0; background: #f8f9fa; border-radius: 5px;">
                    <h4>{risk_icon} {risk_type.replace('_', ' ').title()}</h4>
                    <p><strong>Prediction:</strong> {prediction_text}</p>
                    <p><strong>Impact Level:</strong> <span style="color: {impact_color};">{impact.title()}</span></p>
                    <p><strong>Timeframe:</strong> {timeframe}</p>
                    <p><strong>Confidence:</strong> {confidence:.1%}</p>
                    <p><strong>Suggested Mitigation:</strong> {mitigation}</p>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No significant risk factors detected")
            st.info("The AI system is continuously monitoring for potential risks")
        
        # Risk distribution chart
        if risk_predictions:
            st.subheader("📊 Risk Distribution Analysis")
            
            # Group risks by impact level
            impact_counts = {}
            for pred in risk_predictions:
                impact = pred.get('impact', 'unknown')
                impact_counts[impact] = impact_counts.get(impact, 0) + 1
            
            if impact_counts:
                fig = px.bar(
                    x=list(impact_counts.keys()),
                    y=list(impact_counts.values()),
                    title="Risk Factors by Impact Level",
                    color=list(impact_counts.keys()),
                    color_discrete_map={
                        'high': '#dc3545',
                        'medium': '#ffc107',
                        'low': '#28a745',
                        'unknown': '#6c757d'
                    }
                )
                
                fig.update_layout(
                    xaxis_title="Impact Level",
                    yaxis_title="Number of Risk Factors",
                    showlegend=False
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    def _render_performance_tab(self):
        """Render the performance analysis tab"""
        st.subheader("📈 Cognitive Performance Analysis")
        
        performance_insights = self.cognitive_data.get_performance_insights()
        
        # Performance metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            decision_accuracy = performance_insights.get('decision_accuracy', 0.0)
            st.metric(
                label="Decision Accuracy",
                value=f"{decision_accuracy:.1%}",
                delta="vs baseline"
            )
        
        with col2:
            confidence_calibration = performance_insights.get('confidence_calibration', 0.0)
            st.metric(
                label="Confidence Calibration",
                value=f"{confidence_calibration:.1%}",
                delta="predictive accuracy"
            )
        
        with col3:
            learning_rate = performance_insights.get('learning_rate', 0.0)
            st.metric(
                label="Learning Rate",
                value=f"{learning_rate:.1%}",
                delta="improvement trend"
            )
        
        with col4:
            adaptation_score = performance_insights.get('adaptation_score', 0.0)
            st.metric(
                label="Adaptation Score",
                value=f"{adaptation_score:.1%}",
                delta="market adaptation"
            )
        
        # Performance radar chart
        st.subheader("🎯 Performance Profile")
        
        metrics = [
            'Decision Accuracy',
            'Confidence Calibration',
            'Learning Rate',
            'Memory Efficiency',
            'Thought Quality',
            'Adaptation Score'
        ]
        
        values = [
            performance_insights.get('decision_accuracy', 0.0) * 100,
            performance_insights.get('confidence_calibration', 0.0) * 100,
            performance_insights.get('learning_rate', 0.0) * 100,
            performance_insights.get('memory_efficiency', 0.0) * 100,
            performance_insights.get('thought_quality', 0.0) * 100,
            performance_insights.get('adaptation_score', 0.0) * 100
        ]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=metrics,
            fill='toself',
            name='Current Performance'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )),
            showlegend=True,
            title="Cognitive Performance Profile"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Bias detection and improvement areas
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🧠 Detected Cognitive Biases")
            biases = performance_insights.get('bias_detection', [])
            
            if biases:
                for bias in biases:
                    st.warning(f"⚠️ {bias}")
            else:
                st.success("✅ No significant cognitive biases detected")
        
        with col2:
            st.subheader("🚀 Improvement Recommendations")
            improvements = performance_insights.get('improvement_areas', [])
            
            if improvements:
                for improvement in improvements:
                    st.info(f"💡 {improvement}")
            else:
                st.success("✅ Performance within optimal parameters")
    
    def _render_health_tab(self, cognitive_summary: Dict[str, Any]):
        """Render the cognitive system health tab"""
        st.subheader("⚙️ Cognitive System Health Dashboard")
        
        # AI Configuration Status (added like Log Monitor)
        st.subheader("🔧 AI Configuration")
        from dashboard.data.cognitive_data_provider import OPENAI_AVAILABLE, API_KEY_SOURCE
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if OPENAI_AVAILABLE:
                st.success("✅ OpenAI API Key: Available")
            else:
                st.error("❌ OpenAI API Key: Missing")
        
        with col2:
            st.caption("**Key Source:**")
            st.code(API_KEY_SOURCE)
            if OPENAI_AVAILABLE:
                st.caption("**Key Status:**")
                st.code("✅ Available (Hidden for security)")
        
        st.divider()
        
        cognitive_health = self.cognitive_data.get_cognitive_health()
        
        # System status overview
        system_status = cognitive_health.get('system_status', {})
        initialized = system_status.get('initialized', False)
        current_state = system_status.get('current_state', 'unknown')
        
        if initialized:
            st.success(f"✅ Cognitive system is operational (State: {current_state})")
        else:
            st.error("❌ Cognitive system is offline or not initialized")
        
        # Health check details
        st.subheader("🔍 Detailed Health Checks")
        
        health_checks = cognitive_health.get('health_checks', {})
        
        if health_checks:
            # Create health check grid
            health_items = list(health_checks.items())
            
            # Group into columns
            cols = st.columns(3)
            for i, (check_name, status) in enumerate(health_items):
                col_idx = i % 3
                with cols[col_idx]:
                    if status:
                        st.success(f"✅ {check_name.replace('_', ' ').title()}")
                    else:
                        st.error(f"❌ {check_name.replace('_', ' ').title()}")
        else:
            st.info("Health check details not available")
        
        # Component status
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💾 Memory System Health")
            memory_health = cognitive_health.get('memory_health', {})
            
            working_memory_count = memory_health.get('working_memory_count', 0)
            total_memories = memory_health.get('total_memories', 0)
            
            st.metric("Working Memory Items", working_memory_count)
            st.metric("Total Stored Memories", total_memories)
            
            if working_memory_count > 0:
                st.success("Memory system operational")
            else:
                st.warning("Memory system inactive")
        
        with col2:
            st.subheader("💭 Thought Processing Health")
            thought_health = cognitive_health.get('thought_processing', {})
            
            recent_thoughts = thought_health.get('recent_thoughts', 0)
            total_thoughts = thought_health.get('total_thoughts', 0)
            
            st.metric("Recent Thoughts (24h)", recent_thoughts)
            st.metric("Total Thoughts Recorded", total_thoughts)
            
            if recent_thoughts > 0:
                st.success("Thought processing active")
            else:
                st.warning("No recent thought activity")
        
        # Performance metrics
        st.subheader("📊 System Performance Metrics")
        
        cognitive_metrics = cognitive_health.get('cognitive_metrics', {})
        
        if cognitive_metrics:
            metrics_df = pd.DataFrame([
                {"Metric": "Decisions Made", "Value": cognitive_metrics.get('decisions_made', 0)},
                {"Metric": "Thoughts Recorded", "Value": cognitive_metrics.get('thoughts_recorded', 0)},
                {"Metric": "State Transitions", "Value": cognitive_metrics.get('state_transitions', 0)},
                {"Metric": "Memory Items Stored", "Value": cognitive_metrics.get('memory_items_stored', 0)},
                {"Metric": "Biases Detected", "Value": cognitive_metrics.get('biases_detected', 0)}
            ])
            
            st.dataframe(metrics_df, use_container_width=True, hide_index=True)
        else:
            st.info("Performance metrics not available")
        
        # System recommendations
        st.subheader("🔧 System Maintenance Recommendations")
        
        if not initialized:
            st.error("🚨 **Critical:** Cognitive system requires initialization")
            st.write("• Check cognitive system dependencies")
            st.write("• Verify GCP connectivity")
            st.write("• Review system logs for errors")
        elif recent_thoughts == 0:
            st.warning("⚠️ **Warning:** No recent cognitive activity")
            st.write("• Verify main trading system is running")
            st.write("• Check cognitive system integration")
        else:
            st.success("✅ **System Healthy:** All cognitive components operational")
            st.write("• Regular memory consolidation active")
            st.write("• Thought recording functioning normally")
            st.write("• Decision analysis learning from trades")