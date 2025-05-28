"""
Dashboard Utils Package
Utility functions and classes for the TRON trading dashboard
"""

from .auth import authenticate_user
from .config import DashboardConfig
from .notifications import NotificationManager

__all__ = [
    "authenticate_user",
    "DashboardConfig",
    "NotificationManager"
] 