import streamlit as st
import pandas as pd
from utils.log_api_client import LogApiClient

st.set_page_config(
    page_title="Portfolio Overview",
    page_icon="💼",
    layout="wide"
)

st.title("💼 Portfolio Overview")

@st.cache_data(ttl=60) # Cache data for 60 seconds
def get_portfolio_data():
    """Fetches portfolio data from the API."""
    client = LogApiClient()
    try:
        portfolio_data = client.get_portfolio_overview()
        return portfolio_data
    except Exception as e:
        st.error(f"Failed to fetch portfolio data: {e}")
        return None

portfolio = get_portfolio_data()

if portfolio:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Portfolio Value", f"${portfolio['total_value']:,.2f}")
    col2.metric("Cash Balance", f"${portfolio['cash_balance']:,.2f}")
    
    pnl = portfolio['performance']['total_pnl']
    pnl_color = "normal" if pnl == 0 else ("inverse" if pnl < 0 else "normal")
    col3.metric("Total P&L", f"${pnl:,.2f}", delta_color=pnl_color)

    st.subheader("Open Positions")
    
    positions = portfolio.get('positions', {})
    if not positions:
        st.info("No open positions.")
    else:
        # Filter for open positions and convert to a list of dicts
        open_positions = [pos for pos_id, pos in positions.items() if pos['status'] == 'OPEN']
        
        if not open_positions:
            st.info("No open positions.")
        else:
            df = pd.DataFrame(open_positions)
            # Format and select columns for display
            df_display = df[['symbol', 'asset_class', 'quantity', 'entry_price', 'current_price', 'pnl']]
            df_display['pnl'] = df_display['pnl'].map('${:,.2f}'.format)
            df_display['entry_price'] = df_display['entry_price'].map('${:,.2f}'.format)
            df_display['current_price'] = df_display['current_price'].map('${:,.2f}'.format)
            
            st.dataframe(df_display, use_container_width=True)

else:
    st.warning("Could not load portfolio data. The backend service may be unavailable.") 