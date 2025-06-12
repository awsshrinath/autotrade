import streamlit as st
from pathlib import Path
import sys

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.trade_data_provider import TradeDataProvider

st.set_page_config(layout="wide")

st.title("⚠️ Risk Monitor")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=30)
def get_risk_data():
    provider = TradeDataProvider()
    return {
        "positions": provider.get_live_positions(),
        "summary": provider.get_positions_summary(),
        "risk_metrics": provider.get_real_time_risk_metrics()
    }

data = get_risk_data()
summary = data.get('summary', {})
risk_metrics = data.get('risk_metrics', {})

# --- Summary Metrics ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Exposure", f"${summary.get('total_exposure', 0):,.2f}")
with col2:
    st.metric("Unrealized P&L", f"${summary.get('unrealized_pnl', 0):,.2f}")
with col3:
    st.metric("Value at Risk (VaR)", f"${risk_metrics.get('var_1d', 0):,.2f}")
with col4:
    st.metric("Max Drawdown", f"{risk_metrics.get('max_drawdown_pct', 0):.2f}%")

st.markdown("<hr/>", unsafe_allow_html=True)

# --- Live Positions Table ---
st.subheader("Live Positions")
positions_data = data.get('positions', [])
if positions_data:
    st.dataframe(positions_data, height=400)
else:
    st.info("No live positions to display.")

# --- Additional Risk Metrics (Placeholder) ---
st.subheader("Portfolio Risk Analysis")
col1, col2 = st.columns(2)
with col1:
    with st.container():
        st.markdown("<h6>Correlation Matrix</h6>", unsafe_allow_html=True)
        st.info("Correlation matrix will be displayed here.")

with col2:
    with st.container():
        st.markdown("<h6>Concentration Risk</h6>", unsafe_allow_html=True)
        st.info("Concentration risk analysis will be displayed here.")
