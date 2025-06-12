import streamlit as st
from pathlib import Path
import sys

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.trade_data_provider import TradeDataProvider

st.set_page_config(layout="wide")

st.title("💹 Live Trades")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=10)
def get_live_data():
    provider = TradeDataProvider()
    return {
        "positions": provider.get_live_positions(),
        "events": provider.get_trade_events_timeline()
    }

data = get_live_data()

# --- Filters and Actions ---
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    st.selectbox("Filter by Strategy", options=["All"] + ["Strategy A", "Strategy B"]) # Mock
with col2:
    st.selectbox("Filter by Symbol", options=["All"] + ["NIFTY", "BANKNIFTY"]) # Mock
with col3:
    if st.button("🚨 CLOSE ALL POSITIONS", use_container_width=True):
        st.toast("Close all positions command sent!")


st.markdown("<hr/>", unsafe_allow_html=True)

# --- Live Positions Table ---
st.subheader("Open Positions")
positions_data = data.get('positions', [])
if positions_data:
    st.dataframe(positions_data, height=400)
else:
    st.info("No live positions to display.")


# --- Trade Events Timeline ---
st.subheader("Recent Trade Events")
events_data = data.get('events', [])
if events_data:
    st.dataframe(events_data, height=300)
else:
    st.info("No recent trade events.")
