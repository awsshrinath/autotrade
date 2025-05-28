"""
Dashboard Configuration
Configuration settings for the TRON trading dashboard
"""

import os
from typing import Dict, Any


class DashboardConfig:
    """Dashboard configuration class"""
    
    def __init__(self):
        self.version = "1.0.0"
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # Dashboard settings
        self.auto_refresh_interval = int(os.getenv("AUTO_REFRESH_INTERVAL", "30"))
        self.max_chart_points = int(os.getenv("MAX_CHART_POINTS", "100"))
        self.default_timeframe = os.getenv("DEFAULT_TIMEFRAME", "1D")
        
        # Authentication settings
        self.auth_enabled = os.getenv("AUTH_ENABLED", "true").lower() == "true"
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
        
        # Data refresh settings
        self.data_cache_ttl = int(os.getenv("DATA_CACHE_TTL", "60"))  # 1 minute
        self.real_time_updates = os.getenv("REAL_TIME_UPDATES", "true").lower() == "true"
        
        # Display settings
        self.currency_symbol = os.getenv("CURRENCY_SYMBOL", "₹")
        self.decimal_places = int(os.getenv("DECIMAL_PLACES", "2"))
        self.theme = os.getenv("DASHBOARD_THEME", "light")
        
        # Alert settings
        self.alerts_enabled = os.getenv("ALERTS_ENABLED", "true").lower() == "true"
        self.alert_sound = os.getenv("ALERT_SOUND", "true").lower() == "true"
        
        # Performance settings
        self.max_concurrent_requests = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "30"))
        
        # Feature flags
        self.features = {
            "live_trading": os.getenv("FEATURE_LIVE_TRADING", "false").lower() == "true",
            "cognitive_insights": os.getenv("FEATURE_COGNITIVE_INSIGHTS", "true").lower() == "true",
            "advanced_charts": os.getenv("FEATURE_ADVANCED_CHARTS", "true").lower() == "true",
            "risk_monitoring": os.getenv("FEATURE_RISK_MONITORING", "true").lower() == "true",
            "export_data": os.getenv("FEATURE_EXPORT_DATA", "true").lower() == "true"
        }
    
    def get_chart_config(self) -> Dict[str, Any]:
        """Get chart configuration"""
        return {
            "max_points": self.max_chart_points,
            "default_timeframe": self.default_timeframe,
            "auto_refresh": self.real_time_updates,
            "theme": self.theme,
            "currency_symbol": self.currency_symbol,
            "decimal_places": self.decimal_places
        }
    
    def get_auth_config(self) -> Dict[str, Any]:
        """Get authentication configuration"""
        return {
            "enabled": self.auth_enabled,
            "session_timeout": self.session_timeout,
            "require_https": self.environment == "production"
        }
    
    def get_performance_config(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return {
            "cache_ttl": self.data_cache_ttl,
            "max_concurrent_requests": self.max_concurrent_requests,
            "request_timeout": self.request_timeout,
            "real_time_updates": self.real_time_updates
        }
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """Check if a feature is enabled"""
        return self.features.get(feature_name, False)
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            "version": self.version,
            "environment": self.environment,
            "debug": self.debug,
            "auto_refresh_interval": self.auto_refresh_interval,
            "chart_config": self.get_chart_config(),
            "auth_config": self.get_auth_config(),
            "performance_config": self.get_performance_config(),
            "features": self.features,
            "alerts_enabled": self.alerts_enabled,
            "alert_sound": self.alert_sound
        } 