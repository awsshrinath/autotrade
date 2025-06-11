"""
System Health Page Component
System monitoring and health status display
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Any


class SystemHealthPage:
    """System health page component for monitoring system status"""
    
    def __init__(self, system_data_provider):
        self.system_data = system_data_provider
    
    def render(self):
        """Render the system health page"""
        st.markdown('<h1 style="color: #333333; text-align: center; margin-bottom: 2rem;">⚙️ System Health Monitor</h1>', unsafe_allow_html=True)
        st.markdown('<div style="color: #333333; font-weight: 600; text-align: center; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">Real-time system monitoring and health status tracking</div>', unsafe_allow_html=True)
        st.markdown('<hr style="height: 2px; background: linear-gradient(90deg, transparent, #6c757d, transparent); border: none; margin: 2rem 0;">', unsafe_allow_html=True)
        
        # Overall status
        self._render_overall_status()
        
        # Health checks grid
        self._render_health_checks()
        
        # System metrics
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_resource_usage()
        
        with col2:
            self._render_service_status()
        
        # Performance metrics
        self._render_performance_metrics()
        
        # Logs and alerts
        col1, col2 = st.columns(2)
        
        with col1:
            self._render_recent_alerts()
        
        with col2:
            self._render_log_summary()
    
    def _render_overall_status(self):
        """Render overall system status"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">🎯 Overall System Status</h2>', unsafe_allow_html=True)
        
        # Get system status
        status_data = self.system_data.get_system_status()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            status = status_data.get('overall_status', 'unknown')
            status_icon = "✅" if status == 'healthy' else "⚠️" if status == 'degraded' else "❌"
            status_color = "green" if status == 'healthy' else "orange" if status == 'degraded' else "red"
            
            st.markdown(f"""
            <div style="
                text-align: center; 
                padding: 1.5rem; 
                border: 2px solid {status_color}; 
                border-radius: 10px;
                background-color: white;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                color: #333333 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                margin-bottom: 1rem;
            ">
                <h2 style="margin: 0; font-size: 2rem; color: #333333 !important;">{status_icon}</h2>
                <h3 style="color: {status_color} !important; margin: 0.5rem 0; font-weight: 600;">{str(status).upper()}</h3>
                <p style="color: #555555 !important; margin: 0; font-size: 0.9rem;">System Status</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            uptime = status_data.get('uptime_hours', 0)
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #333333 !important; margin: 0;">⏱️ Uptime</h3>
                <h2 style="color: #007acc !important; margin: 0.5rem 0;">{uptime:.1f} hours</h2>
                <p style="color: #666666 !important; margin: 0; font-size: 0.8rem;">{uptime/24:.1f} days</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            critical_failures = status_data.get('critical_failures', 0)
            failure_color = "red" if critical_failures > 0 else "green"
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #333333 !important; margin: 0;">🚨 Critical Issues</h3>
                <h2 style="color: {failure_color} !important; margin: 0.5rem 0;">{critical_failures}</h2>
                <p style="color: #666666 !important; margin: 0; font-size: 0.8rem;">{"Active" if critical_failures > 0 else "None"}</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            system_ready = status_data.get('system_ready', False)
            ready_icon = "✅" if system_ready else "❌"
            ready_color = "green" if system_ready else "red"
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h3 style="color: #333333 !important; margin: 0;">🎯 System Ready</h3>
                <h2 style="color: {ready_color} !important; margin: 0.5rem 0;">{ready_icon} {'Yes' if system_ready else 'No'}</h2>
                <p style="color: #666666 !important; margin: 0; font-size: 0.8rem;">Trading Ready</p>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_health_checks(self):
        """Render detailed health checks"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">🔍 Health Checks</h2>', unsafe_allow_html=True)
        
        # Get health check data
        health_checks = self.system_data.get_health_checks()
        
        # Debug info (temporarily visible)
        with st.expander("🐛 Debug Health Check Data", expanded=False):
            st.markdown('<div style="background-color: white; padding: 1rem; border-radius: 8px; color: #333333 !important;">', unsafe_allow_html=True)
            st.write(f"Health checks type: {type(health_checks)}")
            st.write(f"Health checks length: {len(health_checks) if health_checks else 'None'}")
            st.json(health_checks)
            st.markdown('</div>', unsafe_allow_html=True)
        
        if health_checks and len(health_checks) > 0:
            # Create grid layout
            cols = st.columns(3)
            
            for i, check in enumerate(health_checks):
                with cols[i % 3]:
                    service = check.get('service', 'Unknown')
                    status = check.get('status', 'unknown')
                    response_time = check.get('response_time', 0)
                    is_critical = check.get('is_critical', False)
                    details = check.get('details', {})
                    
                    # Status styling
                    if status == 'healthy':
                        status_color = "green"
                        status_icon = "✅"
                        status_bg = "#d4edda"
                        border_color = "green"
                    elif status == 'degraded':
                        status_color = "orange"
                        status_icon = "⚠️"
                        status_bg = "#fff3cd"
                        border_color = "orange"
                    else:
                        status_color = "red"
                        status_icon = "❌"
                        status_bg = "#f8d7da"
                        border_color = "red"
                    
                    # Critical indicator
                    critical_badge = " 🔴 CRITICAL" if is_critical and status != 'healthy' else ""
                    
                    # Format details for display
                    details_text = ""
                    if details:
                        for key, value in details.items():
                            if isinstance(value, (int, float)):
                                if 'usage' in key.lower():
                                    details_text += f"<small style='color: #333333 !important; display: block; margin: 2px 0;'><strong style='color: #333333 !important;'>{key.replace('_', ' ').title()}:</strong> {value:.1f}%</small>"
                                elif 'time' in key.lower():
                                    details_text += f"<small style='color: #333333 !important; display: block; margin: 2px 0;'><strong style='color: #333333 !important;'>{key.replace('_', ' ').title()}:</strong> {value:.0f}ms</small>"
                                else:
                                    details_text += f"<small style='color: #333333 !important; display: block; margin: 2px 0;'><strong style='color: #333333 !important;'>{key.replace('_', ' ').title()}:</strong> {value}</small>"
                            elif isinstance(value, str):
                                details_text += f"<small style='color: #333333 !important; display: block; margin: 2px 0;'><strong style='color: #333333 !important;'>{key.replace('_', ' ').title()}:</strong> {value}</small>"
                    
                    st.markdown(f"""
                    <div style="
                        background-color: white;
                        padding: 1.5rem;
                        border-radius: 8px;
                        border: 2px solid {border_color};
                        margin-bottom: 1rem;
                        min-height: 140px;
                        color: #333333 !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    ">
                        <h4 style="margin: 0 0 10px 0; color: {status_color} !important; font-weight: 600; font-size: 1.1rem;">
                            {status_icon} {service.replace('_', ' ').title()}{critical_badge}
                        </h4>
                        <p style="margin: 5px 0; color: #333333 !important; font-size: 0.9rem;"><strong style="color: #333333 !important;">Status:</strong> 
                           <span style="color: {status_color} !important; font-weight: bold;">{str(status).upper()}</span>
                        </p>
                        <p style="margin: 5px 0; color: #333333 !important; font-size: 0.9rem;"><strong style="color: #333333 !important;">Response:</strong> {response_time*1000:.0f}ms</p>
                        <div style="color: #333333 !important; font-size: 0.85rem; margin-top: 10px;">
                            {details_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 2px solid orange; color: #333333 !important;">
                ⚠️ Health check data is not available. System may be starting up or experiencing connectivity issues.
            </div>
            """, unsafe_allow_html=True)
    
    def _render_resource_usage(self):
        """Render system resource usage"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">📊 Resource Usage</h2>', unsafe_allow_html=True)
        
        # Get system metrics
        metrics = self.system_data.get_system_metrics()
        
        # Create container for metrics
        st.markdown('<div style="background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        
        # CPU Usage
        cpu_usage = metrics.get('cpu_usage', 0)
        cpu_color = "red" if cpu_usage > 80 else "orange" if cpu_usage > 60 else "green"
        st.markdown(f'<h4 style="color: #333333 !important; margin-bottom: 0.5rem;">💻 CPU Usage: {cpu_usage:.1f}%</h4>', unsafe_allow_html=True)
        st.progress(cpu_usage/100)
        
        # Memory Usage
        memory_usage = metrics.get('memory_usage', 0)
        memory_available = metrics.get('memory_available_gb', 0)
        memory_color = "red" if memory_usage > 85 else "orange" if memory_usage > 70 else "green"
        st.markdown(f'<h4 style="color: #333333 !important; margin: 1rem 0 0.5rem 0;">🧠 Memory Usage: {memory_usage:.1f}%</h4>', unsafe_allow_html=True)
        st.markdown(f'<p style="color: #666666 !important; margin: 0;">{memory_available:.1f}GB available</p>', unsafe_allow_html=True)
        st.progress(memory_usage/100)
        
        # Disk Usage
        disk_usage = metrics.get('disk_usage', 0)
        disk_color = "red" if disk_usage > 90 else "orange" if disk_usage > 75 else "green"
        st.markdown(f'<h4 style="color: #333333 !important; margin: 1rem 0 0.5rem 0;">💾 Disk Usage: {disk_usage:.1f}%</h4>', unsafe_allow_html=True)
        st.progress(disk_usage/100)
        
        # Network Connections
        network_connections = metrics.get('network_connections', 0)
        st.markdown(f'<h4 style="color: #333333 !important; margin: 1rem 0 0.5rem 0;">🌐 Network Connections: {network_connections}</h4>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_service_status(self):
        """Render individual service status"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">🔧 Service Status</h2>', unsafe_allow_html=True)
        
        # Get service status
        services = self.system_data.get_service_status()
        
        if services:
            st.markdown('<div style="background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
            
            for service_name, service_data in services.items():
                status = service_data.get('status', 'unknown')
                health = service_data.get('health', 'unknown')
                
                # Fix the logic to properly handle different status combinations
                if (status == 'running' or status == 'connected') and health == 'healthy':
                    icon = "✅"
                    color = "green"
                elif status == 'running' or status == 'connected':
                    icon = "⚠️"
                    color = "orange" 
                elif status == 'disconnected' or status == 'stopped':
                    icon = "❌"
                    color = "red"
                else:
                    icon = "❓"
                    color = "gray"
                
                # Display service with proper styling
                st.markdown(f"""
                <div style="
                    display: flex; 
                    justify-content: space-between; 
                    align-items: center; 
                    padding: 0.75rem; 
                    margin: 0.5rem 0;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    background-color: #f9f9f9;
                ">
                    <div style="color: #333333 !important; font-weight: 600;">
                        {icon} {service_name.replace('_', ' ').title()}
                    </div>
                    <div style="display: flex; gap: 1rem;">
                        <span style="color: {color} !important; font-weight: bold; font-size: 0.9rem;">{status}</span>
                        <span style="color: {color} !important; font-weight: bold; font-size: 0.9rem;">{health}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background-color: white; padding: 1.5rem; border-radius: 8px; border: 2px solid #007acc; color: #333333 !important;">
                ℹ️ No service status data available
            </div>
            """, unsafe_allow_html=True)
    
    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">⚡ Performance Metrics</h2>', unsafe_allow_html=True)
        
        # Get performance data
        perf_data = self.system_data.get_performance_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            api_time = perf_data.get('api_response_time_ms', 0)
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #333333 !important; margin: 0;">🔗 API Response</h4>
                <h3 style="color: #007acc !important; margin: 0.5rem 0;">{api_time}ms</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            db_time = perf_data.get('database_query_time_ms', 0)
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #333333 !important; margin: 0;">🗄️ Database Query</h4>
                <h3 style="color: #007acc !important; margin: 0.5rem 0;">{db_time}ms</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            trade_time = perf_data.get('trade_execution_time_ms', 0)
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #333333 !important; margin: 0;">📈 Trade Execution</h4>
                <h3 style="color: #007acc !important; margin: 0.5rem 0;">{trade_time}ms</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            uptime_pct = perf_data.get('uptime_pct', 0)
            st.markdown(f"""
            <div style="background-color: white; padding: 1rem; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <h4 style="color: #333333 !important; margin: 0;">⏰ Uptime</h4>
                <h3 style="color: #007acc !important; margin: 0.5rem 0;">{uptime_pct:.1f}%</h3>
            </div>
            """, unsafe_allow_html=True)
        
        # Performance trends (mock data for visualization)
        st.markdown('<h3 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin: 2rem 0 1rem 0;">📈 Performance Trends</h3>', unsafe_allow_html=True)
        
        # Create sample trend data
        times = pd.date_range(start=datetime.now() - timedelta(hours=24), end=datetime.now(), freq='1H')
        trend_data = pd.DataFrame({
            'time': times,
            'api_response': [api_time + (i % 10 - 5) * 10 for i in range(len(times))],
            'memory_usage': [60 + (i % 20 - 10) for i in range(len(times))],
            'cpu_usage': [40 + (i % 15 - 7) for i in range(len(times))]
        })
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=trend_data['time'],
            y=trend_data['api_response'],
            mode='lines',
            name='API Response (ms)',
            line=dict(color='blue')
        ))
        
        fig.add_trace(go.Scatter(
            x=trend_data['time'],
            y=trend_data['memory_usage'],
            mode='lines',
            name='Memory Usage (%)',
            yaxis='y2',
            line=dict(color='red')
        ))
        
        fig.update_layout(
            title="24-Hour Performance Trends",
            xaxis_title="Time",
            yaxis=dict(title="API Response (ms)", side="left"),
            yaxis2=dict(title="Memory Usage (%)", side="right", overlaying="y"),
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(color='#333333')
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_alerts(self):
        """Render recent system alerts"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">🚨 Recent Alerts</h2>', unsafe_allow_html=True)
        
        # Get alerts
        alerts = self.system_data.get_alerts()
        
        st.markdown('<div style="background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        
        if alerts:
            for alert in alerts[-10:]:  # Show last 10 alerts
                alert_type = alert.get('type', 'info')
                message = alert.get('message', 'No message')
                timestamp = alert.get('timestamp', datetime.now().isoformat())
                severity = alert.get('severity', 'low')
                
                # Alert styling
                if alert_type == 'critical':
                    icon = "🔴"
                    color = "red"
                    bg_color = "#ffe6e6"
                elif alert_type == 'warning':
                    icon = "🟡"
                    color = "orange"
                    bg_color = "#fff3e0"
                else:
                    icon = "🔵"
                    color = "blue"
                    bg_color = "#e3f2fd"
                
                # Format timestamp
                try:
                    alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = alert_time.strftime('%H:%M:%S')
                except:
                    time_str = "Unknown"
                
                st.markdown(f"""
                <div style="
                    padding: 0.75rem; 
                    margin: 0.5rem 0; 
                    border-left: 4px solid {color}; 
                    background-color: {bg_color};
                    border-radius: 4px;
                    color: #333333 !important;
                ">
                    {icon} <strong style="color: #333333 !important;">{time_str}</strong> - <span style="color: #333333 !important;">{message}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 1rem; text-align: center; background-color: #e8f5e8; border-radius: 8px; color: #333333 !important;">
                ✅ No recent alerts
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    def _render_log_summary(self):
        """Render log summary"""
        st.markdown('<h2 style="color: #333333; background-color: rgba(255,255,255,0.9); padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">📋 Log Summary</h2>', unsafe_allow_html=True)
        
        # Get log summary
        log_data = self.system_data.get_log_summary()
        
        st.markdown('<div style="background-color: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">', unsafe_allow_html=True)
        
        if log_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 1rem; background-color: #f9f9f9;">
                    <h4 style="color: #333333 !important; margin: 0;">📁 Log Files</h4>
                    <h3 style="color: #007acc !important; margin: 0.5rem 0;">{log_data.get('total_log_files', 0)}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 6px; background-color: #f9f9f9;">
                    <h4 style="color: #333333 !important; margin: 0;">📝 Total Entries</h4>
                    <h3 style="color: #007acc !important; margin: 0.5rem 0;">{log_data.get('total_entries', 0)}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 6px; margin-bottom: 1rem; background-color: #f9f9f9;">
                    <h4 style="color: #333333 !important; margin: 0;">❌ Error Entries</h4>
                    <h3 style="color: red !important; margin: 0.5rem 0;">{log_data.get('error_entries', 0)}</h3>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div style="text-align: center; padding: 1rem; border: 1px solid #e0e0e0; border-radius: 6px; background-color: #f9f9f9;">
                    <h4 style="color: #333333 !important; margin: 0;">⚠️ Warning Entries</h4>
                    <h3 style="color: orange !important; margin: 0.5rem 0;">{log_data.get('warning_entries', 0)}</h3>
                </div>
                """, unsafe_allow_html=True)
            
            # Log file breakdown (if available)
            if log_data.get('total_log_files', 0) > 0:
                st.markdown('<h4 style="color: #333333 !important; margin: 1.5rem 0 1rem 0;">Recent Log Activity:</h4>', unsafe_allow_html=True)
                
                # Mock log activity data
                log_activity = [
                    {"time": "14:30", "level": "INFO", "message": "Trade executed successfully"},
                    {"time": "14:25", "level": "INFO", "message": "Market data updated"},
                    {"time": "14:20", "level": "WARN", "message": "High memory usage detected"},
                    {"time": "14:15", "level": "INFO", "message": "Strategy analysis completed"},
                    {"time": "14:10", "level": "ERROR", "message": "API rate limit exceeded"}
                ]
                
                for entry in log_activity:
                    level = entry['level']
                    icon = "❌" if level == "ERROR" else "⚠️" if level == "WARN" else "ℹ️"
                    color = "red" if level == "ERROR" else "orange" if level == "WARN" else "blue"
                    
                    st.markdown(f"""
                    <div style="
                        font-size: 0.9rem; 
                        padding: 0.5rem; 
                        margin: 0.25rem 0;
                        background-color: #f5f5f5;
                        border-radius: 4px;
                        color: #333333 !important;
                    ">
                        {icon} <span style="color: #666666 !important;">{entry['time']}</span> 
                        <span style="color: {color} !important; font-weight: bold;">[{level}]</span> 
                        <span style="color: #333333 !important;">{entry['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="padding: 1rem; text-align: center; background-color: #e3f2fd; border-radius: 8px; color: #333333 !important;">
                ℹ️ No log data available
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) 