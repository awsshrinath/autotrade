#!/usr/bin/env python3
"""
Tron Trading Dashboard - Main Application
Comprehensive trading dashboard with cognitive insights, system monitoring, and analytics.
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import dashboard components
from dashboard.data.system_data_provider import SystemDataProvider
from dashboard.data.cognitive_data_provider import CognitiveDataProvider
from dashboard.data.trade_data_provider import TradeDataProvider
from dashboard.components.system_health import SystemHealthPage
from dashboard.components.live_trades import LiveTradesPage
from dashboard.components.cognitive_insights import CognitiveInsightsPage
from dashboard.components.pnl_analysis import PnLAnalysisPage
from dashboard.components.risk_monitor import RiskMonitorPage
from dashboard.components.strategy_performance import StrategyPerformancePage

# Page configuration
st.set_page_config(
    page_title="Tron Trading Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem 0;
    }
    
    .page-header {
        font-size: 2.2rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #e0e0e0;
    }
    
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
    }
    
    .sidebar-info {
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #2196f3;
    }
    
    .connection-status {
        padding: 0.75rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        font-weight: bold;
        text-align: center;
        transition: all 0.2s ease;
    }
    
    .status-healthy { 
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        color: #155724; 
        border-left: 4px solid #28a745;
    }
    
    .status-warning { 
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        color: #856404; 
        border-left: 4px solid #ffc107;
    }
    
    .status-error { 
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        color: #721c24; 
        border-left: 4px solid #dc3545;
    }
    
    .analytics-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border-top: 4px solid #1f77b4;
    }
    
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: bold;
        margin: 0.25rem 0;
        transition: all 0.2s ease;
    }
    
    .quick-action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    .section-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #1f77b4, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    .nav-item {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 6px;
        transition: background-color 0.2s ease;
    }
    
    .nav-item:hover {
        background-color: #f0f2f6;
    }
    
    .metric-highlight {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    
         .stTabs [data-baseweb="tab-list"] {
         gap: 8px;
         margin-bottom: 1rem;
     }
     
     .stTabs [data-baseweb="tab"] {
         background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
         border-radius: 12px 12px 0 0;
         padding: 12px 20px;
         font-weight: 600;
         border: 1px solid #dee2e6;
         transition: all 0.2s ease;
     }
     
     .stTabs [data-baseweb="tab"]:hover {
         background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
         transform: translateY(-1px);
     }
     
     .stTabs [aria-selected="true"] {
         background: linear-gradient(135deg, #1f77b4 0%, #0d6efd 100%);
         color: white;
         border-color: #1f77b4;
         box-shadow: 0 2px 4px rgba(31, 119, 180, 0.2);
     }
     
     .stTabs [data-baseweb="tab-panel"] {
         background: white;
         border-radius: 0 12px 12px 12px;
         border: 1px solid #dee2e6;
         padding: 1.5rem;
         margin-top: -1px;
     }
     
     .sidebar .stSelectbox > div > div {
         background-color: #f8f9fa;
         border-radius: 8px;
     }
     
     .element-container button {
         transition: all 0.2s ease;
     }
     
     .element-container button:hover {
         transform: translateY(-1px);
         box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
     }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_system_status():
    """Get cached system status"""
    try:
        system_data = SystemDataProvider()
        return system_data.get_system_health()
    except Exception as e:
        return {"status": "error", "message": str(e)}

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_cognitive_status():
    """Get cached cognitive system status"""
    try:
        cognitive_data = CognitiveDataProvider()
        return cognitive_data.get_cognitive_summary()
    except Exception as e:
        return {"status": "error", "message": str(e)}

def render_sidebar():
    """Render the sidebar with navigation and status"""
    st.sidebar.markdown("## 🚀 Tron Trading Dashboard")
    st.sidebar.markdown("*Advanced Trading Analytics*")
    
    # Navigation sections
    st.sidebar.markdown("### 📊 Navigation")
    
    # Organized page selection with sections
    st.sidebar.markdown("**🏠 Main**")
    pages = {
        "🏠 Overview": "overview",
        "📈 Analytics Hub": "analytics",
    }
    
    st.sidebar.markdown("**📊 Analysis Tools**")
    analysis_pages = {
        "💰 P&L Analysis": "pnl",
        "⚠️ Risk Monitor": "risk",
        "🎯 Strategy Performance": "strategy"
    }
    pages.update(analysis_pages)
    
    st.sidebar.markdown("**🔧 System Tools**")
    system_pages = {
        "💹 Live Trades": "trades", 
        "🧠 Cognitive Insights": "cognitive",
        "⚙️ System Health": "health"
    }
    pages.update(system_pages)
    
    selected_page = st.sidebar.selectbox(
        "Choose Dashboard",
        list(pages.keys()),
        key="page_selector"
    )
    
    # Quick status indicators
    st.sidebar.markdown("### 🔍 Quick Status")
    
    # System status
    system_status = get_system_status()
    if system_status.get("status") == "healthy":
        st.sidebar.markdown('<div class="connection-status status-healthy">✅ System Online</div>', unsafe_allow_html=True)
    elif system_status.get("status") == "warning":
        st.sidebar.markdown('<div class="connection-status status-warning">⚠️ System Warning</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="connection-status status-error">❌ System Error</div>', unsafe_allow_html=True)
    
    # Cognitive status
    cognitive_status = get_cognitive_status()
    if cognitive_status.get("system_status", {}).get("initialized", False):
        st.sidebar.markdown('<div class="connection-status status-healthy">🧠 Cognitive Online</div>', unsafe_allow_html=True)
    else:
        st.sidebar.markdown('<div class="connection-status status-warning">🧠 Cognitive Offline</div>', unsafe_allow_html=True)
    
    # Connection info
    st.sidebar.markdown("### 🔗 Connection Info")
    st.sidebar.markdown('<div class="sidebar-info">', unsafe_allow_html=True)
    
    # Check environment variables
    env_status = []
    if os.getenv('OPENAI_API_KEY'):
        env_status.append("✅ OpenAI Connected")
    else:
        env_status.append("❌ OpenAI Not Set")
    
    if os.getenv('GCP_PROJECT_ID'):
        env_status.append("✅ GCP Configured")
    else:
        env_status.append("❌ GCP Not Set")
    
    for status in env_status:
        st.sidebar.markdown(f"<small>{status}</small>", unsafe_allow_html=True)
    
    st.sidebar.markdown('</div>', unsafe_allow_html=True)
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    return pages[selected_page]

def render_overview_page():
    """Render the overview/dashboard page"""
    st.markdown('<h1 class="main-header">🚀 Tron Trading Dashboard</h1>', unsafe_allow_html=True)
    
    # Hero metrics section
    st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
    st.markdown("### 📊 System Overview")
    
    # Quick metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    system_status = get_system_status()
    cognitive_status = get_cognitive_status()
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="🔧 System Status",
            value="Online" if system_status.get("status") == "healthy" else "Issues",
            delta="Operational" if system_status.get("status") == "healthy" else "Check logs"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        cognitive_initialized = cognitive_status.get("system_status", {}).get("initialized", False)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="🧠 Cognitive AI",
            value="Active" if cognitive_initialized else "Offline",
            delta="AI Analysis" if cognitive_initialized else "Fallback mode"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        total_thoughts = cognitive_status.get("thought_summary", {}).get("total_thoughts", 0)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="💭 AI Thoughts",
            value=f"{total_thoughts:,}",
            delta="Recorded decisions"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        total_memories = cognitive_status.get("memory_summary", {}).get("total_memories", 0)
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric(
            label="🧲 Memory Items",
            value=f"{total_memories:,}",
            delta="Stored experiences"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Section divider
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    
    # Main content areas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # System status section
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 🔍 System Health Status")
        
        # Recent activity summary
        if cognitive_initialized:
            st.success("🧠 **Cognitive Insights Available** - AI-powered analysis is active")
            st.info("💡 Navigate to the Cognitive Insights tab for detailed AI analysis")
        else:
            st.warning("🧠 **Cognitive System Offline** - Using fallback mode")
            st.info("ℹ️ Some advanced features may be limited")
        
        # System health summary
        if system_status.get("status") == "healthy":
            st.success("✅ All systems operational")
        elif system_status.get("status") == "warning":
            st.warning("⚠️ Some issues detected - check System Health tab")
        else:
            st.error("❌ System errors detected - immediate attention required")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Analytics overview section
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 📈 Analytics Overview")
        
        # Quick analytics metrics in columns
        acol1, acol2, acol3 = st.columns(3)
        
        with acol1:
            st.markdown("**💰 P&L Analysis**")
            st.markdown("- Real-time profit tracking")
            st.markdown("- Performance analytics")
            st.markdown("- Risk-adjusted returns")
        
        with acol2:
            st.markdown("**⚠️ Risk Monitor**")
            st.markdown("- VaR calculations")
            st.markdown("- Correlation analysis")
            st.markdown("- Risk alerts system")
        
        with acol3:
            st.markdown("**🎯 Strategy Performance**")
            st.markdown("- Individual strategy metrics")
            st.markdown("- Win/loss analysis")
            st.markdown("- AI optimization")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Quick actions section
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 🚀 Quick Actions")
        
        # Quick action buttons with better styling
        st.markdown("**🔍 Analysis Tools**")
        if st.button("💰 P&L Analysis", use_container_width=True):
            st.session_state.page_selector = "💰 P&L Analysis"
            st.rerun()
        
        if st.button("⚠️ Risk Monitor", use_container_width=True):
            st.session_state.page_selector = "⚠️ Risk Monitor"
            st.rerun()
        
        if st.button("🎯 Strategy Performance", use_container_width=True):
            st.session_state.page_selector = "🎯 Strategy Performance"
            st.rerun()
        
        st.markdown("---")
        st.markdown("**🧠 System Tools**")
        
        if st.button("🧠 Cognitive Insights", use_container_width=True):
            st.session_state.page_selector = "🧠 Cognitive Insights"
            st.rerun()
        
        if st.button("💹 Live Trades", use_container_width=True):
            st.session_state.page_selector = "💹 Live Trades"
            st.rerun()
        
        if st.button("⚙️ System Health", use_container_width=True):
            st.session_state.page_selector = "⚙️ System Health"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent alerts section
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 🔔 System Alerts")
        
        alert_count = 0
        if not cognitive_initialized:
            st.warning("🧠 Cognitive system offline")
            alert_count += 1
        
        if not os.getenv('GCP_PROJECT_ID'):
            st.error("🔗 GCP not configured")
            alert_count += 1
        
        if not os.getenv('OPENAI_API_KEY'):
            st.error("🔑 OpenAI API not set")
            alert_count += 1
        
        if alert_count == 0:
            st.success("✅ No active alerts")
        else:
            st.markdown(f"**{alert_count} alert(s) detected**")
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_analytics_page():
    """Render the comprehensive analytics hub page"""
    st.markdown('<h1 class="main-header">📈 Analytics Hub</h1>', unsafe_allow_html=True)
    
    # Analytics navigation tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Overview",
        "💰 Financial Analysis", 
        "⚠️ Risk Management",
        "📊 Performance Metrics"
    ])
    
    with tab1:
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Analytics Overview")
        st.markdown("**Welcome to the Tron Trading Analytics Hub** - Your comprehensive suite of trading analysis tools.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Feature cards
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
            st.markdown("#### 💰 P&L Analysis")
            st.markdown("""
            **Real-time financial tracking:**
            - Profit & Loss calculations
            - Performance metrics
            - Daily/weekly/monthly breakdowns
            - Risk-adjusted returns
            - Cumulative performance charts
            """)
            if st.button("Open P&L Analysis", key="pnl_from_analytics", use_container_width=True):
                st.session_state.page_selector = "💰 P&L Analysis"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
            st.markdown("#### ⚠️ Risk Monitor")
            st.markdown("""
            **Comprehensive risk management:**
            - Value at Risk (VaR) calculations
            - Maximum drawdown analysis
            - Correlation matrices
            - Risk alerts & notifications
            - Portfolio concentration tracking
            """)
            if st.button("Open Risk Monitor", key="risk_from_analytics", use_container_width=True):
                st.session_state.page_selector = "⚠️ Risk Monitor"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
            st.markdown("#### 🎯 Strategy Performance")
            st.markdown("""
            **Strategy optimization tools:**
            - Individual strategy analysis
            - Win/loss breakdowns
            - Performance comparisons
            - AI-powered optimization
            - Backtest vs live tracking
            """)
            if st.button("Open Strategy Performance", key="strategy_from_analytics", use_container_width=True):
                st.session_state.page_selector = "🎯 Strategy Performance"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    
    with tab2:
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 💰 Financial Analysis Tools")
        
        # Quick metrics summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📈 Total P&L", "$0.00", "Real-time tracking")
        with col2:
            st.metric("📊 Win Rate", "0.0%", "Strategy success")
        with col3:
            st.metric("🎯 Sharpe Ratio", "0.00", "Risk-adjusted return")
        with col4:
            st.metric("📉 Max Drawdown", "0.0%", "Worst decline")
        
        st.markdown("---")
        st.markdown("**Access detailed P&L analysis including profit tracking, performance metrics, and risk-adjusted returns.**")
        
        if st.button("🚀 Launch P&L Analysis Dashboard", key="launch_pnl", use_container_width=True):
            st.session_state.page_selector = "💰 P&L Analysis"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### ⚠️ Risk Management Tools")
        
        # Risk metrics summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📉 1-Day VaR", "0.0%", "Daily risk exposure")
        with col2:
            st.metric("🎯 Risk Score", "0/10", "Overall risk level")
        with col3:
            st.metric("⚡ Correlation Risk", "Low", "Portfolio correlation")
        
        st.markdown("---")
        st.markdown("**Monitor portfolio risk with VaR calculations, correlation analysis, and real-time alerts.**")
        
        if st.button("🚀 Launch Risk Monitor Dashboard", key="launch_risk", use_container_width=True):
            st.session_state.page_selector = "⚠️ Risk Monitor"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown('<div class="analytics-card">', unsafe_allow_html=True)
        st.markdown("### 📊 Performance Metrics")
        
        # Performance summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("🎯 Active Strategies", "0", "Currently running")
        with col2:
            st.metric("💰 Profitable Strategies", "0", "Positive returns")
        with col3:
            st.metric("🏆 Best Strategy", "None", "Top performer")
        
        st.markdown("---")
        st.markdown("**Analyze individual strategy performance, compare results, and get AI-powered optimization recommendations.**")
        
        if st.button("🚀 Launch Strategy Performance Dashboard", key="launch_strategy", use_container_width=True):
            st.session_state.page_selector = "🎯 Strategy Performance"
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    try:
        # Initialize data providers
        if 'system_data' not in st.session_state:
            st.session_state.system_data = SystemDataProvider()
        
        if 'cognitive_data' not in st.session_state:
            st.session_state.cognitive_data = CognitiveDataProvider()
        
        if 'trade_data' not in st.session_state:
            st.session_state.trade_data = TradeDataProvider()
        
        # Render sidebar and get selected page
        selected_page = render_sidebar()
        
        # Render the selected page
        if selected_page == "overview":
            render_overview_page()
        
        elif selected_page == "trades":
            trades_page = LiveTradesPage(st.session_state.trade_data)
            trades_page.render()
        
        elif selected_page == "cognitive":
            cognitive_page = CognitiveInsightsPage(st.session_state.cognitive_data)
            cognitive_page.render()
        
        elif selected_page == "health":
            health_page = SystemHealthPage(st.session_state.system_data)
            health_page.render()
        
        elif selected_page == "analytics":
            render_analytics_page()
        
        elif selected_page == "pnl":
            pnl_page = PnLAnalysisPage(st.session_state.trade_data)
            pnl_page.render()
        
        elif selected_page == "risk":
            risk_page = RiskMonitorPage(st.session_state.trade_data)
            risk_page.render()
        
        elif selected_page == "strategy":
            strategy_page = StrategyPerformancePage(st.session_state.trade_data)
            strategy_page.render()
        
        else:
            st.error(f"Unknown page: {selected_page}")
    
    except Exception as e:
        st.error(f"❌ **Application Error:** {str(e)}")
        st.exception(e)
        
        # Show connection diagnostics button
        if st.button("🔍 Run Connection Diagnostics"):
            with st.spinner("Running diagnostics..."):
                try:
                    # Import and run diagnostics
                    from dashboard.utils.connection_diagnostics import ConnectionDiagnostics
                    
                    diagnostics = ConnectionDiagnostics()
                    results = diagnostics.run_full_diagnostics()
                    
                    # Display results
                    st.subheader("🔍 Connection Diagnostics Results")
                    
                    status = results.get('status', 'unknown')
                    if status == 'healthy':
                        st.success(f"✅ System Status: {status.upper()}")
                    elif status == 'warning':
                        st.warning(f"⚠️ System Status: {status.upper()}")
                    else:
                        st.error(f"❌ System Status: {status.upper()}")
                    
                    # Show issues
                    issues = results.get('issues', [])
                    if issues:
                        st.subheader("⚠️ Issues Found")
                        for issue in issues:
                            severity = issue.get('severity', 'unknown')
                            description = issue.get('description', 'Unknown issue')
                            
                            if severity == 'critical':
                                st.error(f"🔴 **{severity.upper()}:** {description}")
                            elif severity == 'high':
                                st.warning(f"🟠 **{severity.upper()}:** {description}")
                            else:
                                st.info(f"🟡 **{severity.upper()}:** {description}")
                    
                    # Show recommendations
                    recommendations = results.get('recommendations', [])
                    if recommendations:
                        st.subheader("💡 Recommendations")
                        for rec in recommendations:
                            st.info(f"**{rec.get('title', 'Recommendation')}:** {rec.get('description', 'No description')}")
                
                except Exception as diag_error:
                    st.error(f"Failed to run diagnostics: {diag_error}")

if __name__ == "__main__":
    main()