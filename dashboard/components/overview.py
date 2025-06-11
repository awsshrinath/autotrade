"""
Overview Page Component
Main dashboard overview with key metrics and summaries
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any


def render_overview_page(get_system_data, get_cognitive_data, get_trade_data):
    """
    Renders the main overview page with the new card-based design.
    """
    
    # --- Load Data ---
    system_data = get_system_data()
    cognitive_data = get_cognitive_data()
    trade_data = get_trade_data()

    # --- Header Cards ---
    col1, col2, col3 = st.columns(3)

    with col1:
        with st.container(border=True):
            st.markdown("<h6>System Status</h6>", unsafe_allow_html=True)
            status = system_data.get('health', {}).get('status', 'Unknown').capitalize()
            st.markdown(f"## {status}")
            # Add sub-details later

    with col2:
        with st.container(border=True):
            st.markdown("<h6>Cognitive AI Status</h6>", unsafe_allow_html=True)
            mode = cognitive_data.get('system_status', {}).get('mode', 'Unknown').capitalize()
            st.markdown(f"## {mode}")
            # Add sub-details later

    with col3:
        with st.container(border=True):
            st.markdown("<h6>System Health</h6>", unsafe_allow_html=True)
            health = system_data.get('health', {})
            status = health.get('status', 'Unknown').capitalize()
            st.markdown(f"## {status}")
            # Add sub-details later

    # --- Metric Cards ---
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        with st.container(border=True):
            st.markdown("<h6>AI Thoughts</h6>", unsafe_allow_html=True)
            thoughts = cognitive_data.get('thought_summary', {}).get('total_thoughts', 0)
            st.markdown(f"## {thoughts}")
            
    with col2:
        with st.container(border=True):
            st.markdown("<h6>AI Memories</h6>", unsafe_allow_html=True)
            memories = cognitive_data.get('memory_summary', {}).get('total_memories', 0)
            st.markdown(f"## {memories}")

    with col3:
        with st.container(border=True):
            st.markdown("<h6>System Uptime</h6>", unsafe_allow_html=True)
            uptime = system_data.get('health', {}).get('uptime_hours', 0)
            st.markdown(f"## {uptime:.2f} hrs")
            
    with col4:
        with st.container(border=True):
            st.markdown("<h6>Processing Speed</h6>", unsafe_allow_html=True)
            speed = system_data.get('metrics', {}).get('api_response_time_ms', 247) # Mock
            st.markdown(f"## {speed} ms")


    st.markdown("### Analytics Hub Overview")
    st.markdown("<hr/>", unsafe_allow_html=True)

    # --- Analytics Hub Cards ---
    col1, col2, col3 = st.columns(3)
    summary = trade_data.get('summary', {})

    with col1:
        with st.container(border=True):
            st.markdown("<h6>Daily P&L</h6>", unsafe_allow_html=True)
            pnl = summary.get('total_pnl', 0)
            st.markdown(f"## ${pnl:,.2f}")

    with col2:
        with st.container(border=True):
            st.markdown("<h6>Win Rate</h6>", unsafe_allow_html=True)
            win_rate = summary.get('win_rate', 0)
            st.markdown(f"## {win_rate:.1f}%")

    with col3:
        with st.container(border=True):
            st.markdown("<h6>Max Drawdown</h6>", unsafe_allow_html=True)
            drawdown = summary.get('max_drawdown', 3241) # Mock
            st.markdown(f"## ${drawdown:,.2f}")
            
    # --- Quick Actions (Placeholder) ---
    st.markdown("### Quick Actions")
    st.markdown("<hr/>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("Quick actions will be implemented next.")


class OverviewPage:
    """Overview page component for the trading dashboard"""
    
    def __init__(self, trade_data_provider, system_data_provider):
        self.trade_data = trade_data_provider
        self.system_data = system_data_provider
    
    def render(self):
        """Render the overview page"""
        st.title("🏠 Trading System Overview")
        
        # Key metrics cards
        self._render_key_metrics()
        
        # Charts row
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_pnl_chart()
        
        with col2:
            self._render_portfolio_allocation()
        
        # Live positions and recent trades
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_live_positions()
        
        with col2:
            self._render_recent_trades()
        
        # Strategy performance summary
        self._render_strategy_summary()
        
        # Market overview
        self._render_market_overview()
    
    def _render_key_metrics(self):
        """Render key performance metrics"""
        st.subheader("📊 Key Metrics")
        
        # Get data
        summary = self.trade_data.get_daily_summary()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            pnl = summary.get('total_pnl', 0)
            pnl_change = summary.get('pnl_change_pct', 0)
            st.metric(
                "💰 Today's P&L",
                f"₹{pnl:,.2f}",
                f"{pnl_change:+.1f}%",
                delta_color="normal"
            )
        
        with col2:
            active_trades = summary.get('active_trades', 0)
            trades_change = summary.get('trades_change', 0)
            st.metric(
                "📈 Active Trades",
                active_trades,
                f"{trades_change:+d}"
            )
        
        with col3:
            win_rate = summary.get('win_rate', 0)
            win_rate_change = summary.get('win_rate_change', 0)
            st.metric(
                "🎯 Win Rate",
                f"{win_rate:.1f}%",
                f"{win_rate_change:+.1f}%"
            )
        
        with col4:
            total_trades = summary.get('total_trades', 0)
            st.metric(
                "📊 Total Trades",
                total_trades,
                f"Today"
            )
        
        with col5:
            avg_profit = summary.get('avg_profit_per_trade', 0)
            st.metric(
                "💵 Avg Profit/Trade",
                f"₹{avg_profit:,.0f}",
                f"Per trade"
            )
        
        with col6:
            portfolio_value = summary.get('portfolio_value', 0)
            portfolio_change = summary.get('portfolio_change_pct', 0)
            st.metric(
                "💼 Portfolio Value",
                f"₹{portfolio_value:,.0f}",
                f"{portfolio_change:+.1f}%"
            )
    
    def _render_pnl_chart(self):
        """Render P&L trend chart"""
        st.subheader("📈 P&L Trend")
        
        # Get P&L data
        pnl_data = self.trade_data.get_pnl_timeline()
        
        if pnl_data:
            df = pd.DataFrame(pnl_data)
            
            # Create line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['cumulative_pnl'],
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color='#1f77b4', width=2),
                marker=dict(size=4),
                hovertemplate='<b>%{x}</b><br>P&L: ₹%{y:,.2f}<extra></extra>'
            ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig.update_layout(
                title="Cumulative P&L Today",
                xaxis_title="Time",
                yaxis_title="P&L (₹)",
                height=300,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No P&L data available for today")
    
    def _render_portfolio_allocation(self):
        """Render portfolio allocation pie chart"""
        st.subheader("🥧 Portfolio Allocation")
        
        # Get allocation data
        allocation_data = self.trade_data.get_portfolio_allocation()
        
        if allocation_data:
            df = pd.DataFrame(allocation_data)
            
            fig = px.pie(
                df,
                values='value',
                names='category',
                title="Current Allocation",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Value: ₹%{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No allocation data available")
    
    def _render_live_positions(self):
        """Render live positions table"""
        st.subheader("🔴 Live Positions")
        
        # Get live positions
        positions = self.trade_data.get_live_positions()
        
        if positions:
            df = pd.DataFrame(positions)
            
            # Format the dataframe for display
            display_df = df[['symbol', 'strategy', 'entry_price', 'current_price', 'quantity', 'unrealized_pnl', 'duration']].copy()
            
            # Format columns
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['unrealized_pnl'] = display_df['unrealized_pnl'].apply(
                lambda x: f"₹{x:,.2f}" if x >= 0 else f"-₹{abs(x):,.2f}"
            )
            
            # Rename columns for display
            display_df.columns = ['Symbol', 'Strategy', 'Entry', 'Current', 'Qty', 'P&L', 'Duration']
            
            # Style the dataframe
            def style_pnl(val):
                if '₹' in str(val):
                    if val.startswith('-'):
                        return 'color: red'
                    else:
                        return 'color: green'
                return ''
            
            styled_df = display_df.style.applymap(style_pnl, subset=['P&L'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("No active positions")
    
    def _render_recent_trades(self):
        """Render recent completed trades"""
        st.subheader("📋 Recent Trades")
        
        # Get recent trades
        recent_trades = self.trade_data.get_recent_trades(limit=10)
        
        if recent_trades:
            df = pd.DataFrame(recent_trades)
            
            # Format for display
            display_df = df[['symbol', 'strategy', 'entry_price', 'exit_price', 'pnl', 'status', 'exit_time']].copy()
            
            # Format columns
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['exit_price'] = display_df['exit_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['pnl'] = display_df['pnl'].apply(
                lambda x: f"₹{x:,.2f}" if x >= 0 else f"-₹{abs(x):,.2f}"
            )
            display_df['exit_time'] = pd.to_datetime(display_df['exit_time']).dt.strftime('%H:%M')
            
            # Rename columns
            display_df.columns = ['Symbol', 'Strategy', 'Entry', 'Exit', 'P&L', 'Status', 'Time']
            
            # Style the dataframe
            def style_pnl(val):
                if '₹' in str(val):
                    if val.startswith('-'):
                        return 'color: red'
                    else:
                        return 'color: green'
                return ''
            
            def style_status(val):
                if val == 'target_hit':
                    return 'color: green'
                elif val == 'stop_loss_hit':
                    return 'color: red'
                else:
                    return 'color: orange'
            
            styled_df = display_df.style.applymap(style_pnl, subset=['P&L']).applymap(style_status, subset=['Status'])
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
        else:
            st.info("No recent trades")
    
    def _render_strategy_summary(self):
        """Render strategy performance summary"""
        st.subheader("🎯 Strategy Performance Summary")
        
        # Get strategy performance data
        strategy_data = self.trade_data.get_strategy_performance_summary()
        
        if strategy_data:
            col1, col2, col3 = st.columns(3)
            
            for i, strategy in enumerate(strategy_data):
                with [col1, col2, col3][i % 3]:
                    with st.container():
                        st.markdown(f"""
                        <div class="metric-card">
                            <h4>{strategy['name']}</h4>
                            <p><strong>P&L:</strong> ₹{strategy['pnl']:,.2f}</p>
                            <p><strong>Win Rate:</strong> {strategy['win_rate']:.1f}%</p>
                            <p><strong>Trades:</strong> {strategy['total_trades']}</p>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            st.info("No strategy performance data available")
    
    def _render_market_overview(self):
        """Render market overview section"""
        st.subheader("🌍 Market Overview")
        
        # Get market data
        market_data = self.system_data.get_market_overview()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            nifty_data = market_data.get('nifty', {})
            st.metric(
                "NIFTY 50",
                f"{nifty_data.get('price', 0):,.0f}",
                f"{nifty_data.get('change_pct', 0):+.2f}%"
            )
        
        with col2:
            banknifty_data = market_data.get('banknifty', {})
            st.metric(
                "BANK NIFTY",
                f"{banknifty_data.get('price', 0):,.0f}",
                f"{banknifty_data.get('change_pct', 0):+.2f}%"
            )
        
        with col3:
            vix_data = market_data.get('vix', {})
            st.metric(
                "VIX",
                f"{vix_data.get('price', 0):.2f}",
                f"{vix_data.get('change_pct', 0):+.2f}%"
            )
        
        with col4:
            sentiment = market_data.get('sentiment', 'Neutral')
            sentiment_color = "green" if sentiment == "Bullish" else "red" if sentiment == "Bearish" else "orange"
            st.markdown(f"""
            <div style="text-align: center;">
                <h3>Market Sentiment</h3>
                <h2 style="color: {sentiment_color};">{sentiment}</h2>
            </div>
            """, unsafe_allow_html=True) 