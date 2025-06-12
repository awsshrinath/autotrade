"""
Notifications Manager
Handles alerts and notifications for the dashboard
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class NotificationManager:
    """Manages notifications and alerts for the dashboard"""
    
    def __init__(self):
        self.alerts_cache = []
        self.max_alerts = 100
    
    def add_alert(self, alert_type: str, message: str, severity: str = "medium") -> None:
        """
        Add a new alert
        
        Args:
            alert_type: Type of alert (info, warning, critical)
            message: Alert message
            severity: Severity level (low, medium, high)
        """
        alert = {
            'id': len(self.alerts_cache) + 1,
            'type': alert_type,
            'message': message,
            'severity': severity,
            'timestamp': datetime.now().isoformat(),
            'read': False
        }
        
        self.alerts_cache.append(alert)
        
        # Keep only the most recent alerts
        if len(self.alerts_cache) > self.max_alerts:
            self.alerts_cache = self.alerts_cache[-self.max_alerts:]
    
    def get_recent_alerts(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent alerts
        
        Args:
            limit: Maximum number of alerts to return
            
        Returns:
            List of recent alerts
        """
        # Return most recent alerts first
        return sorted(self.alerts_cache, key=lambda x: x['timestamp'], reverse=True)[:limit]
    
    def get_unread_alerts(self) -> List[Dict[str, Any]]:
        """Get unread alerts"""
        return [alert for alert in self.alerts_cache if not alert['read']]
    
    def mark_alert_read(self, alert_id: int) -> bool:
        """
        Mark an alert as read
        
        Args:
            alert_id: ID of the alert to mark as read
            
        Returns:
            True if alert was found and marked as read
        """
        for alert in self.alerts_cache:
            if alert['id'] == alert_id:
                alert['read'] = True
                return True
        return False
    
    def clear_old_alerts(self, hours: int = 24) -> int:
        """
        Clear alerts older than specified hours
        
        Args:
            hours: Number of hours to keep alerts
            
        Returns:
            Number of alerts cleared
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        initial_count = len(self.alerts_cache)
        
        self.alerts_cache = [
            alert for alert in self.alerts_cache
            if datetime.fromisoformat(alert['timestamp']) > cutoff_time
        ]
        
        return initial_count - len(self.alerts_cache)
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by type and severity"""
        summary = {
            'total': len(self.alerts_cache),
            'unread': len(self.get_unread_alerts()),
            'by_type': {},
            'by_severity': {}
        }
        
        for alert in self.alerts_cache:
            # Count by type
            alert_type = alert['type']
            summary['by_type'][alert_type] = summary['by_type'].get(alert_type, 0) + 1
            
            # Count by severity
            severity = alert['severity']
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
        
        return summary
    
    def create_trade_alert(self, trade_data: Dict[str, Any]) -> None:
        """Create alert for trade events"""
        symbol = trade_data.get('symbol', 'Unknown')
        action = trade_data.get('action', 'unknown')
        pnl = trade_data.get('pnl', 0)
        
        if action == 'entry':
            message = f"New position opened: {symbol}"
            alert_type = "info"
            severity = "low"
        elif action == 'exit':
            if pnl > 0:
                message = f"Profitable exit: {symbol} (+₹{pnl:,.2f})"
                alert_type = "info"
                severity = "low"
            else:
                message = f"Loss exit: {symbol} (-₹{abs(pnl):,.2f})"
                alert_type = "warning"
                severity = "medium"
        elif action == 'stop_loss':
            message = f"Stop loss hit: {symbol} (-₹{abs(pnl):,.2f})"
            alert_type = "warning"
            severity = "high"
        else:
            message = f"Trade event: {symbol} - {action}"
            alert_type = "info"
            severity = "low"
        
        self.add_alert(alert_type, message, severity)
    
    def create_system_alert(self, system_data: Dict[str, Any]) -> None:
        """Create alert for system events"""
        event_type = system_data.get('event_type', 'unknown')
        message = system_data.get('message', 'System event occurred')
        
        if event_type == 'high_cpu':
            alert_type = "warning"
            severity = "medium"
        elif event_type == 'high_memory':
            alert_type = "critical"
            severity = "high"
        elif event_type == 'service_down':
            alert_type = "critical"
            severity = "high"
        elif event_type == 'api_error':
            alert_type = "warning"
            severity = "medium"
        else:
            alert_type = "info"
            severity = "low"
        
        self.add_alert(alert_type, message, severity)
    
    def create_risk_alert(self, risk_data: Dict[str, Any]) -> None:
        """Create alert for risk events"""
        risk_type = risk_data.get('risk_type', 'unknown')
        value = risk_data.get('value', 0)
        threshold = risk_data.get('threshold', 0)
        
        if risk_type == 'drawdown':
            message = f"High drawdown detected: {value:.2f}% (threshold: {threshold:.2f}%)"
            alert_type = "critical"
            severity = "high"
        elif risk_type == 'var_breach':
            message = f"VaR threshold breached: ₹{value:,.0f} (limit: ₹{threshold:,.0f})"
            alert_type = "warning"
            severity = "high"
        elif risk_type == 'concentration':
            message = f"High concentration risk: {value:.1f}% in single position"
            alert_type = "warning"
            severity = "medium"
        else:
            message = f"Risk alert: {risk_type} - {value}"
            alert_type = "warning"
            severity = "medium"
        
        self.add_alert(alert_type, message, severity) 