import streamlit as st
from typing import Dict, Any, List

class PredictiveAlerts:
    def __init__(self, market_monitor):
        self.market_monitor = market_monitor

    def render(self):
        st.subheader("🔮 Predictive Alerts")
        
        alerts = self.market_monitor.get_predictive_alerts()
        
        if not alerts:
            st.info("No predictive alerts at this time.")
            return

        for alert in alerts:
            st.metric(
                label=alert['title'],
                value=alert['value'],
                delta=alert.get('change', ''),
                delta_color=alert.get('color', 'normal')
            )
            st.caption(alert['description'])
            st.divider() 