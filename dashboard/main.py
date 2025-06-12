#!/usr/bin/env python3
"""
Tron Trading Dashboard - Main Application (Redesigned)
"""

import streamlit as st
import sys
from pathlib import Path

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.data.system_data_provider import SystemDataProvider
from dashboard.data.cognitive_data_provider import CognitiveDataProvider
from dashboard.data.trade_data_provider import TradeDataProvider
from dashboard.components.overview import render_overview_page

st.set_page_config(
    page_title="MarketPulse by Tron",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    st.markdown("""
    <style>
        /* --- Base Layout & Theme --- */
        #root > div:nth-child(1) > div > div > div > div > section[data-testid="stSidebar"] {
            background-color: #1E293B; /* Dark blue-gray */
        }
        .stApp {
            background-color: #F0F2F6;
        }
        .main .block-container {
            padding: 2rem;
            max-width: 100%;
        }

        /* --- Custom Components --- */
        .top-nav {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 2rem;
        }
        .top-nav .brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: #1E293B;
        }
        h1 {
            font-weight: bold;
            color: #1E293B;
        }
    </style>
    """, unsafe_allow_html=True)

load_css()

# --- Data Caching ---
@st.cache_data(ttl=30)
def get_system_data():
    provider = SystemDataProvider()
    return {"health": provider.get_system_health(), "metrics": provider.get_system_metrics()}

@st.cache_data(ttl=60)
def get_cognitive_data():
    provider = CognitiveDataProvider()
    return provider.get_cognitive_summary()

@st.cache_data(ttl=30)
def get_trade_data():
    provider = TradeDataProvider()
    return {"summary": provider.get_daily_summary(), "positions": provider.get_live_positions()}

# --- Sidebar ---
with st.sidebar:
    st.markdown("<h1>TradingAI</h1>", unsafe_allow_html=True)
    st.page_link("main.py", label="Dashboard", icon="🏠")
    st.markdown("---")
    st.markdown("### Analytics Hub")
    st.page_link("pages/1_pnl_analysis.py", label="P&L Analysis", icon="📈")
    st.page_link("pages/2_risk_monitor.py", label="Risk Monitor", icon="⚠️")
    st.page_link("pages/3_strategy_performance.py", label="Strategy Performance", icon="🎯")
    st.markdown("---")
    st.markdown("### System Tools")
    st.page_link("pages/4_live_trades.py", label="Live Trades", icon="💹")
    st.page_link("pages/5_cognitive_insights.py", label="Cognitive Insights", icon="🧠")
    st.page_link("pages/6_system_health.py", label="System Health", icon="⚙️")
    st.markdown("---")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# --- Header ---
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<div class="brand">MarketPulse</div>', unsafe_allow_html=True)
with col2:
    st.text_input("Search stocks...", label_visibility="collapsed", placeholder="Search stocks, indices...")

# --- Main Content ---
st.title("Trading System Dashboard")
st.markdown("<hr/>", unsafe_allow_html=True)

# For now, we only render the main overview page.
# I will create the other pages next.
render_overview_page(get_system_data, get_cognitive_data, get_trade_data)