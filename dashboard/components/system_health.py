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
        st.markdown('<h1 style="color: #6c757d; text-align: center; margin-bottom: 2rem;">⚙️ System Health Monitor</h1>', unsafe_allow_html=True)
        st.markdown("**Real-time system monitoring and health status tracking**")
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
        st.subheader("🎯 Overall System Status")
        
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
                padding: 1rem; 
                border: 2px solid {status_color}; 
                border-radius: 10px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                color: #333333 !important;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            ">
                <h2 style="margin: 0; font-size: 2rem;">{status_icon}</h2>
                <h3 style="color: {status_color} !important; margin: 0.5rem 0; font-weight: 600;">{str(status).upper()}</h3>
                <p style="color: #555555 !important; margin: 0; font-size: 0.9rem;">System Status</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            uptime = status_data.get('uptime_hours', 0)
            st.metric(
                "⏱️ Uptime",
                f"{uptime:.1f} hours",
                f"{uptime/24:.1f} days"
            )
        
        with col3:
            critical_failures = status_data.get('critical_failures', 0)
            st.metric(
                "🚨 Critical Issues",
                critical_failures,
                "Active" if critical_failures > 0 else "None"
            )
        
        with col4:
            system_ready = status_data.get('system_ready', False)
            ready_icon = "✅" if system_ready else "❌"
            st.metric(
                "🎯 System Ready",
                f"{ready_icon} {'Yes' if system_ready else 'No'}",
                "Trading Ready"
            )
    
    def _render_health_checks(self):
        """Render detailed health checks"""
        st.subheader("🔍 Health Checks")
        
        # Get health check data
        health_checks = self.system_data.get_health_checks()
        
        # Debug info (temporarily visible)
        with st.expander("🐛 Debug Health Check Data", expanded=False):
            st.write(f"Health checks type: {type(health_checks)}")
            st.write(f"Health checks length: {len(health_checks) if health_checks else 'None'}")
            st.json(health_checks)
        
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
                    elif status == 'degraded':
                        status_color = "orange"
                        status_icon = "⚠️"
                        status_bg = "#fff3cd"
                    else:
                        status_color = "red"
                        status_icon = "❌"
                        status_bg = "#f8d7da"
                    
                    # Critical indicator
                    critical_badge = " 🔴 CRITICAL" if is_critical and status != 'healthy' else ""
                    
                    # Format details for display
                    details_text = ""
                    if details:
                        for key, value in details.items():
                            if isinstance(value, (int, float)):
                                if 'usage' in key.lower():
                                    details_text += f"<small style='color: #555555 !important; display: block; margin: 2px 0;'><strong style='color: #555555 !important;'>{key.replace('_', ' ').title()}:</strong> {value:.1f}%</small>"
                                elif 'time' in key.lower():
                                    details_text += f"<small style='color: #555555 !important; display: block; margin: 2px 0;'><strong style='color: #555555 !important;'>{key.replace('_', ' ').title()}:</strong> {value:.0f}ms</small>"
                                else:
                                    details_text += f"<small style='color: #555555 !important; display: block; margin: 2px 0;'><strong style='color: #555555 !important;'>{key.replace('_', ' ').title()}:</strong> {value}</small>"
                            elif isinstance(value, str):
                                details_text += f"<small style='color: #555555 !important; display: block; margin: 2px 0;'><strong style='color: #555555 !important;'>{key.replace('_', ' ').title()}:</strong> {value}</small>"
                    
                    st.markdown(f"""
                    <div style="
                        background-color: {status_bg};
                        padding: 1rem;
                        border-radius: 8px;
                        border-left: 4px solid {status_color};
                        margin-bottom: 1rem;
                        min-height: 120px;
                        color: #333333 !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    ">
                        <h4 style="margin: 0 0 10px 0; color: {status_color} !important; font-weight: 600; font-size: 1.1rem;">
                            {status_icon} {service.replace('_', ' ').title()}{critical_badge}
                        </h4>
                        <p style="margin: 5px 0; color: #333333 !important; font-size: 0.9rem;"><strong style="color: #333333 !important;">Status:</strong> 
                           <span style="color: {status_color} !important; font-weight: bold;">{str(status).upper()}</span>
                        </p>
                        <p style="margin: 5px 0; color: #333333 !important; font-size: 0.9rem;"><strong style="color: #333333 !important;">Response:</strong> {response_time*1000:.0f}ms</p>
                        <div style="color: #555555 !important; font-size: 0.85rem;">
                            {details_text}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("⚠️ Health check data is not available. System may be starting up or experiencing connectivity issues.")
    
    def _render_resource_usage(self):
        """Render system resource usage"""
        st.subheader("📊 Resource Usage")
        
        # Get system metrics
        metrics = self.system_data.get_system_metrics()
        
        # CPU Usage
        cpu_usage = metrics.get('cpu_usage', 0)
        cpu_color = "red" if cpu_usage > 80 else "orange" if cpu_usage > 60 else "green"
        st.metric("💻 CPU Usage", f"{cpu_usage:.1f}%")
        st.progress(cpu_usage/100)
        
        # Memory Usage
        memory_usage = metrics.get('memory_usage', 0)
        memory_available = metrics.get('memory_available_gb', 0)
        memory_color = "red" if memory_usage > 85 else "orange" if memory_usage > 70 else "green"
        st.metric("🧠 Memory Usage", f"{memory_usage:.1f}%", f"{memory_available:.1f}GB available")
        st.progress(memory_usage/100)
        
        # Disk Usage
        disk_usage = metrics.get('disk_usage', 0)
        disk_color = "red" if disk_usage > 90 else "orange" if disk_usage > 75 else "green"
        st.metric("💾 Disk Usage", f"{disk_usage:.1f}%")
        st.progress(disk_usage/100)
        
        # Network Connections
        network_connections = metrics.get('network_connections', 0)
        st.metric("🌐 Network Connections", network_connections)
    
    def _render_service_status(self):
        """Render individual service status"""
        st.subheader("🔧 Service Status")
        
        # Get service status
        services = self.system_data.get_service_status()
        
        if services:
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
                
                # Display service with proper spacing and clear status
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"{icon} **{service_name.replace('_', ' ').title()}**")
                
                with col2:
                    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{status}</span>", unsafe_allow_html=True)
                
                with col3:
                    st.markdown(f"<span style='color: {color}; font-weight: bold;'>{health}</span>", unsafe_allow_html=True)
                    
                # Add small spacing between services
                st.markdown("---")
        else:
            st.info("No service status data available")
    
    def _render_performance_metrics(self):
        """Render performance metrics"""
        st.subheader("⚡ Performance Metrics")
        
        # Get performance data
        perf_data = self.system_data.get_performance_metrics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            api_time = perf_data.get('api_response_time_ms', 0)
            st.metric("🔗 API Response", f"{api_time}ms")
        
        with col2:
            db_time = perf_data.get('database_query_time_ms', 0)
            st.metric("🗄️ Database Query", f"{db_time}ms")
        
        with col3:
            trade_time = perf_data.get('trade_execution_time_ms', 0)
            st.metric("📈 Trade Execution", f"{trade_time}ms")
        
        with col4:
            uptime_pct = perf_data.get('uptime_pct', 0)
            st.metric("⏰ Uptime", f"{uptime_pct:.1f}%")
        
        # Performance trends (mock data for visualization)
        st.subheader("📈 Performance Trends")
        
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
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_recent_alerts(self):
        """Render recent system alerts"""
        st.subheader("🚨 Recent Alerts")
        
        # Get alerts
        alerts = self.system_data.get_alerts()
        
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
                elif alert_type == 'warning':
                    icon = "🟡"
                    color = "orange"
                else:
                    icon = "🔵"
                    color = "blue"
                
                # Format timestamp
                try:
                    alert_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = alert_time.strftime('%H:%M:%S')
                except:
                    time_str = "Unknown"
                
                st.markdown(f"""
                <div style="padding: 0.5rem; margin: 0.25rem 0; border-left: 3px solid {color}; background-color: rgba(255,255,255,0.1);">
                    {icon} <strong>{time_str}</strong> - {message}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.success("✅ No recent alerts")
    
    def _render_log_summary(self):
        """Render log summary"""
        st.subheader("📋 Log Summary")
        
        # Get log summary
        log_data = self.system_data.get_log_summary()
        
        if log_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📁 Log Files", log_data.get('total_log_files', 0))
                st.metric("📝 Total Entries", log_data.get('total_entries', 0))
            
            with col2:
                st.metric("❌ Error Entries", log_data.get('error_entries', 0))
                st.metric("⚠️ Warning Entries", log_data.get('warning_entries', 0))
            
            # Log file breakdown (if available)
            if log_data.get('total_log_files', 0) > 0:
                st.write("**Recent Log Activity:**")
                
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
                    <div style="font-size: 0.8rem; padding: 0.25rem; margin: 0.1rem 0;">
                        {icon} <span style="color: gray;">{entry['time']}</span> 
                        <span style="color: {color};">[{level}]</span> {entry['message']}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("No log data available") 