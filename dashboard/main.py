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
from dashboard.components.system_health import SystemHealthPage
from dashboard.components.live_trades import LiveTradesPage
from dashboard.components.cognitive_insights import CognitiveInsightsPage

# Page configuration
st.set_page_config(
    page_title="Tron Trading Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
        margin-bottom: 1rem;
    }
    
    .sidebar-info {
        background: #e3f2fd;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .connection-status {
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.5rem 0;
        font-weight: bold;
    }
    
    .status-healthy { background-color: #d4edda; color: #155724; }
    .status-warning { background-color: #fff3cd; color: #856404; }
    .status-error { background-color: #f8d7da; color: #721c24; }
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
    
    # Navigation
    st.sidebar.markdown("### 📊 Navigation")
    
    # Page selection
    pages = {
        "🏠 Overview": "overview",
        "💹 Live Trades": "trades", 
        "🧠 Cognitive Insights": "cognitive",
        "⚙️ System Health": "health",
        "📈 Analytics": "analytics"
    }
    
    selected_page = st.sidebar.selectbox(
        "Select Page",
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
    
    # Quick metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    system_status = get_system_status()
    cognitive_status = get_cognitive_status()
    
    with col1:
        st.metric(
            label="System Status",
            value="Online" if system_status.get("status") == "healthy" else "Issues",
            delta="Operational" if system_status.get("status") == "healthy" else "Check logs"
        )
    
    with col2:
        cognitive_initialized = cognitive_status.get("system_status", {}).get("initialized", False)
        st.metric(
            label="Cognitive System",
            value="Active" if cognitive_initialized else "Offline",
            delta="AI Analysis" if cognitive_initialized else "Fallback mode"
        )
    
    with col3:
        total_thoughts = cognitive_status.get("thought_summary", {}).get("total_thoughts", 0)
        st.metric(
            label="AI Thoughts",
            value=f"{total_thoughts:,}",
            delta="Recorded decisions"
        )
    
    with col4:
        total_memories = cognitive_status.get("memory_summary", {}).get("total_memories", 0)
        st.metric(
            label="Memory Items",
            value=f"{total_memories:,}",
            delta="Stored experiences"
        )
    
    # Main content areas
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("📊 System Overview")
        
        # Recent activity summary
        if cognitive_initialized:
            st.success("🧠 **Cognitive Insights Available** - AI-powered analysis is active")
            st.info("💡 Navigate to the Cognitive Insights tab for detailed AI analysis")
        else:
            st.warning("🧠 **Cognitive System Offline** - Using fallback mode")
            st.info("ℹ️ Some advanced features may be limited")
        
        # System health summary
        st.subheader("⚙️ System Health Summary")
        
        if system_status.get("status") == "healthy":
            st.success("✅ All systems operational")
        elif system_status.get("status") == "warning":
            st.warning("⚠️ Some issues detected - check System Health tab")
        else:
            st.error("❌ System errors detected - immediate attention required")
    
    with col2:
        st.subheader("🔗 Quick Actions")
        
        # Quick action buttons
        if st.button("🧠 View Cognitive Insights", use_container_width=True):
            st.session_state.page_selector = "🧠 Cognitive Insights"
            st.rerun()
        
        if st.button("💹 Check Live Trades", use_container_width=True):
            st.session_state.page_selector = "💹 Live Trades"
            st.rerun()
        
        if st.button("⚙️ System Diagnostics", use_container_width=True):
            st.session_state.page_selector = "⚙️ System Health"
            st.rerun()
        
        # Recent alerts or notifications
        st.subheader("🔔 Recent Alerts")
        
        if not cognitive_initialized:
            st.warning("Cognitive system offline")
        
        if not os.getenv('GCP_PROJECT_ID'):
            st.error("GCP not configured")
        
        if not os.getenv('OPENAI_API_KEY'):
            st.error("OpenAI API not set")

def render_analytics_page():
    """Render the analytics page"""
    st.markdown('<h1 class="main-header">📈 Analytics Dashboard</h1>', unsafe_allow_html=True)
    
    st.info("📊 **Analytics Dashboard** - Coming Soon!")
    st.markdown("""
    This section will include:
    - 📈 Performance analytics
    - 📊 Trading statistics
    - 🎯 Strategy performance
    - 📉 Risk metrics
    - 🔍 Historical analysis
    """)
    
    # Placeholder metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Trades", "1,234", "+12%")
    
    with col2:
        st.metric("Win Rate", "67.8%", "+2.1%")
    
    with col3:
        st.metric("Total P&L", "$12,345", "+$1,234")

def main():
    """Main application function"""
    try:
        # Initialize data providers
        if 'system_data' not in st.session_state:
            st.session_state.system_data = SystemDataProvider()
        
        if 'cognitive_data' not in st.session_state:
            st.session_state.cognitive_data = CognitiveDataProvider()
        
        # Render sidebar and get selected page
        selected_page = render_sidebar()
        
        # Render the selected page
        if selected_page == "overview":
            render_overview_page()
        
        elif selected_page == "trades":
            trades_page = LiveTradesPage(st.session_state.system_data)
            trades_page.render()
        
        elif selected_page == "cognitive":
            cognitive_page = CognitiveInsightsPage(st.session_state.cognitive_data)
            cognitive_page.render()
        
        elif selected_page == "health":
            health_page = SystemHealthPage(st.session_state.system_data)
            health_page.render()
        
        elif selected_page == "analytics":
            render_analytics_page()
        
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