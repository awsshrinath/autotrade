import streamlit as st
from pathlib import Path
import sys

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.trade_data_provider import TradeDataProvider

st.set_page_config(layout="wide")

st.title("📈 P&L Analysis")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=30)
def get_pnl_data():
    provider = TradeDataProvider()
    return {
        "summary": provider.get_daily_summary(),
        "timeline": provider.get_pnl_timeline(),
        "recent_trades": provider.get_recent_trades(limit=50)
    }

data = get_pnl_data()
summary = data.get('summary', {})

# --- Summary Metrics ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total P&L", f"${summary.get('total_pnl', 0):,.2f}")
with col2:
    st.metric("Total Trades", summary.get('total_trades', 0))
with col3:
    st.metric("Win Rate", f"{summary.get('win_rate', 0):.1f}%")
with col4:
    st.metric("Avg. Profit/Trade", f"${summary.get('avg_profit_per_trade', 0):,.2f}")

st.markdown("<hr/>", unsafe_allow_html=True)

# --- P&L Timeline Chart ---
st.subheader("P&L Timeline")
timeline_data = data.get('timeline', [])
if timeline_data:
    # Convert to DataFrame for charting
    import pandas as pd
    df = pd.DataFrame(timeline_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    st.line_chart(df.set_index('timestamp')['cumulative_pnl'])
else:
    st.info("No timeline data available to display.")


# --- Recent Trades Table ---
st.subheader("Recent Completed Trades")
trades_data = data.get('recent_trades', [])
if trades_data:
    st.dataframe(trades_data, height=400)
else:
    st.info("No recent trades to display.")
