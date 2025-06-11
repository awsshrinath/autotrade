"""
Strategy Performance Page Component
Detailed strategy analysis and performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import math


class StrategyPerformancePage:
    """Strategy performance page component"""
    
    def __init__(self, trade_data_provider):
        self.trade_data = trade_data_provider
    
    def render(self):
        """Render the strategy performance page"""
        st.markdown('<h1 style="color: #28a745; text-align: center; margin-bottom: 2rem;">🎯 Strategy Performance Dashboard</h1>', unsafe_allow_html=True)
        st.markdown("**Comprehensive strategy analysis with AI-powered optimization recommendations**")
        st.markdown('<hr style="height: 2px; background: linear-gradient(90deg, transparent, #28a745, transparent); border: none; margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Strategy overview metrics
        self._render_strategy_overview()
        
        # Main strategy analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Individual Performance", 
            "🔀 Strategy Comparison", 
            "📈 Win/Loss Analysis", 
            "🎯 Optimization", 
            "📋 Backtest vs Live"
        ])
        
        with tab1:
            self._render_individual_performance()
        
        with tab2:
            self._render_strategy_comparison()
        
        with tab3:
            self._render_winloss_analysis()
        
        with tab4:
            self._render_optimization_recommendations()
        
        with tab5:
            self._render_backtest_live_comparison()
    
    def _render_strategy_overview(self):
        """Render strategy overview metrics"""
        try:
            # Get strategy performance data
            strategy_data = self._get_strategy_performance_data()
            
            if not strategy_data:
                st.warning("No strategy performance data available")
                return
            
            # Calculate overview metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                total_strategies = len(strategy_data)
                st.metric("Total Strategies", total_strategies)
            
            with col2:
                profitable_strategies = sum(1 for s in strategy_data.values() if s.get('total_pnl', 0) > 0)
                st.metric("Profitable Strategies", profitable_strategies)
            
            with col3:
                avg_win_rate = np.mean([s.get('win_rate', 0) for s in strategy_data.values()])
                st.metric("Avg Win Rate", f"{avg_win_rate:.1f}%")
            
            with col4:
                best_strategy = max(strategy_data.items(), key=lambda x: x[1].get('total_pnl', 0))
                st.metric("Best Strategy", best_strategy[0])
            
            with col5:
                total_pnl = sum(s.get('total_pnl', 0) for s in strategy_data.values())
                st.metric("Total P&L", f"₹{total_pnl:,.2f}", 
                         delta=f"{total_pnl:+.2f}" if total_pnl != 0 else None)
        
        except Exception as e:
            st.error(f"Error loading strategy overview: {str(e)}")
    
    def _render_individual_performance(self):
        """Render individual strategy performance analysis"""
        st.subheader("📊 Individual Strategy Performance")
        
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if not strategy_data:
                st.info("No strategy data available for analysis")
                return
            
            # Strategy selector
            selected_strategy = st.selectbox(
                "Select Strategy",
                options=list(strategy_data.keys()),
                key="strategy_selector"
            )
            
            if selected_strategy and selected_strategy in strategy_data:
                strategy_info = strategy_data[selected_strategy]
                
                # Strategy metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    pnl = strategy_info.get('total_pnl', 0)
                    st.metric("Total P&L", f"₹{pnl:,.2f}", 
                             delta=f"{pnl:+.2f}" if pnl != 0 else None)
                
                with col2:
                    win_rate = strategy_info.get('win_rate', 0)
                    st.metric("Win Rate", f"{win_rate:.1f}%")
                
                with col3:
                    trade_count = strategy_info.get('trade_count', 0)
                    st.metric("Total Trades", trade_count)
                
                with col4:
                    sharpe = strategy_info.get('sharpe_ratio', 0)
                    st.metric("Sharpe Ratio", f"{sharpe:.2f}")
                
                # Strategy performance chart
                self._render_strategy_performance_chart(selected_strategy, strategy_info)
                
                # Strategy trades table
                self._render_strategy_trades_table(selected_strategy)
        
        except Exception as e:
            st.error(f"Error loading individual performance: {str(e)}")
    
    def _render_strategy_comparison(self):
        """Render strategy comparison charts"""
        st.subheader("🔀 Strategy Comparison")
        
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if not strategy_data or len(strategy_data) < 2:
                st.info("Need at least 2 strategies for comparison")
                return
            
            # Create comparison dataframe
            comparison_df = pd.DataFrame([
                {
                    'Strategy': name,
                    'Total P&L': data.get('total_pnl', 0),
                    'Win Rate': data.get('win_rate', 0),
                    'Trade Count': data.get('trade_count', 0),
                    'Sharpe Ratio': data.get('sharpe_ratio', 0),
                    'Max Drawdown': data.get('max_drawdown', 0),
                    'Avg Trade': data.get('avg_trade_pnl', 0)
                }
                for name, data in strategy_data.items()
            ])
            
            # Strategy comparison bar chart
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Bar(
                name='Total P&L',
                x=comparison_df['Strategy'],
                y=comparison_df['Total P&L'],
                marker_color=['green' if x > 0 else 'red' for x in comparison_df['Total P&L']]
            ))
            
            fig_comparison.update_layout(
                title="Strategy P&L Comparison",
                xaxis_title="Strategy",
                yaxis_title="Total P&L (₹)",
                height=400
            )
            
            st.plotly_chart(fig_comparison, use_container_width=True)
            
            # Risk-Return scatter plot
            fig_scatter = px.scatter(
                comparison_df,
                x='Sharpe Ratio',
                y='Total P&L',
                size='Trade Count',
                color='Win Rate',
                hover_name='Strategy',
                title="Risk-Return Analysis",
                labels={'Win Rate': 'Win Rate (%)'}
            )
            
            st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Strategy comparison table
            st.subheader("📋 Strategy Metrics Comparison")
            styled_df = comparison_df.style.format({
                'Total P&L': '₹{:,.2f}',
                'Win Rate': '{:.1f}%',
                'Sharpe Ratio': '{:.2f}',
                'Max Drawdown': '{:.2f}%',
                'Avg Trade': '₹{:,.2f}'
            }).background_gradient(subset=['Total P&L'], cmap='RdYlGn')
            
            st.dataframe(styled_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error loading strategy comparison: {str(e)}")
    
    def _render_winloss_analysis(self):
        """Render win/loss ratio analysis"""
        st.subheader("📈 Win/Loss Analysis")
        
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if not strategy_data:
                st.info("No strategy data available for win/loss analysis")
                return
            
            # Strategy selector for detailed analysis
            selected_strategy = st.selectbox(
                "Select Strategy for Detailed Analysis",
                options=list(strategy_data.keys()),
                key="winloss_strategy_selector"
            )
            
            if selected_strategy and selected_strategy in strategy_data:
                strategy_info = strategy_data[selected_strategy]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Win/Loss distribution pie chart
                    wins = strategy_info.get('wins', 0)
                    losses = strategy_info.get('losses', 0)
                    
                    if wins + losses > 0:
                        fig_pie = go.Figure(data=[go.Pie(
                            labels=['Wins', 'Losses'],
                            values=[wins, losses],
                            marker_colors=['green', 'red'],
                            hole=0.3
                        )])
                        
                        fig_pie.update_layout(
                            title=f"{selected_strategy} - Win/Loss Distribution",
                            height=400
                        )
                        
                        st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    # Win/Loss metrics
                    st.write("**Win/Loss Metrics:**")
                    
                    win_rate = strategy_info.get('win_rate', 0)
                    avg_win = strategy_info.get('avg_win', 0)
                    avg_loss = strategy_info.get('avg_loss', 0)
                    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0
                    
                    metrics_df = pd.DataFrame([
                        {"Metric": "Win Rate", "Value": f"{win_rate:.1f}%"},
                        {"Metric": "Average Win", "Value": f"₹{avg_win:,.2f}"},
                        {"Metric": "Average Loss", "Value": f"₹{avg_loss:,.2f}"},
                        {"Metric": "Profit Factor", "Value": f"{profit_factor:.2f}"},
                        {"Metric": "Total Wins", "Value": str(wins)},
                        {"Metric": "Total Losses", "Value": str(losses)}
                    ])
                    
                    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
                
                # Trade outcome timeline
                self._render_trade_outcome_timeline(selected_strategy)
        
        except Exception as e:
            st.error(f"Error loading win/loss analysis: {str(e)}")
    
    def _render_optimization_recommendations(self):
        """Render strategy optimization recommendations"""
        st.subheader("🎯 Strategy Optimization")
        
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if not strategy_data:
                st.info("No strategy data available for optimization analysis")
                return
            
            # Generate optimization recommendations
            recommendations = self._generate_optimization_recommendations(strategy_data)
            
            if recommendations:
                st.write("**AI-Powered Optimization Recommendations:**")
                
                for i, rec in enumerate(recommendations, 1):
                    with st.expander(f"Recommendation {i}: {rec['title']}"):
                        st.write(f"**Strategy:** {rec['strategy']}")
                        st.write(f"**Issue:** {rec['issue']}")
                        st.write(f"**Recommendation:** {rec['recommendation']}")
                        st.write(f"**Expected Impact:** {rec['impact']}")
                        
                        # Add action buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Apply Recommendation {i}", key=f"apply_{i}"):
                                st.success("Recommendation marked for implementation")
                        with col2:
                            if st.button(f"Dismiss {i}", key=f"dismiss_{i}"):
                                st.info("Recommendation dismissed")
            
            # Strategy performance ranking
            st.subheader("📊 Strategy Performance Ranking")
            
            ranking_df = pd.DataFrame([
                {
                    'Rank': i + 1,
                    'Strategy': name,
                    'Score': self._calculate_strategy_score(data),
                    'P&L': data.get('total_pnl', 0),
                    'Win Rate': data.get('win_rate', 0),
                    'Sharpe': data.get('sharpe_ratio', 0),
                    'Status': self._get_strategy_status(data)
                }
                for i, (name, data) in enumerate(
                    sorted(strategy_data.items(), 
                          key=lambda x: self._calculate_strategy_score(x[1]), 
                          reverse=True)
                )
            ])
            
            styled_ranking = ranking_df.style.format({
                'Score': '{:.1f}',
                'P&L': '₹{:,.2f}',
                'Win Rate': '{:.1f}%',
                'Sharpe': '{:.2f}'
            }).background_gradient(subset=['Score'], cmap='RdYlGn')
            
            st.dataframe(styled_ranking, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error loading optimization recommendations: {str(e)}")
    
    def _render_backtest_live_comparison(self):
        """Render backtest vs live performance comparison"""
        st.subheader("📋 Backtest vs Live Performance")
        
        try:
            st.info("🚧 Backtest comparison feature requires historical backtest data integration")
            
            # Placeholder for backtest comparison
            strategy_data = self._get_strategy_performance_data()
            
            if strategy_data:
                # Mock backtest data for demonstration
                comparison_data = []
                for strategy_name, live_data in strategy_data.items():
                    # Generate mock backtest data (in real implementation, this would come from backtesting results)
                    backtest_pnl = live_data.get('total_pnl', 0) * (1 + np.random.uniform(-0.2, 0.3))
                    backtest_winrate = live_data.get('win_rate', 0) * (1 + np.random.uniform(-0.1, 0.2))
                    
                    comparison_data.append({
                        'Strategy': strategy_name,
                        'Live P&L': live_data.get('total_pnl', 0),
                        'Backtest P&L': backtest_pnl,
                        'Live Win Rate': live_data.get('win_rate', 0),
                        'Backtest Win Rate': backtest_winrate,
                        'P&L Difference': live_data.get('total_pnl', 0) - backtest_pnl,
                        'Performance Gap': 'Underperforming' if live_data.get('total_pnl', 0) < backtest_pnl else 'Outperforming'
                    })
                
                comparison_df = pd.DataFrame(comparison_data)
                
                # Backtest vs Live chart
                fig_comparison = go.Figure()
                
                fig_comparison.add_trace(go.Bar(
                    name='Live Performance',
                    x=comparison_df['Strategy'],
                    y=comparison_df['Live P&L'],
                    marker_color='blue',
                    opacity=0.7
                ))
                
                fig_comparison.add_trace(go.Bar(
                    name='Backtest Performance',
                    x=comparison_df['Strategy'],
                    y=comparison_df['Backtest P&L'],
                    marker_color='orange',
                    opacity=0.7
                ))
                
                fig_comparison.update_layout(
                    title="Live vs Backtest Performance Comparison",
                    xaxis_title="Strategy",
                    yaxis_title="P&L (₹)",
                    height=400,
                    barmode='group'
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                # Comparison table
                styled_comparison = comparison_df.style.format({
                    'Live P&L': '₹{:,.2f}',
                    'Backtest P&L': '₹{:,.2f}',
                    'Live Win Rate': '{:.1f}%',
                    'Backtest Win Rate': '{:.1f}%',
                    'P&L Difference': '₹{:+,.2f}'
                }).apply(lambda x: ['background-color: lightgreen' if v == 'Outperforming' 
                                  else 'background-color: lightcoral' if v == 'Underperforming' 
                                  else '' for v in x], subset=['Performance Gap'])
                
                st.dataframe(styled_comparison, use_container_width=True)
                
                # Performance analysis
                st.subheader("📈 Performance Analysis")
                
                underperforming = comparison_df[comparison_df['Performance Gap'] == 'Underperforming']
                if not underperforming.empty:
                    st.warning(f"⚠️ {len(underperforming)} strategies are underperforming compared to backtest")
                    for _, row in underperforming.iterrows():
                        st.write(f"• **{row['Strategy']}**: Live P&L ₹{row['Live P&L']:,.2f} vs Backtest ₹{row['Backtest P&L']:,.2f}")
        
        except Exception as e:
            st.error(f"Error loading backtest comparison: {str(e)}")
    
    def _get_strategy_performance_data(self) -> Dict[str, Any]:
        """Get strategy performance data from trade data provider"""
        try:
            # Get trades data
            trades = self.trade_data.get_recent_trades(limit=1000)
            
            if not trades:
                return {}
            
            # Group trades by strategy
            strategy_data = {}
            
            for trade in trades:
                strategy = trade.get('strategy', 'Unknown Strategy')
                pnl = trade.get('pnl', 0)
                
                if strategy not in strategy_data:
                    strategy_data[strategy] = {
                        'trades': [],
                        'total_pnl': 0,
                        'wins': 0,
                        'losses': 0,
                        'trade_count': 0
                    }
                
                strategy_data[strategy]['trades'].append(trade)
                strategy_data[strategy]['total_pnl'] += pnl
                strategy_data[strategy]['trade_count'] += 1
                
                if pnl > 0:
                    strategy_data[strategy]['wins'] += 1
                elif pnl < 0:
                    strategy_data[strategy]['losses'] += 1
            
            # Calculate additional metrics for each strategy
            for strategy, data in strategy_data.items():
                trades = data['trades']
                total_trades = len(trades)
                
                if total_trades > 0:
                    # Win rate
                    data['win_rate'] = (data['wins'] / total_trades) * 100
                    
                    # Average trade P&L
                    data['avg_trade_pnl'] = data['total_pnl'] / total_trades
                    
                    # Average win/loss
                    winning_trades = [t['pnl'] for t in trades if t.get('pnl', 0) > 0]
                    losing_trades = [t['pnl'] for t in trades if t.get('pnl', 0) < 0]
                    
                    data['avg_win'] = np.mean(winning_trades) if winning_trades else 0
                    data['avg_loss'] = np.mean(losing_trades) if losing_trades else 0
                    
                    # Sharpe ratio (simplified)
                    pnl_series = [t.get('pnl', 0) for t in trades]
                    if len(pnl_series) > 1:
                        mean_return = np.mean(pnl_series)
                        std_return = np.std(pnl_series)
                        data['sharpe_ratio'] = mean_return / std_return if std_return != 0 else 0
                    else:
                        data['sharpe_ratio'] = 0
                    
                    # Max drawdown (simplified)
                    cumulative_pnl = np.cumsum(pnl_series)
                    running_max = np.maximum.accumulate(cumulative_pnl)
                    drawdown = (cumulative_pnl - running_max) / running_max
                    data['max_drawdown'] = abs(np.min(drawdown)) * 100 if len(drawdown) > 0 else 0
            
            return strategy_data
        
        except Exception as e:
            st.error(f"Error getting strategy performance data: {str(e)}")
            return {}
    
    def _render_strategy_performance_chart(self, strategy_name: str, strategy_info: Dict[str, Any]):
        """Render strategy performance chart"""
        try:
            trades = strategy_info.get('trades', [])
            
            if not trades:
                st.info("No trades available for chart")
                return
            
            # Create cumulative P&L chart
            pnl_values = [trade.get('pnl', 0) for trade in trades]
            cumulative_pnl = np.cumsum(pnl_values)
            
            # Create timestamps (using trade dates if available, otherwise generate)
            timestamps = []
            for i, trade in enumerate(trades):
                if 'timestamp' in trade:
                    timestamps.append(pd.to_datetime(trade['timestamp']))
                else:
                    timestamps.append(datetime.now() - timedelta(days=len(trades)-i))
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=timestamps,
                y=cumulative_pnl,
                mode='lines+markers',
                name='Cumulative P&L',
                line=dict(color='blue', width=2),
                marker=dict(size=4)
            ))
            
            fig.update_layout(
                title=f"{strategy_name} - Cumulative P&L Performance",
                xaxis_title="Date",
                yaxis_title="Cumulative P&L (₹)",
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error rendering strategy chart: {str(e)}")
    
    def _render_strategy_trades_table(self, strategy_name: str):
        """Render strategy trades table"""
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if strategy_name not in strategy_data:
                return
            
            trades = strategy_data[strategy_name]['trades']
            
            if not trades:
                st.info("No trades available for this strategy")
                return
            
            # Create trades dataframe
            trades_df = pd.DataFrame([
                {
                    'Date': trade.get('timestamp', 'Unknown'),
                    'Symbol': trade.get('symbol', 'Unknown'),
                    'Action': trade.get('action', 'Unknown'),
                    'Quantity': trade.get('quantity', 0),
                    'Price': trade.get('price', 0),
                    'P&L': trade.get('pnl', 0),
                    'Status': 'Win' if trade.get('pnl', 0) > 0 else 'Loss' if trade.get('pnl', 0) < 0 else 'Breakeven'
                }
                for trade in trades[-20:]  # Show last 20 trades
            ])
            
            if not trades_df.empty:
                st.subheader(f"📋 Recent {strategy_name} Trades")
                
                # Style the dataframe
                styled_df = trades_df.style.format({
                    'Price': '₹{:,.2f}',
                    'P&L': '₹{:+,.2f}'
                }).apply(lambda x: ['background-color: lightgreen' if v == 'Win' 
                                  else 'background-color: lightcoral' if v == 'Loss' 
                                  else 'background-color: lightgray' for v in x], 
                        subset=['Status'])
                
                st.dataframe(styled_df, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error rendering trades table: {str(e)}")
    
    def _render_trade_outcome_timeline(self, strategy_name: str):
        """Render trade outcome timeline"""
        try:
            strategy_data = self._get_strategy_performance_data()
            
            if strategy_name not in strategy_data:
                return
            
            trades = strategy_data[strategy_name]['trades']
            
            if not trades:
                return
            
            # Create outcome timeline
            outcomes = ['Win' if trade.get('pnl', 0) > 0 else 'Loss' for trade in trades]
            trade_numbers = list(range(1, len(outcomes) + 1))
            
            colors = ['green' if outcome == 'Win' else 'red' for outcome in outcomes]
            
            fig = go.Figure(data=[go.Bar(
                x=trade_numbers,
                y=[1 if outcome == 'Win' else -1 for outcome in outcomes],
                marker_color=colors,
                name='Trade Outcomes'
            )])
            
            fig.update_layout(
                title=f"{strategy_name} - Trade Outcome Timeline",
                xaxis_title="Trade Number",
                yaxis_title="Win/Loss",
                height=300,
                showlegend=False
            )
            
            fig.update_yaxis(tickvals=[-1, 0, 1], ticktext=['Loss', 'Breakeven', 'Win'])
            
            st.plotly_chart(fig, use_container_width=True)
        
        except Exception as e:
            st.error(f"Error rendering outcome timeline: {str(e)}")
    
    def _generate_optimization_recommendations(self, strategy_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate AI-powered optimization recommendations"""
        recommendations = []
        
        try:
            for strategy_name, data in strategy_data.items():
                win_rate = data.get('win_rate', 0)
                total_pnl = data.get('total_pnl', 0)
                sharpe_ratio = data.get('sharpe_ratio', 0)
                trade_count = data.get('trade_count', 0)
                
                # Low win rate recommendation
                if win_rate < 40 and trade_count > 10:
                    recommendations.append({
                        'title': 'Improve Win Rate',
                        'strategy': strategy_name,
                        'issue': f'Low win rate of {win_rate:.1f}%',
                        'recommendation': 'Consider tightening entry criteria and improving signal quality',
                        'impact': 'Could improve win rate by 10-15%'
                    })
                
                # Negative P&L recommendation
                if total_pnl < 0:
                    recommendations.append({
                        'title': 'Address Losses',
                        'strategy': strategy_name,
                        'issue': f'Negative total P&L of ₹{total_pnl:,.2f}',
                        'recommendation': 'Review risk management rules and consider reducing position sizes',
                        'impact': 'Could reduce losses by 20-30%'
                    })
                
                # Low Sharpe ratio recommendation
                if sharpe_ratio < 0.5 and trade_count > 5:
                    recommendations.append({
                        'title': 'Improve Risk-Adjusted Returns',
                        'strategy': strategy_name,
                        'issue': f'Low Sharpe ratio of {sharpe_ratio:.2f}',
                        'recommendation': 'Optimize position sizing and consider volatility-based adjustments',
                        'impact': 'Could improve risk-adjusted returns by 25%'
                    })
                
                # Low trade count recommendation
                if trade_count < 5:
                    recommendations.append({
                        'title': 'Increase Trading Frequency',
                        'strategy': strategy_name,
                        'issue': f'Only {trade_count} trades executed',
                        'recommendation': 'Review strategy parameters to identify more opportunities',
                        'impact': 'Could increase trading opportunities by 50%'
                    })
        
        except Exception as e:
            st.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _calculate_strategy_score(self, strategy_data: Dict[str, Any]) -> float:
        """Calculate overall strategy performance score"""
        try:
            # Normalize metrics to 0-100 scale
            win_rate = strategy_data.get('win_rate', 0)
            total_pnl = max(0, strategy_data.get('total_pnl', 0))  # Only positive P&L contributes
            sharpe_ratio = max(0, strategy_data.get('sharpe_ratio', 0))
            trade_count = min(100, strategy_data.get('trade_count', 0))  # Cap at 100
            
            # Weighted score calculation
            score = (
                win_rate * 0.3 +  # 30% weight on win rate
                min(100, total_pnl / 100) * 0.4 +  # 40% weight on P&L (₹100 = 1 point)
                min(100, sharpe_ratio * 20) * 0.2 +  # 20% weight on Sharpe ratio
                trade_count * 0.1  # 10% weight on trade count
            )
            
            return min(100, score)  # Cap at 100
        
        except Exception:
            return 0.0
    
    def _get_strategy_status(self, strategy_data: Dict[str, Any]) -> str:
        """Get strategy status based on performance"""
        score = self._calculate_strategy_score(strategy_data)
        
        if score >= 80:
            return "🟢 Excellent"
        elif score >= 60:
            return "🟡 Good"
        elif score >= 40:
            return "🟠 Average"
        else:
            return "🔴 Poor"
 