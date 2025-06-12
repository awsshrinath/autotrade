import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.trade_data_provider import TradeDataProvider

st.set_page_config(layout="wide")

st.title("🎯 Strategy Performance")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=60)
def get_strategy_data():
    provider = TradeDataProvider()
    return provider.get_strategy_performance_summary()

data = get_strategy_data()

if not data:
    st.info("No strategy performance data available.")
    st.stop()

df = pd.DataFrame(data)

# --- Performance Table ---
st.subheader("Performance by Strategy")
st.dataframe(
    df,
    column_config={
        "name": "Strategy",
        "total_trades": "Total Trades",
        "win_rate": st.column_config.ProgressColumn("Win Rate", format="%.1f%%", min_value=0, max_value=100),
        "pnl": st.column_config.NumberColumn("Total P&L", format="$%.2f")
    },
    hide_index=True,
)

st.markdown("<hr/>", unsafe_allow_html=True)

# --- P&L by Strategy Chart ---
st.subheader("P&L by Strategy")
pnl_chart_data = df[['name', 'pnl']].set_index('name')
st.bar_chart(pnl_chart_data)
