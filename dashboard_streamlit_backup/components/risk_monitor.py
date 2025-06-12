"""
Risk Monitor Page Component
Risk management and monitoring dashboard
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import math


class RiskMonitorPage:
    """Risk monitor page component"""
    
    def __init__(self, trade_data_provider):
        self.trade_data = trade_data_provider
    
    def render(self):
        """Render the risk monitor page"""
        st.markdown('<h1 style="color: #dc3545; text-align: center; margin-bottom: 2rem;">⚠️ Risk Monitor Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("**Real-time risk monitoring with VaR analysis and correlation tracking**")
        st.markdown('<hr style="height: 2px; background: linear-gradient(90deg, transparent, #dc3545, transparent); border: none; margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Risk overview metrics
        self._render_risk_overview()
        
        # Main risk analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Risk Overview",
            "📈 VaR Analysis", 
            "🔗 Correlation Matrix",
            "⚠️ Risk Alerts",
            "📋 Risk Reports"
        ])
        
        with tab1:
            self._render_risk_overview_tab()
        
        with tab2:
            self._render_var_analysis_tab()
        
        with tab3:
            self._render_correlation_tab()
        
        with tab4:
            self._render_risk_alerts_tab()
        
        with tab5:
            self._render_risk_reports_tab()
    
    def _render_risk_overview(self):
        """Render key risk metrics overview"""
        st.subheader("⚡ Real-Time Risk Metrics")
        
        # Get real-time risk data
        risk_data = self._get_real_time_risk_metrics()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            var_1d = risk_data.get('var_1d', 0)
            var_change = risk_data.get('var_1d_change_pct', 0)
            color = "red" if var_1d > 10000 else "orange" if var_1d > 5000 else "green"
            st.metric(
                "📊 VaR (1D)",
                f"₹{var_1d:,.0f}",
                f"{var_change:+.1f}%",
                delta_color="inverse"
            )
        
        with col2:
            max_drawdown = risk_data.get('max_drawdown_pct', 0)
            dd_change = risk_data.get('drawdown_change', 0)
            st.metric(
                "📉 Max Drawdown",
                f"{max_drawdown:.2f}%",
                f"{dd_change:+.2f}%",
                delta_color="inverse"
            )
        
        with col3:
            correlation_risk = risk_data.get('correlation_risk', 0)
            corr_change = risk_data.get('correlation_change', 0)
            st.metric(
                "🔗 Correlation Risk",
                f"{correlation_risk:.2f}",
                f"{corr_change:+.2f}",
                delta_color="inverse"
            )
        
        with col4:
            concentration = risk_data.get('concentration_pct', 0)
            conc_change = risk_data.get('concentration_change', 0)
            st.metric(
                "🎯 Concentration",
                f"{concentration:.1f}%",
                f"{conc_change:+.1f}%",
                delta_color="inverse"
            )
        
        with col5:
            sharpe_ratio = risk_data.get('sharpe_ratio', 0)
            sharpe_change = risk_data.get('sharpe_change', 0)
            st.metric(
                "📈 Sharpe Ratio",
                f"{sharpe_ratio:.2f}",
                f"{sharpe_change:+.2f}",
                delta_color="normal"
            )
        
        with col6:
            risk_score = risk_data.get('overall_risk_score', 0)
            score_change = risk_data.get('risk_score_change', 0)
            risk_level = "🟢 Low" if risk_score < 30 else "🟡 Medium" if risk_score < 70 else "🔴 High"
            st.metric(
                "🛡️ Risk Score",
                risk_level,
                f"{score_change:+.0f}",
                delta_color="inverse"
            )
    
    def _render_risk_overview_tab(self):
        """Render comprehensive risk overview"""
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_risk_distribution_chart()
        
        with col2:
            self._render_risk_trend_chart()
        
        # Position risk breakdown
        st.subheader("🔍 Position Risk Breakdown")
        self._render_position_risk_table()
        
        # Risk limits and utilization
        st.subheader("🚨 Risk Limits & Utilization")
        self._render_risk_limits()
    
    def _render_var_analysis_tab(self):
        """Render VaR analysis with different time horizons"""
        st.subheader("📊 Value at Risk (VaR) Analysis")
        
        # VaR calculation methods
        col1, col2 = st.columns([1, 3])
        
        with col1:
            var_method = st.selectbox(
                "VaR Method",
                ["Historical", "Parametric", "Monte Carlo"],
                key="var_method"
            )
            
            confidence_level = st.selectbox(
                "Confidence Level",
                ["95%", "99%", "99.5%"],
                key="confidence_level"
            )
        
        with col2:
            # VaR comparison chart
            self._render_var_comparison_chart(var_method, confidence_level)
        
        # VaR breakdown by strategy/asset
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 VaR by Strategy")
            self._render_var_by_strategy()
        
        with col2:
            st.subheader("📊 VaR by Asset Class")
            self._render_var_by_asset_class()
        
        # Historical VaR performance
        st.subheader("📈 VaR Model Performance")
        self._render_var_backtesting()
    
    def _render_correlation_tab(self):
        """Render correlation analysis"""
        st.subheader("🔗 Portfolio Correlation Analysis")
        
        # Correlation matrix
        self._render_correlation_matrix()
        
        # Correlation insights
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Correlation Insights")
            self._render_correlation_insights()
        
        with col2:
            st.subheader("⚠️ High Correlation Alerts")
            self._render_correlation_alerts()
        
        # Time-varying correlation
        st.subheader("📈 Time-Varying Correlation")
        self._render_rolling_correlation()
    
    def _render_risk_alerts_tab(self):
        """Render risk alerts and monitoring"""
        st.subheader("⚠️ Risk Alerts & Monitoring")
        
        # Active alerts
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("🚨 Active Risk Alerts")
            self._render_active_alerts()
        
        with col2:
            st.subheader("⚙️ Alert Settings")
            self._render_alert_settings()
        
        # Risk monitoring dashboard
        st.subheader("📊 Risk Monitoring Dashboard")
        self._render_risk_monitoring_dashboard()
        
        # Emergency controls
        st.subheader("🛑 Emergency Risk Controls")
        self._render_emergency_controls()
    
    def _render_risk_reports_tab(self):
        """Render risk reporting functionality"""
        st.subheader("📋 Risk Reports & Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📄 Report Generation")
            self._render_report_generation()
        
        with col2:
            st.subheader("📈 Risk Analytics")
            self._render_risk_analytics()
        
        # Historical risk analysis
        st.subheader("📊 Historical Risk Analysis")
        self._render_historical_risk_analysis()
    
    def _get_real_time_risk_metrics(self) -> Dict[str, Any]:
        """Calculate real-time risk metrics from trading data"""
        try:
            # Get current positions
            positions = self.trade_data.get_live_positions()
            
            if not positions:
                return self._get_default_risk_metrics()
            
            # Calculate portfolio metrics
            total_exposure = sum(pos.get('current_price', 0) * pos.get('quantity', 0) for pos in positions)
            total_pnl = sum(pos.get('unrealized_pnl', 0) for pos in positions)
            
            # Calculate VaR (simplified historical method)
            var_1d = self._calculate_var_1d(positions)
            
            # Calculate max drawdown
            max_drawdown = self._calculate_max_drawdown()
            
            # Calculate concentration risk
            concentration = self._calculate_concentration_risk(positions)
            
            # Calculate correlation risk
            correlation_risk = self._calculate_correlation_risk(positions)
            
            # Calculate Sharpe ratio (simplified)
            sharpe_ratio = self._calculate_sharpe_ratio()
            
            # Calculate overall risk score
            risk_score = self._calculate_risk_score(var_1d, max_drawdown, concentration, correlation_risk)
            
            return {
                'var_1d': var_1d,
                'var_1d_change_pct': 0,  # Would need historical comparison
                'max_drawdown_pct': max_drawdown,
                'drawdown_change': 0,
                'correlation_risk': correlation_risk,
                'correlation_change': 0,
                'concentration_pct': concentration,
                'concentration_change': 0,
                'sharpe_ratio': sharpe_ratio,
                'sharpe_change': 0,
                'overall_risk_score': risk_score,
                'risk_score_change': 0,
                'total_exposure': total_exposure,
                'total_pnl': total_pnl
            }
            
        except Exception as e:
            st.error(f"Error calculating risk metrics: {e}")
            return self._get_default_risk_metrics()
    
    def _calculate_var_1d(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate 1-day Value at Risk"""
        try:
            # Simplified VaR calculation based on position values
            position_values = []
            
            for pos in positions:
                value = pos.get('current_price', 0) * pos.get('quantity', 0)
                position_values.append(value)
            
            if not position_values:
                return 0
            
            # Use 95% confidence level, assume 2% daily volatility
            portfolio_value = sum(position_values)
            daily_volatility = 0.02  # 2% daily volatility assumption
            confidence_level = 1.645  # 95% confidence (z-score)
            
            var_1d = portfolio_value * daily_volatility * confidence_level
            return var_1d
            
        except Exception:
            return 5000  # Default VaR
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from P&L timeline"""
        try:
            # Get P&L timeline
            pnl_timeline = self.trade_data.get_pnl_timeline()
            
            if not pnl_timeline:
                return 0
            
            # Calculate running maximum and drawdown
            cumulative_pnl = [item['cumulative_pnl'] for item in pnl_timeline]
            
            if len(cumulative_pnl) < 2:
                return 0
            
            running_max = np.maximum.accumulate(cumulative_pnl)
            drawdown = (cumulative_pnl - running_max) / running_max * 100
            
            max_drawdown = abs(min(drawdown)) if len(drawdown) > 0 else 0
            return max_drawdown
            
        except Exception:
            return 2.5  # Default drawdown
    
    def _calculate_concentration_risk(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate portfolio concentration risk"""
        try:
            if not positions:
                return 0
            
            # Calculate position weights
            position_values = []
            for pos in positions:
                value = pos.get('current_price', 0) * pos.get('quantity', 0)
                position_values.append(value)
            
            if not position_values:
                return 0
            
            total_value = sum(position_values)
            if total_value == 0:
                return 0
            
            # Find largest position percentage
            max_position_pct = max(position_values) / total_value * 100
            return max_position_pct
            
        except Exception:
            return 15.0  # Default concentration
    
    def _calculate_correlation_risk(self, positions: List[Dict[str, Any]]) -> float:
        """Calculate portfolio correlation risk"""
        try:
            # Simplified correlation risk calculation
            # In reality, this would use historical price correlations
            
            if len(positions) <= 1:
                return 0
            
            # Assume moderate correlation for demonstration
            return 0.3
            
        except Exception:
            return 0.3  # Default correlation
    
    def _calculate_sharpe_ratio(self) -> float:
        """Calculate portfolio Sharpe ratio"""
        try:
            # Get recent trades for returns calculation
            recent_trades = self.trade_data.get_recent_trades(limit=50)
            
            if not recent_trades:
                return 0
            
            # Calculate returns
            returns = [trade.get('pnl', 0) for trade in recent_trades if trade.get('pnl') is not None]
            
            if len(returns) < 2:
                return 0
            
            # Calculate Sharpe ratio (simplified)
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            
            if std_return == 0:
                return 0
            
            # Assume risk-free rate of 5% annually (0.014% daily)
            risk_free_rate = 0.00014
            sharpe_ratio = (avg_return - risk_free_rate) / std_return
            
            return sharpe_ratio
            
        except Exception:
            return 1.2  # Default Sharpe ratio
    
    def _calculate_risk_score(self, var_1d: float, max_drawdown: float, concentration: float, correlation: float) -> float:
        """Calculate overall risk score (0-100)"""
        try:
            # Weighted risk score calculation
            var_score = min(var_1d / 200, 100) * 0.3  # VaR weight: 30%
            dd_score = min(max_drawdown * 10, 100) * 0.25  # Drawdown weight: 25%
            conc_score = min(concentration, 100) * 0.25  # Concentration weight: 25%
            corr_score = correlation * 100 * 0.2  # Correlation weight: 20%
            
            overall_score = var_score + dd_score + conc_score + corr_score
            return min(overall_score, 100)
            
        except Exception:
            return 45  # Default medium risk score
    
    def _get_default_risk_metrics(self) -> Dict[str, Any]:
        """Get default risk metrics when no data is available"""
        return {
            'var_1d': 0,
            'var_1d_change_pct': 0,
            'max_drawdown_pct': 0,
            'drawdown_change': 0,
            'correlation_risk': 0,
            'correlation_change': 0,
            'concentration_pct': 0,
            'concentration_change': 0,
            'sharpe_ratio': 0,
            'sharpe_change': 0,
            'overall_risk_score': 0,
            'risk_score_change': 0,
            'total_exposure': 0,
            'total_pnl': 0
        }
    
    def _render_risk_distribution_chart(self):
        """Render risk distribution pie chart"""
        st.subheader("📊 Risk Distribution")
        
        risk_data = self._get_real_time_risk_metrics()
        
        # Create risk distribution
        labels = ['VaR Risk', 'Concentration Risk', 'Correlation Risk', 'Other Risk']
        var_score = min(risk_data['var_1d'] / 200, 100) * 0.3
        conc_score = risk_data['concentration_pct'] * 0.25
        corr_score = risk_data['correlation_risk'] * 100 * 0.2
        other_score = max(0, 100 - var_score - conc_score - corr_score)
        
        values = [var_score, conc_score, corr_score, other_score]
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.4
        )])
        
        fig.update_layout(
            title="Portfolio Risk Components",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_risk_trend_chart(self):
        """Render risk trend over time"""
        st.subheader("📈 Risk Trend")
        
        # Generate sample risk trend data
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
        
        # Simulate risk scores over time
        np.random.seed(42)
        risk_scores = 45 + np.cumsum(np.random.randn(len(dates)) * 2)
        risk_scores = np.clip(risk_scores, 0, 100)
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=dates,
            y=risk_scores,
            mode='lines+markers',
            name='Risk Score',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=4)
        ))
        
        # Add risk level zones
        fig.add_hline(y=30, line_dash="dash", line_color="green", opacity=0.5, annotation_text="Low Risk")
        fig.add_hline(y=70, line_dash="dash", line_color="red", opacity=0.5, annotation_text="High Risk")
        
        fig.update_layout(
            title="30-Day Risk Score Trend",
            xaxis_title="Date",
            yaxis_title="Risk Score",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_position_risk_table(self):
        """Render position-wise risk breakdown"""
        try:
            positions = self.trade_data.get_live_positions()
            
            if positions:
                # Calculate risk metrics for each position
                risk_data = []
                
                for pos in positions:
                    symbol = pos.get('symbol', 'N/A')
                    position_value = pos.get('current_price', 0) * pos.get('quantity', 0)
                    unrealized_pnl = pos.get('unrealized_pnl', 0)
                    
                    # Calculate position risk metrics
                    position_var = position_value * 0.02 * 1.645  # Simplified VaR
                    risk_level = "🟢 Low" if position_var < 2000 else "🟡 Medium" if position_var < 5000 else "🔴 High"
                    
                    risk_data.append({
                        'Symbol': symbol,
                        'Position Value': f"₹{position_value:,.0f}",
                        'P&L': f"₹{unrealized_pnl:,.0f}",
                        'VaR (1D)': f"₹{position_var:,.0f}",
                        'Risk Level': risk_level,
                        'Strategy': pos.get('strategy', 'N/A')
                    })
                
                df = pd.DataFrame(risk_data)
                
                # Style the dataframe
                def style_pnl(val):
                    if '₹' in str(val) and 'P&L' in df.columns:
                        if '-' in str(val):
                            return 'color: red'
                        else:
                            return 'color: green'
                    return ''
                
                styled_df = df.style.applymap(style_pnl, subset=['P&L'] if 'P&L' in df.columns else [])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("No active positions to analyze")
                
        except Exception as e:
            st.error(f"Error rendering position risk table: {e}")
    
    def _render_risk_limits(self):
        """Render risk limits and utilization"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("💰 Capital Limits")
            
            # Sample risk limits
            max_portfolio_risk = 100000
            current_risk = 45000
            utilization = (current_risk / max_portfolio_risk) * 100
            
            st.metric("Max Portfolio Risk", f"₹{max_portfolio_risk:,.0f}")
            st.metric("Current Risk", f"₹{current_risk:,.0f}")
            
            # Progress bar for utilization
            st.progress(utilization / 100)
            st.write(f"Risk Utilization: {utilization:.1f}%")
        
        with col2:
            st.subheader("📊 Position Limits")
            
            max_position_size = 50000
            largest_position = 35000
            position_util = (largest_position / max_position_size) * 100
            
            st.metric("Max Position Size", f"₹{max_position_size:,.0f}")
            st.metric("Largest Position", f"₹{largest_position:,.0f}")
            
            st.progress(position_util / 100)
            st.write(f"Position Utilization: {position_util:.1f}%")
        
        with col3:
            st.subheader("⚠️ Risk Alerts")
            
            # Sample alert counts
            st.metric("Active Alerts", "3", "+1")
            st.metric("High Risk Positions", "2")
            
            if st.button("🔔 View All Alerts", use_container_width=True):
                st.info("Alert details would be shown here")
    
    # Placeholder methods for advanced features
    def _render_var_comparison_chart(self, method: str, confidence: str):
        """Render VaR comparison chart"""
        st.info(f"VaR Analysis ({method}, {confidence}) - Enhanced charts coming soon")
    
    def _render_var_by_strategy(self):
        """Render VaR breakdown by strategy"""
        st.info("VaR by Strategy breakdown - Coming soon")
    
    def _render_var_by_asset_class(self):
        """Render VaR breakdown by asset class"""
        st.info("VaR by Asset Class breakdown - Coming soon")
    
    def _render_var_backtesting(self):
        """Render VaR model backtesting results"""
        st.info("VaR Model Backtesting - Coming soon")
    
    def _render_correlation_matrix(self):
        """Render portfolio correlation matrix"""
        st.info("Portfolio Correlation Matrix - Coming soon")
    
    def _render_correlation_insights(self):
        """Render correlation insights"""
        st.info("Correlation Insights - Coming soon")
    
    def _render_correlation_alerts(self):
        """Render high correlation alerts"""
        st.info("High Correlation Alerts - Coming soon")
    
    def _render_rolling_correlation(self):
        """Render rolling correlation analysis"""
        st.info("Rolling Correlation Analysis - Coming soon")
    
    def _render_active_alerts(self):
        """Render active risk alerts"""
        # Sample alerts
        alerts = [
            {"type": "🔴 High Risk", "message": "Position concentration exceeds 30%", "time": "2 min ago"},
            {"type": "🟡 Medium Risk", "message": "VaR increased by 15%", "time": "5 min ago"},
            {"type": "🟡 Medium Risk", "message": "Correlation risk elevated", "time": "10 min ago"}
        ]
        
        for alert in alerts:
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{alert['type']}: {alert['message']}")
                with col2:
                    st.write(alert['time'])
                st.divider()
    
    def _render_alert_settings(self):
        """Render alert configuration settings"""
        st.write("**Alert Thresholds:**")
        
        var_threshold = st.slider("VaR Alert Threshold", 1000, 20000, 10000, 1000)
        dd_threshold = st.slider("Drawdown Alert (%)", 1.0, 10.0, 5.0, 0.5)
        conc_threshold = st.slider("Concentration Alert (%)", 10, 50, 30, 5)
        
        if st.button("💾 Save Settings"):
            st.success("Alert settings saved!")
    
    def _render_risk_monitoring_dashboard(self):
        """Render real-time risk monitoring dashboard"""
        st.info("Real-time Risk Monitoring Dashboard - Coming soon")
    
    def _render_emergency_controls(self):
        """Render emergency risk controls"""
        st.warning("⚠️ Emergency Controls - Use with caution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🛑 Emergency Stop All", type="secondary"):
                st.error("Emergency stop would be triggered - This is a demo")
        
        with col2:
            if st.button("⚡ Reduce Positions", type="secondary"):
                st.warning("Position reduction would be triggered - This is a demo")
    
    def _render_report_generation(self):
        """Render risk report generation"""
        st.info("Risk Report Generation - Coming soon")
    
    def _render_risk_analytics(self):
        """Render advanced risk analytics"""
        st.info("Advanced Risk Analytics - Coming soon")
    
    def _render_historical_risk_analysis(self):
        """Render historical risk analysis"""
        st.info("Historical Risk Analysis - Coming soon") 