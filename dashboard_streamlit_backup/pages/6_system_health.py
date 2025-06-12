import streamlit as st
from pathlib import Path
import sys
import pandas as pd

# Add project root for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dashboard.data.system_data_provider import SystemDataProvider

st.set_page_config(layout="wide")

st.title("⚙️ System Health")
st.markdown("<hr/>", unsafe_allow_html=True)

# --- Data Loading ---
@st.cache_data(ttl=10)
def get_health_data():
    provider = SystemDataProvider()
    return {
        "health": provider.get_system_health(),
        "metrics": provider.get_system_metrics(),
        "logs": provider.get_recent_system_logs(limit=100)
    }

data = get_health_data()
health = data.get('health', {})
metrics = data.get('metrics', {})

# --- Health Status & Metrics ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("Component Status")
    status_data = health.get('components', [])
    if status_data:
        st.dataframe(status_data)
    else:
        st.info("Component status not available.")

with col2:
    st.subheader("Resource Usage")
    st.progress(metrics.get('cpu_usage_pct', 0) / 100, text=f"CPU Usage: {metrics.get('cpu_usage_pct', 0)}%")
    st.progress(metrics.get('memory_usage_pct', 0) / 100, text=f"Memory Usage: {metrics.get('memory_usage_pct', 0)}%")
    st.progress(metrics.get('disk_usage_pct', 0) / 100, text=f"Disk Usage: {metrics.get('disk_usage_pct', 0)}%")
    st.metric("API Response Time", f"{metrics.get('api_response_time_ms', 0)} ms")

st.markdown("<hr/>", unsafe_allow_html=True)

# --- System Logs ---
st.subheader("Recent System Logs")
logs_data = data.get('logs', [])
if logs_data:
    st.dataframe(logs_data, height=500)
else:
    st.info("No system logs to display.")
