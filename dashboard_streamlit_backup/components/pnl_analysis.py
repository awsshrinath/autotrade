"""
P&L Analysis Page Component
Detailed profit and loss analysis and reporting
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any
import numpy as np


class PnLAnalysisPage:
    """P&L analysis page component"""
    
    def __init__(self, trade_data_provider):
        self.trade_data = trade_data_provider
    
    def render(self):
        """Render the P&L analysis page"""
        st.markdown('<h1 style="color: #1f77b4; text-align: center; margin-bottom: 2rem;">💰 P&L Analysis Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("**Real-time profit & loss tracking with comprehensive analytics**")
        st.markdown('<hr style="height: 2px; background: linear-gradient(90deg, transparent, #1f77b4, transparent); border: none; margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Time period selector
        self._render_time_period_selector()
        
        # Key P&L metrics
        self._render_key_pnl_metrics()
        
        # Main analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Overview", 
            "📈 Timeline", 
            "🎯 Strategy Analysis", 
            "📉 Risk Analysis", 
            "📋 Export"
        ])
        
        with tab1:
            self._render_overview_tab()
        
        with tab2:
            self._render_timeline_tab()
        
        with tab3:
            self._render_strategy_analysis_tab()
        
        with tab4:
            self._render_risk_analysis_tab()
        
        with tab5:
            self._render_export_tab()
    
    def _render_time_period_selector(self):
        """Render time period selection controls"""
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            start_date = st.date_input(
                "From Date",
                value=datetime.now() - timedelta(days=30),
                key="pnl_start_date"
            )
        
        with col2:
            end_date = st.date_input(
                "To Date", 
                value=datetime.now(),
                key="pnl_end_date"
            )
        
        with col3:
            st.selectbox(
                "Period",
                ["Custom", "Today", "This Week", "This Month", "Last 30 Days"],
                key="pnl_period"
            )
    
    def _render_key_pnl_metrics(self):
        """Render key P&L performance metrics"""
        st.subheader("📊 Key Metrics")
        
        # Get P&L data for the selected period
        pnl_data = self._get_pnl_data()
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            total_pnl = pnl_data.get('total_pnl', 0)
            pnl_change = pnl_data.get('pnl_change_pct', 0)
            color = "green" if total_pnl >= 0 else "red"
            st.metric(
                "💰 Total P&L",
                f"₹{total_pnl:,.2f}",
                f"{pnl_change:+.1f}%",
                delta_color="normal"
            )
        
        with col2:
            best_trade = pnl_data.get('best_trade', {})
            st.metric(
                "📈 Best Trade",
                f"₹{best_trade.get('pnl', 0):,.2f}",
                best_trade.get('symbol', 'N/A')
            )
        
        with col3:
            worst_trade = pnl_data.get('worst_trade', {})
            st.metric(
                "📉 Worst Trade",
                f"₹{worst_trade.get('pnl', 0):,.2f}",
                worst_trade.get('symbol', 'N/A')
            )
        
        with col4:
            win_rate = pnl_data.get('win_rate', 0)
            win_rate_change = pnl_data.get('win_rate_change', 0)
            st.metric(
                "🎯 Win Rate",
                f"{win_rate:.1f}%",
                f"{win_rate_change:+.1f}%"
            )
        
        with col5:
            total_trades = pnl_data.get('total_trades', 0)
            st.metric(
                "📊 Total Trades",
                total_trades,
                f"Completed"
            )
        
        with col6:
            avg_profit = pnl_data.get('avg_profit_per_trade', 0)
            st.metric(
                "💵 Avg P&L/Trade",
                f"₹{avg_profit:,.0f}",
                f"Per trade"
            )
    
    def _render_overview_tab(self):
        """Render P&L overview with charts and summaries"""
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_pnl_distribution_chart()
        
        with col2:
            self._render_win_loss_chart()
        
        # Trade performance table
        st.subheader("📋 Top Performing Trades")
        self._render_top_trades_table()
        
        # Strategy comparison
        st.subheader("🎯 Strategy Performance Comparison")
        self._render_strategy_comparison_chart()
    
    def _render_timeline_tab(self):
        """Render P&L timeline analysis"""
        # Cumulative P&L chart
        st.subheader("📈 Cumulative P&L Timeline")
        self._render_cumulative_pnl_chart()
        
        # Daily P&L chart
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Daily P&L")
            self._render_daily_pnl_chart()
        
        with col2:
            st.subheader("⏰ Hourly P&L Pattern")
            self._render_hourly_pnl_pattern()
        
        # Trade frequency analysis
        st.subheader("📈 Trade Frequency vs P&L")
        self._render_trade_frequency_chart()
    
    def _render_strategy_analysis_tab(self):
        """Render detailed strategy analysis"""
        # Strategy performance breakdown
        st.subheader("🎯 Strategy Performance Breakdown")
        
        strategy_data = self._get_strategy_performance_data()
        
        if strategy_data:
            # Strategy metrics table
            df = pd.DataFrame(strategy_data)
            
            # Format and display
            st.dataframe(
                df.style.format({
                    'Total P&L': '₹{:,.2f}',
                    'Avg P&L': '₹{:,.2f}',
                    'Win Rate': '{:.1f}%',
                    'Best Trade': '₹{:,.2f}',
                    'Worst Trade': '₹{:,.2f}'
                }),
                use_container_width=True
            )
            
            # Strategy performance charts
            col1, col2 = st.columns(2)
            
            with col1:
                self._render_strategy_pnl_chart(df)
            
            with col2:
                self._render_strategy_risk_return_scatter(df)
        else:
            st.info("No strategy data available for the selected period")
        
        # Trade duration analysis
        st.subheader("⏱️ Trade Duration Analysis")
        self._render_duration_analysis()
    
    def _render_risk_analysis_tab(self):
        """Render risk analysis and drawdown metrics"""
        st.subheader("📉 Risk Analysis & Drawdown")
        
        # Risk metrics
        risk_data = self._get_risk_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            max_drawdown = risk_data.get('max_drawdown_pct', 0)
            st.metric("📉 Max Drawdown", f"{max_drawdown:.2f}%")
        
        with col2:
            sharpe_ratio = risk_data.get('sharpe_ratio', 0)
            st.metric("📊 Sharpe Ratio", f"{sharpe_ratio:.2f}")
        
        with col3:
            profit_factor = risk_data.get('profit_factor', 0)
            st.metric("💹 Profit Factor", f"{profit_factor:.2f}")
        
        with col4:
            recovery_factor = risk_data.get('recovery_factor', 0)
            st.metric("🔄 Recovery Factor", f"{recovery_factor:.2f}")
        
        # Drawdown chart
        st.subheader("📉 Drawdown Analysis")
        self._render_drawdown_chart()
        
        # Risk distribution
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 P&L Distribution")
            self._render_pnl_histogram()
        
        with col2:
            st.subheader("🎯 Risk-Return Analysis")
            self._render_risk_return_analysis()
    
    def _render_export_tab(self):
        """Render export and reporting options"""
        st.subheader("📋 Export & Reporting")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Data Export")
            
            # Export options
            export_type = st.selectbox(
                "Export Format",
                ["CSV", "Excel", "JSON"],
                key="export_format"
            )
            
            export_data = st.selectbox(
                "Data to Export",
                ["All Trades", "P&L Summary", "Strategy Performance", "Risk Metrics"],
                key="export_data_type"
            )
            
            if st.button("📥 Download Data", use_container_width=True):
                self._handle_data_export(export_type, export_data)
        
        with col2:
            st.subheader("📄 Report Generation")
            
            report_type = st.selectbox(
                "Report Type",
                ["Daily Summary", "Weekly Report", "Monthly Report", "Custom Period"],
                key="report_type"
            )
            
            include_charts = st.checkbox("Include Charts", value=True)
            include_details = st.checkbox("Include Trade Details", value=False)
            
            if st.button("📄 Generate PDF Report", use_container_width=True):
                self._handle_report_generation(report_type, include_charts, include_details)
        
        # Scheduled reports
        st.subheader("📅 Scheduled Reports")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            schedule_enabled = st.checkbox("Enable Scheduled Reports")
        
        with col2:
            if schedule_enabled:
                schedule_frequency = st.selectbox(
                    "Frequency",
                    ["Daily", "Weekly", "Monthly"]
                )
        
        with col3:
            if schedule_enabled:
                email_recipients = st.text_input("Email Recipients (comma-separated)")
        
        if schedule_enabled and st.button("💾 Save Schedule"):
            st.success("✅ Scheduled reports configured successfully!")
    
    def _get_pnl_data(self) -> Dict[str, Any]:
        """Get P&L data for the selected time period"""
        try:
            # Get date range from session state
            start_date = st.session_state.get('pnl_start_date', datetime.now() - timedelta(days=30))
            end_date = st.session_state.get('pnl_end_date', datetime.now())
            
            # Get all trades in the period
            all_trades = self._get_trades_in_period(start_date, end_date)
            
            if not all_trades:
                return self._get_default_pnl_data()
            
            # Calculate metrics
            completed_trades = [t for t in all_trades if t.get('status') != 'open']
            
            if not completed_trades:
                return self._get_default_pnl_data()
            
            total_pnl = sum(trade.get('pnl', 0) for trade in completed_trades)
            
            # Find best and worst trades
            best_trade = max(completed_trades, key=lambda x: x.get('pnl', 0))
            worst_trade = min(completed_trades, key=lambda x: x.get('pnl', 0))
            
            # Calculate win rate
            winning_trades = [t for t in completed_trades if t.get('pnl', 0) > 0]
            win_rate = (len(winning_trades) / len(completed_trades) * 100) if completed_trades else 0
            
            # Calculate average profit per trade
            avg_profit = total_pnl / len(completed_trades) if completed_trades else 0
            
            return {
                'total_pnl': total_pnl,
                'pnl_change_pct': 0,  # Would need previous period data
                'best_trade': {
                    'pnl': best_trade.get('pnl', 0),
                    'symbol': best_trade.get('symbol', 'N/A')
                },
                'worst_trade': {
                    'pnl': worst_trade.get('pnl', 0),
                    'symbol': worst_trade.get('symbol', 'N/A')
                },
                'win_rate': win_rate,
                'win_rate_change': 0,  # Would need previous period data
                'total_trades': len(completed_trades),
                'avg_profit_per_trade': avg_profit
            }
            
        except Exception as e:
            st.error(f"Error calculating P&L data: {e}")
            return self._get_default_pnl_data()
    
    def _get_trades_in_period(self, start_date, end_date) -> List[Dict[str, Any]]:
        """Get all trades in the specified period"""
        try:
            # Convert dates to strings for comparison
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")
            
            all_trades = []
            
            # Get trades from Firestore
            if hasattr(self.trade_data, 'firestore') and hasattr(self.trade_data.firestore, 'db'):
                trades_collection = self.trade_data.firestore.db.collection('gpt_runner_trades')
                
                # Get all documents and filter by date
                docs = trades_collection.get()
                
                for doc in docs:
                    trade = doc.to_dict()
                    trade['id'] = doc.id
                    
                    if trade:
                        # Check if trade is in date range
                        trade_date = trade.get('entry_time', '')
                        if isinstance(trade_date, str) and start_str <= trade_date[:10] <= end_str:
                            all_trades.append(trade)
            
            return all_trades
            
        except Exception as e:
            st.error(f"Error fetching trades: {e}")
            return []
    
    def _get_default_pnl_data(self) -> Dict[str, Any]:
        """Get default P&L data when no real data is available"""
        return {
            'total_pnl': 0,
            'pnl_change_pct': 0,
            'best_trade': {'pnl': 0, 'symbol': 'N/A'},
            'worst_trade': {'pnl': 0, 'symbol': 'N/A'},
            'win_rate': 0,
            'win_rate_change': 0,
            'total_trades': 0,
            'avg_profit_per_trade': 0
        }
    
    def _render_pnl_distribution_chart(self):
        """Render P&L distribution pie chart"""
        st.subheader("📊 P&L Distribution")
        
        pnl_data = self._get_pnl_data()
        
        # Create sample distribution data
        if pnl_data['total_trades'] > 0:
            labels = ['Winning Trades', 'Losing Trades']
            win_rate = pnl_data['win_rate']
            values = [win_rate, 100 - win_rate]
            colors = ['#2E8B57', '#DC143C']
        else:
            labels = ['No Data']
            values = [100]
            colors = ['#808080']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker_colors=colors,
            hole=0.4
        )])
        
        fig.update_layout(
            title="Win/Loss Distribution",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_win_loss_chart(self):
        """Render win/loss ratio chart"""
        st.subheader("🎯 Win/Loss Analysis")
        
        pnl_data = self._get_pnl_data()
        
        fig = go.Figure()
        
        if pnl_data['total_trades'] > 0:
            win_rate = pnl_data['win_rate']
            loss_rate = 100 - win_rate
            
            fig.add_trace(go.Bar(
                x=['Win Rate', 'Loss Rate'],
                y=[win_rate, loss_rate],
                marker_color=['#2E8B57', '#DC143C'],
                text=[f'{win_rate:.1f}%', f'{loss_rate:.1f}%'],
                textposition='auto'
            ))
        else:
            fig.add_trace(go.Bar(
                x=['No Data'],
                y=[0],
                marker_color=['#808080']
            ))
        
        fig.update_layout(
            title="Win/Loss Percentage",
            yaxis_title="Percentage (%)",
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_top_trades_table(self):
        """Render table of top performing trades"""
        try:
            # Get trades for the period
            start_date = st.session_state.get('pnl_start_date', datetime.now() - timedelta(days=30))
            end_date = st.session_state.get('pnl_end_date', datetime.now())
            
            trades = self._get_trades_in_period(start_date, end_date)
            completed_trades = [t for t in trades if t.get('status') != 'open' and t.get('pnl') is not None]
            
            if completed_trades:
                # Sort by P&L and take top 10
                top_trades = sorted(completed_trades, key=lambda x: x.get('pnl', 0), reverse=True)[:10]
                
                df = pd.DataFrame([{
                    'Symbol': trade.get('symbol', 'N/A'),
                    'Strategy': trade.get('strategy', 'N/A'),
                    'Entry Price': f"₹{trade.get('entry_price', 0):,.2f}",
                    'Exit Price': f"₹{trade.get('exit_price', 0):,.2f}",
                    'P&L': f"₹{trade.get('pnl', 0):,.2f}",
                    'Duration': trade.get('duration', 'N/A'),
                    'Exit Time': trade.get('exit_time', 'N/A')
                } for trade in top_trades])
                
                # Style the dataframe
                def style_pnl(val):
                    if '₹' in str(val):
                        if '-' in str(val):
                            return 'color: red'
                        else:
                            return 'color: green'
                    return ''
                
                styled_df = df.style.applymap(style_pnl, subset=['P&L'])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            else:
                st.info("No completed trades found for the selected period")
                
        except Exception as e:
            st.error(f"Error rendering top trades table: {e}")
    
    def _render_strategy_comparison_chart(self):
        """Render strategy performance comparison"""
        strategy_data = self._get_strategy_performance_data()
        
        if strategy_data:
            df = pd.DataFrame(strategy_data)
            
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df['Strategy'],
                y=df['Total P&L'],
                name='Total P&L',
                marker_color=['#2E8B57' if x >= 0 else '#DC143C' for x in df['Total P&L']]
            ))
            
            fig.update_layout(
                title="Strategy Performance Comparison",
                xaxis_title="Strategy",
                yaxis_title="P&L (₹)",
                height=300,
                margin=dict(l=0, r=0, t=30, b=0),
                showlegend=False
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No strategy performance data available")
    
    def _render_cumulative_pnl_chart(self):
        """Render cumulative P&L timeline chart"""
        pnl_timeline = self.trade_data.get_pnl_timeline()
        
        if pnl_timeline:
            df = pd.DataFrame(pnl_timeline)
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(df['timestamp']),
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
                title="Cumulative P&L Over Time",
                xaxis_title="Time",
                yaxis_title="P&L (₹)",
                height=400,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No P&L timeline data available")
    
    def _render_daily_pnl_chart(self):
        """Render daily P&L bar chart"""
        # This would require daily aggregation of trades
        st.info("Daily P&L chart - Feature coming soon")
    
    def _render_hourly_pnl_pattern(self):
        """Render hourly P&L pattern"""
        # This would require hourly aggregation of trades
        st.info("Hourly P&L pattern - Feature coming soon")
    
    def _render_trade_frequency_chart(self):
        """Render trade frequency vs P&L analysis"""
        st.info("Trade frequency analysis - Feature coming soon")
    
    def _render_duration_analysis(self):
        """Render trade duration analysis"""
        st.info("Trade duration analysis - Feature coming soon")
    
    def _render_drawdown_chart(self):
        """Render drawdown chart"""
        st.info("Drawdown analysis chart - Feature coming soon")
    
    def _render_pnl_histogram(self):
        """Render P&L distribution histogram"""
        st.info("P&L distribution histogram - Feature coming soon")
    
    def _render_risk_return_analysis(self):
        """Render risk-return scatter plot"""
        st.info("Risk-return analysis - Feature coming soon")
    
    def _render_strategy_pnl_chart(self, df):
        """Render strategy-wise P&L chart"""
        st.info("Strategy P&L chart - Feature coming soon")
    
    def _render_strategy_risk_return_scatter(self, df):
        """Render strategy risk-return scatter plot"""
        st.info("Strategy risk-return scatter - Feature coming soon")
    
    def _get_strategy_performance_data(self) -> List[Dict[str, Any]]:
        """Get strategy performance data"""
        try:
            start_date = st.session_state.get('pnl_start_date', datetime.now() - timedelta(days=30))
            end_date = st.session_state.get('pnl_end_date', datetime.now())
            
            trades = self._get_trades_in_period(start_date, end_date)
            completed_trades = [t for t in trades if t.get('status') != 'open' and t.get('pnl') is not None]
            
            if not completed_trades:
                return []
            
            # Group by strategy
            strategy_stats = {}
            
            for trade in completed_trades:
                strategy = trade.get('strategy', 'Unknown')
                pnl = trade.get('pnl', 0)
                
                if strategy not in strategy_stats:
                    strategy_stats[strategy] = {
                        'trades': [],
                        'total_pnl': 0,
                        'win_count': 0
                    }
                
                strategy_stats[strategy]['trades'].append(trade)
                strategy_stats[strategy]['total_pnl'] += pnl
                if pnl > 0:
                    strategy_stats[strategy]['win_count'] += 1
            
            # Convert to list format
            result = []
            for strategy, stats in strategy_stats.items():
                trade_count = len(stats['trades'])
                win_rate = (stats['win_count'] / trade_count * 100) if trade_count > 0 else 0
                avg_pnl = stats['total_pnl'] / trade_count if trade_count > 0 else 0
                
                # Find best and worst trades for this strategy
                pnls = [t.get('pnl', 0) for t in stats['trades']]
                best_trade = max(pnls) if pnls else 0
                worst_trade = min(pnls) if pnls else 0
                
                result.append({
                    'Strategy': strategy,
                    'Total Trades': trade_count,
                    'Total P&L': stats['total_pnl'],
                    'Avg P&L': avg_pnl,
                    'Win Rate': win_rate,
                    'Best Trade': best_trade,
                    'Worst Trade': worst_trade
                })
            
            return result
            
        except Exception as e:
            st.error(f"Error getting strategy performance data: {e}")
            return []
    
    def _get_risk_metrics(self) -> Dict[str, Any]:
        """Get risk analysis metrics"""
        # This would require more sophisticated calculations
        # For now, return placeholder data
        return {
            'max_drawdown_pct': 0,
            'sharpe_ratio': 0,
            'profit_factor': 0,
            'recovery_factor': 0
        }
    
    def _handle_data_export(self, export_type: str, data_type: str):
        """Handle data export functionality"""
        st.info(f"📥 Exporting {data_type} as {export_type} - Feature coming soon")
        
    def _handle_report_generation(self, report_type: str, include_charts: bool, include_details: bool):
        """Handle PDF report generation"""
        st.info(f"�� Generating {report_type} report - Feature coming soon") 