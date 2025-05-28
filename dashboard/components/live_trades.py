"""
Live Trades Page Component
Real-time monitoring of active trades and positions
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any


class LiveTradesPage:
    """Live trades page component for real-time trade monitoring"""
    
    def __init__(self, trade_data_provider):
        self.trade_data = trade_data_provider
    
    def render(self):
        """Render the live trades page"""
        st.title("📊 Live Trading Monitor")
        
        # Control panel
        self._render_control_panel()
        
        # Live positions overview
        self._render_positions_overview()
        
        # Active trades table
        self._render_active_trades_table()
        
        # Trade actions panel
        self._render_trade_actions()
        
        # Real-time charts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_position_pnl_chart()
        
        with col2:
            self._render_trade_timeline()
        
        # Risk metrics
        self._render_risk_metrics()
    
    def _render_control_panel(self):
        """Render control panel with filters and actions"""
        st.subheader("⚙️ Control Panel")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Auto-refresh toggle
            auto_refresh = st.toggle("🔄 Auto Refresh", value=True, key="live_auto_refresh")
            
        with col2:
            # Filter by strategy
            strategies = self.trade_data.get_active_strategies()
            selected_strategy = st.selectbox(
                "Filter by Strategy",
                ["All"] + strategies,
                key="strategy_filter"
            )
        
        with col3:
            # Filter by symbol
            symbols = self.trade_data.get_active_symbols()
            selected_symbol = st.selectbox(
                "Filter by Symbol",
                ["All"] + symbols,
                key="symbol_filter"
            )
        
        with col4:
            # Emergency actions
            if st.button("🚨 Close All Positions", type="secondary"):
                self._handle_close_all_positions()
        
        # Store filters in session state
        st.session_state.strategy_filter = selected_strategy
        st.session_state.symbol_filter = selected_symbol
    
    def _render_positions_overview(self):
        """Render positions overview cards"""
        st.subheader("📈 Positions Overview")
        
        # Get positions summary
        summary = self.trade_data.get_positions_summary()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_positions = summary.get('total_positions', 0)
            st.metric("📊 Total Positions", total_positions)
        
        with col2:
            unrealized_pnl = summary.get('unrealized_pnl', 0)
            pnl_color = "green" if unrealized_pnl >= 0 else "red"
            st.metric(
                "💰 Unrealized P&L",
                f"₹{unrealized_pnl:,.2f}",
                delta_color="normal"
            )
        
        with col3:
            total_exposure = summary.get('total_exposure', 0)
            st.metric("💼 Total Exposure", f"₹{total_exposure:,.0f}")
        
        with col4:
            margin_used = summary.get('margin_used', 0)
            margin_pct = summary.get('margin_utilization_pct', 0)
            st.metric(
                "📋 Margin Used",
                f"₹{margin_used:,.0f}",
                f"{margin_pct:.1f}%"
            )
        
        with col5:
            avg_duration = summary.get('avg_duration_minutes', 0)
            st.metric("⏱️ Avg Duration", f"{avg_duration:.0f} min")
    
    def _render_active_trades_table(self):
        """Render detailed active trades table"""
        st.subheader("🔴 Active Trades")
        
        # Get active trades with filters
        filters = {
            'strategy': st.session_state.get('strategy_filter', 'All'),
            'symbol': st.session_state.get('symbol_filter', 'All')
        }
        
        active_trades = self.trade_data.get_active_trades(filters=filters)
        
        if active_trades:
            df = pd.DataFrame(active_trades)
            
            # Add action buttons column
            df['Actions'] = df.apply(lambda row: self._create_action_buttons(row), axis=1)
            
            # Format columns for display
            display_columns = [
                'symbol', 'strategy', 'direction', 'entry_price', 'current_price',
                'quantity', 'stop_loss', 'target', 'unrealized_pnl', 'duration',
                'confidence', 'Actions'
            ]
            
            display_df = df[display_columns].copy()
            
            # Format numeric columns
            display_df['entry_price'] = display_df['entry_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['current_price'] = display_df['current_price'].apply(lambda x: f"₹{x:,.2f}")
            display_df['stop_loss'] = display_df['stop_loss'].apply(lambda x: f"₹{x:,.2f}")
            display_df['target'] = display_df['target'].apply(lambda x: f"₹{x:,.2f}")
            display_df['unrealized_pnl'] = display_df['unrealized_pnl'].apply(
                lambda x: f"₹{x:,.2f}" if x >= 0 else f"-₹{abs(x):,.2f}"
            )
            
            # Rename columns
            display_df.columns = [
                'Symbol', 'Strategy', 'Direction', 'Entry', 'Current',
                'Qty', 'Stop Loss', 'Target', 'P&L', 'Duration', 'Confidence', 'Actions'
            ]
            
            # Style the dataframe
            def style_pnl(val):
                if '₹' in str(val):
                    if val.startswith('-'):
                        return 'background-color: #ffebee; color: red'
                    else:
                        return 'background-color: #e8f5e8; color: green'
                return ''
            
            def style_direction(val):
                if val == 'bullish':
                    return 'color: green; font-weight: bold'
                elif val == 'bearish':
                    return 'color: red; font-weight: bold'
                return ''
            
            styled_df = display_df.style.applymap(style_pnl, subset=['P&L']).applymap(style_direction, subset=['Direction'])
            
            # Display with custom height
            st.dataframe(styled_df, use_container_width=True, hide_index=True, height=400)
            
            # Trade details expander
            with st.expander("📋 Trade Details"):
                selected_trade = st.selectbox(
                    "Select trade for details",
                    options=df['symbol'].tolist(),
                    format_func=lambda x: f"{x} - {df[df['symbol']==x]['strategy'].iloc[0]}"
                )
                
                if selected_trade:
                    trade_details = df[df['symbol'] == selected_trade].iloc[0]
                    self._render_trade_details(trade_details)
        else:
            st.info("No active trades found")
    
    def _create_action_buttons(self, trade_row):
        """Create action buttons for each trade"""
        trade_id = trade_row['id']
        symbol = trade_row['symbol']
        
        # Create unique keys for buttons
        close_key = f"close_{trade_id}"
        modify_key = f"modify_{trade_id}"
        
        # Return button HTML (simplified for display)
        return f"Close | Modify"
    
    def _render_trade_actions(self):
        """Render trade action panel"""
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🎯 Move All to Breakeven", use_container_width=True):
                self._handle_move_to_breakeven()
        
        with col2:
            if st.button("📈 Trail Stop Loss", use_container_width=True):
                self._handle_trail_stop_loss()
        
        with col3:
            if st.button("💰 Partial Exit (50%)", use_container_width=True):
                self._handle_partial_exit()
        
        with col4:
            if st.button("🔄 Refresh Prices", use_container_width=True):
                self._handle_refresh_prices()
    
    def _render_position_pnl_chart(self):
        """Render real-time P&L chart for positions"""
        st.subheader("📈 Position P&L Trend")
        
        # Get P&L timeline data
        pnl_timeline = self.trade_data.get_position_pnl_timeline()
        
        if pnl_timeline:
            df = pd.DataFrame(pnl_timeline)
            
            fig = go.Figure()
            
            # Add traces for each position
            for symbol in df['symbol'].unique():
                symbol_data = df[df['symbol'] == symbol]
                
                fig.add_trace(go.Scatter(
                    x=symbol_data['timestamp'],
                    y=symbol_data['pnl'],
                    mode='lines+markers',
                    name=symbol,
                    line=dict(width=2),
                    marker=dict(size=4),
                    hovertemplate=f'<b>{symbol}</b><br>Time: %{{x}}<br>P&L: ₹%{{y:,.2f}}<extra></extra>'
                ))
            
            # Add zero line
            fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig.update_layout(
                title="Real-time Position P&L",
                xaxis_title="Time",
                yaxis_title="P&L (₹)",
                height=300,
                legend=dict(orientation="h", yanchor="bottom", y=-0.3),
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No P&L timeline data available")
    
    def _render_trade_timeline(self):
        """Render trade execution timeline"""
        st.subheader("⏰ Trade Timeline")
        
        # Get recent trade events
        trade_events = self.trade_data.get_trade_events_timeline()
        
        if trade_events:
            # Create timeline visualization
            df = pd.DataFrame(trade_events)
            
            fig = px.scatter(
                df,
                x='timestamp',
                y='symbol',
                color='event_type',
                size='impact_score',
                hover_data=['description', 'pnl_impact'],
                title="Recent Trade Events"
            )
            
            fig.update_layout(
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No recent trade events")
    
    def _render_risk_metrics(self):
        """Render real-time risk metrics"""
        st.subheader("🛡️ Risk Metrics")
        
        # Get risk data
        risk_data = self.trade_data.get_real_time_risk_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            var_1d = risk_data.get('var_1d', 0)
            st.metric("📊 VaR (1D)", f"₹{var_1d:,.0f}")
        
        with col2:
            max_drawdown = risk_data.get('max_drawdown_pct', 0)
            st.metric("📉 Max Drawdown", f"{max_drawdown:.2f}%")
        
        with col3:
            correlation_risk = risk_data.get('correlation_risk', 0)
            st.metric("🔗 Correlation Risk", f"{correlation_risk:.2f}")
        
        with col4:
            concentration_risk = risk_data.get('concentration_risk_pct', 0)
            st.metric("🎯 Concentration", f"{concentration_risk:.1f}%")
        
        # Risk alerts
        risk_alerts = risk_data.get('alerts', [])
        if risk_alerts:
            st.warning("⚠️ Risk Alerts:")
            for alert in risk_alerts:
                st.write(f"• {alert}")
    
    def _render_trade_details(self, trade):
        """Render detailed information for a specific trade"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Trade Information:**")
            st.write(f"• Symbol: {trade['symbol']}")
            st.write(f"• Strategy: {trade['strategy']}")
            st.write(f"• Direction: {trade['direction']}")
            st.write(f"• Entry Time: {trade['entry_time']}")
            st.write(f"• Quantity: {trade['quantity']}")
            
        with col2:
            st.write("**Price Levels:**")
            st.write(f"• Entry Price: ₹{trade['entry_price']:,.2f}")
            st.write(f"• Current Price: ₹{trade['current_price']:,.2f}")
            st.write(f"• Stop Loss: ₹{trade['stop_loss']:,.2f}")
            st.write(f"• Target: ₹{trade['target']:,.2f}")
            st.write(f"• Unrealized P&L: ₹{trade['unrealized_pnl']:,.2f}")
    
    def _handle_close_all_positions(self):
        """Handle close all positions action"""
        if st.session_state.get('confirm_close_all', False):
            # Execute close all
            result = self.trade_data.close_all_positions()
            if result['success']:
                st.success(f"✅ Closed {result['closed_count']} positions")
            else:
                st.error(f"❌ Failed to close positions: {result['error']}")
            st.session_state.confirm_close_all = False
        else:
            st.warning("⚠️ This will close ALL active positions. Click again to confirm.")
            st.session_state.confirm_close_all = True
    
    def _handle_move_to_breakeven(self):
        """Handle move all positions to breakeven"""
        result = self.trade_data.move_all_to_breakeven()
        if result['success']:
            st.success(f"✅ Moved {result['updated_count']} positions to breakeven")
        else:
            st.error(f"❌ Failed to update positions: {result['error']}")
    
    def _handle_trail_stop_loss(self):
        """Handle trailing stop loss activation"""
        result = self.trade_data.activate_trailing_stop()
        if result['success']:
            st.success(f"✅ Activated trailing stop for {result['updated_count']} positions")
        else:
            st.error(f"❌ Failed to activate trailing stop: {result['error']}")
    
    def _handle_partial_exit(self):
        """Handle partial exit of positions"""
        result = self.trade_data.partial_exit_all(exit_percentage=50)
        if result['success']:
            st.success(f"✅ Partial exit completed for {result['updated_count']} positions")
        else:
            st.error(f"❌ Failed to execute partial exit: {result['error']}")
    
    def _handle_refresh_prices(self):
        """Handle manual price refresh"""
        result = self.trade_data.refresh_all_prices()
        if result['success']:
            st.success("✅ Prices refreshed successfully")
            st.rerun()
        else:
            st.error(f"❌ Failed to refresh prices: {result['error']}") 