"""
Dashboard Utils Package
Utility functions and classes for the TRON trading dashboard
"""

from dashboard.utils.auth import authenticate_user
from dashboard.utils.config import DashboardConfig
from dashboard.utils.notifications import NotificationManager

__all__ = [
    "authenticate_user",
    "DashboardConfig",
    "NotificationManager"
] 