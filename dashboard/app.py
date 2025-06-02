"""
Main Trading Dashboard Application
Streamlit-based real-time monitoring interface for TRON trading system
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import asyncio
import time
import json
from typing import Dict, List, Any, Optional

# Dashboard components
from dashboard.components.overview import OverviewPage
from dashboard.components.live_trades import LiveTradesPage
from dashboard.components.pnl_analysis import PnLAnalysisPage
from dashboard.components.system_health import SystemHealthPage
from dashboard.components.cognitive_insights import CognitiveInsightsPage
from dashboard.components.risk_monitor import RiskMonitorPage
from dashboard.components.strategy_performance import StrategyPerformancePage

# Data providers
from dashboard.data.trade_data_provider import TradeDataProvider
from dashboard.data.system_data_provider import SystemDataProvider
from dashboard.data.cognitive_data_provider import CognitiveDataProvider

# Utils
from dashboard.utils.auth import authenticate_user
from dashboard.utils.config import DashboardConfig
from dashboard.utils.notifications import NotificationManager


class TradingDashboard:
    """Main Trading Dashboard Application"""
    
    def __init__(self):
        self.config = DashboardConfig()
        self.trade_data = TradeDataProvider()
        self.system_data = SystemDataProvider()
        self.cognitive_data = CognitiveDataProvider()
        self.notification_manager = NotificationManager()
        
        # Initialize session state
        self._initialize_session_state()
        
    def _initialize_session_state(self):
        """Initialize Streamlit session state variables"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'last_refresh' not in st.session_state:
            st.session_state.last_refresh = datetime.now()
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = True
        if 'refresh_interval' not in st.session_state:
            st.session_state.refresh_interval = 30  # seconds
        if 'selected_timeframe' not in st.session_state:
            st.session_state.selected_timeframe = "1D"
        if 'alerts_enabled' not in st.session_state:
            st.session_state.alerts_enabled = True
    
    def run(self):
        """Main application entry point"""
        # Configure Streamlit page
        st.set_page_config(
            page_title="TRON Trading Dashboard",
            page_icon="📈",
            layout="wide",
            initial_sidebar_state="expanded",
            menu_items={
                'Get Help': 'https://github.com/your-repo/tron-trading',
                'Report a bug': 'https://github.com/your-repo/tron-trading/issues',
                'About': "TRON Trading System Dashboard v1.0.0"
            }
        )
        
        # Custom CSS
        self._inject_custom_css()
        
        # Authentication check
        if not st.session_state.authenticated:
            self._show_login_page()
            return
        
        # Main dashboard
        self._show_main_dashboard()
    
    def _inject_custom_css(self):
        """Inject custom CSS for better styling"""
        st.markdown("""
        <style>
        .main-header {
            background: linear-gradient(90deg, #1f4e79 0%, #2d5aa0 100%);
            padding: 1rem;
            border-radius: 10px;
            margin-bottom: 2rem;
            color: white;
        }
        
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 4px solid #1f4e79;
        }
        
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        
        .trade-card {
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            padding: 1rem;
            margin: 0.5rem 0;
            background: white;
        }
        
        .profit { color: #28a745; font-weight: bold; }
        .loss { color: #dc3545; font-weight: bold; }
        
        .sidebar .sidebar-content {
            background: #f8f9fa;
        }
        
        .stAlert > div {
            padding: 0.5rem 1rem;
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)
    
    def _show_login_page(self):
        """Show authentication page"""
        st.markdown("""
        <div class="main-header">
            <h1>🔐 TRON Trading Dashboard</h1>
            <p>Secure access to your trading system</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.subheader("Login")
            
            with st.form("login_form"):
                username = st.text_input("Username")
                password = st.text_input("Password", type="password")
                remember_me = st.checkbox("Remember me")
                
                if st.form_submit_button("Login", use_container_width=True):
                    if authenticate_user(username, password):
                        st.session_state.authenticated = True
                        st.success("Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Invalid credentials")
    
    def _show_main_dashboard(self):
        """Show main dashboard interface"""
        # Header
        self._show_header()
        
        # Sidebar
        self._show_sidebar()
        
        # Main content based on selected page
        page = st.session_state.get('selected_page', '🏠 Overview')
        
        if page == "🏠 Overview":
            OverviewPage(self.trade_data, self.system_data).render()
        elif page == "📊 Live Trades":
            LiveTradesPage(self.trade_data).render()
        elif page == "💰 P&L Analysis":
            PnLAnalysisPage(self.trade_data).render()
        elif page == "⚙️ System Health":
            SystemHealthPage(self.system_data).render()
        elif page == "🧠 Cognitive Insights":
            CognitiveInsightsPage(self.cognitive_data).render()
        elif page == "🛡️ Risk Monitor":
            RiskMonitorPage(self.trade_data, self.system_data).render()
        elif page == "📈 Strategy Performance":
            StrategyPerformancePage(self.trade_data).render()
    
    def _show_header(self):
        """Show dashboard header with key metrics"""
        st.markdown("""
        <div class="main-header">
            <h1>📈 TRON Trading Dashboard</h1>
            <p>Real-time monitoring and analytics</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        # Get real-time data
        summary = self.trade_data.get_daily_summary()
        system_status = self.system_data.get_system_status()
        
        with col1:
            pnl = summary.get('total_pnl', 0)
            pnl_color = "green" if pnl >= 0 else "red"
            st.metric(
                "💰 Today's P&L",
                f"₹{pnl:,.2f}",
                f"{summary.get('pnl_change_pct', 0):+.1f}%"
            )
        
        with col2:
            st.metric(
                "📊 Active Trades",
                summary.get('active_trades', 0),
                f"{summary.get('trades_change', 0):+d}"
            )
        
        with col3:
            win_rate = summary.get('win_rate', 0)
            st.metric(
                "🎯 Win Rate",
                f"{win_rate:.1f}%",
                f"{summary.get('win_rate_change', 0):+.1f}%"
            )
        
        with col4:
            status = system_status.get('overall_status', 'unknown')
            status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
            st.metric(
                "⚡ System Status",
                f"{status_icon} {status.title()}",
                f"Uptime: {system_status.get('uptime_hours', 0):.1f}h"
            )
        
        with col5:
            portfolio_value = summary.get('portfolio_value', 0)
            st.metric(
                "💼 Portfolio",
                f"₹{portfolio_value:,.0f}",
                f"{summary.get('portfolio_change_pct', 0):+.1f}%"
            )
    
    def _show_sidebar(self):
        """Show sidebar with navigation and controls"""
        with st.sidebar:
            st.title("🎯 Navigation")
            
            # Page selection
            pages = [
                "🏠 Overview",
                "📊 Live Trades", 
                "💰 P&L Analysis",
                "⚙️ System Health",
                "🧠 Cognitive Insights",
                "🛡️ Risk Monitor",
                "📈 Strategy Performance"
            ]
            
            selected_page = st.selectbox(
                "Select Page",
                pages,
                key="selected_page"
            )
            
            st.divider()
            
            # Controls
            st.subheader("⚙️ Controls")
            
            # Auto-refresh toggle
            auto_refresh = st.toggle(
                "Auto Refresh",
                value=st.session_state.auto_refresh,
                key="auto_refresh"
            )
            
            if auto_refresh:
                refresh_interval = st.slider(
                    "Refresh Interval (seconds)",
                    min_value=10,
                    max_value=300,
                    value=st.session_state.refresh_interval,
                    step=10,
                    key="refresh_interval"
                )
            
            # Manual refresh button
            if st.button("🔄 Refresh Now", use_container_width=True):
                st.session_state.last_refresh = datetime.now()
                st.rerun()
            
            # Timeframe selection
            st.selectbox(
                "Timeframe",
                ["1H", "4H", "1D", "1W", "1M"],
                index=2,  # Default to 1D
                key="selected_timeframe"
            )
            
            st.divider()
            
            # Alerts section
            st.subheader("🔔 Alerts")
            
            alerts_enabled = st.toggle(
                "Enable Alerts",
                value=st.session_state.alerts_enabled,
                key="alerts_enabled"
            )
            
            if alerts_enabled:
                # Show recent alerts
                recent_alerts = self.notification_manager.get_recent_alerts(limit=5)
                
                if recent_alerts:
                    st.write("**Recent Alerts:**")
                    for alert in recent_alerts:
                        alert_type = alert.get('type', 'info')
                        icon = "🔴" if alert_type == 'critical' else "🟡" if alert_type == 'warning' else "🔵"
                        st.write(f"{icon} {alert.get('message', '')}")
                else:
                    st.info("No recent alerts")
            
            st.divider()
            
            # System info
            st.subheader("ℹ️ System Info")
            st.write(f"**Version:** {self.config.version}")
            st.write(f"**Environment:** {self.config.environment}")
            st.write(f"**Last Update:** {st.session_state.last_refresh.strftime('%H:%M:%S')}")
            
            # Logout button
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.authenticated = False
                st.rerun()
        
        # Auto-refresh logic
        if st.session_state.auto_refresh:
            time_since_refresh = (datetime.now() - st.session_state.last_refresh).total_seconds()
            if time_since_refresh >= st.session_state.refresh_interval:
                st.session_state.last_refresh = datetime.now()
                st.rerun()


def main():
    """Main entry point for the dashboard"""
    dashboard = TradingDashboard()
    dashboard.run()


if __name__ == "__main__":
    main() 