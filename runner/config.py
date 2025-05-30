"""
Enhanced Configuration Module
Now uses file-based configuration instead of environment variables
"""

import os
import sys

# Add project root to path for proper imports
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

# Try to import config_manager with fallback
try:
    from config.config_manager import (
        get_config,
        get_trading_config,
        get_paper_trade,
        get_default_capital,
        get_max_daily_loss,
        get_position_limits,
    )
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import config_manager: {e}")
    CONFIG_AVAILABLE = False
    
    # Create fallback functions
    class FallbackConfig:
        paper_trade = True
        default_capital = 100000
        log_level = "INFO"
        scalp_config = {
            "min_price": 100,
            "max_price": 120,
            "sl_buffer": 30,
            "target_buffer": 60,
            "quantity": 75,
        }
        environment = "development"
        max_daily_loss = 1000
        max_daily_loss_pct = 2.0
        stock_position_limit = 0.1
        option_position_limit = 0.05
        future_position_limit = 0.15
        margin_utilization_limit = 0.8
        max_volatility_threshold = 0.05
        min_trade_value = 1000
        api_rate_limit = 3
        api_timeout = 10
        monitoring_interval = 30
        backup_frequency = 300
        auto_square_off_time = "15:20"
        alerts_email_enabled = False
        alerts_slack_enabled = False
        alerts_webhook_url = ""
    
    def get_config():
        return FallbackConfig()
    
    def get_trading_config():
        return FallbackConfig()
    
    def get_paper_trade():
        return True
    
    def get_default_capital():
        return 100000
    
    def get_max_daily_loss():
        return 1000
    
    def get_position_limits():
        return {"stock": 0.1, "option": 0.05, "future": 0.15}

# Initialize configuration
if CONFIG_AVAILABLE:
    _config_manager = get_config()
    _trading_config = get_trading_config()
else:
    _config_manager = get_config()
    _trading_config = get_trading_config()

# Backward compatibility with old config.py interface
PAPER_TRADE = _trading_config.paper_trade
DEFAULT_CAPITAL = _trading_config.default_capital
LOG_LEVEL = _trading_config.log_level
SCALP_CONFIG = _trading_config.scalp_config

# Additional configuration values now available
ENVIRONMENT = _trading_config.environment
MAX_DAILY_LOSS = _trading_config.max_daily_loss
MAX_DAILY_LOSS_PCT = _trading_config.max_daily_loss_pct

# Position limits
STOCK_POSITION_LIMIT = _trading_config.stock_position_limit
OPTION_POSITION_LIMIT = _trading_config.option_position_limit
FUTURE_POSITION_LIMIT = _trading_config.future_position_limit

# Risk management
MARGIN_UTILIZATION_LIMIT = _trading_config.margin_utilization_limit
MAX_VOLATILITY_THRESHOLD = _trading_config.max_volatility_threshold
MIN_TRADE_VALUE = _trading_config.min_trade_value

# API settings
API_RATE_LIMIT = _trading_config.api_rate_limit
API_TIMEOUT = _trading_config.api_timeout

# Monitoring settings
MONITORING_INTERVAL = _trading_config.monitoring_interval
BACKUP_FREQUENCY = _trading_config.backup_frequency
AUTO_SQUARE_OFF_TIME = _trading_config.auto_square_off_time

# Alert settings
ALERTS_EMAIL_ENABLED = _trading_config.alerts_email_enabled
ALERTS_SLACK_ENABLED = _trading_config.alerts_slack_enabled
ALERTS_WEBHOOK_URL = _trading_config.alerts_webhook_url


def get_config_manager():
    """Get the configuration manager instance"""
    return _config_manager


def get_environment_info():
    """Get environment information"""
    return _config_manager.get_environment_info()


def is_paper_trade():
    """Check if paper trading is enabled"""
    return _config_manager.is_paper_trade()


def is_production():
    """Check if running in production"""
    return _config_manager.is_production()


def is_development():
    """Check if running in development"""
    return _config_manager.is_development()


def validate_config():
    """Validate current configuration"""
    return _config_manager.validate_configuration()


def get_strategy_config(strategy_name: str):
    """Get strategy-specific configuration"""
    if strategy_name.lower() == "scalp":
        return SCALP_CONFIG
    else:
        # Return default strategy config
        return {
            "position_size_pct": 0.1,
            "stop_loss_pct": 0.02,
            "target_pct": 0.04,
            "max_positions": 3,
        }


def get_position_limits_dict():
    """Get position limits as dictionary"""
    return {
        "stock": STOCK_POSITION_LIMIT,
        "option": OPTION_POSITION_LIMIT,
        "future": FUTURE_POSITION_LIMIT,
    }


def get_risk_settings():
    """Get risk management settings"""
    return {
        "max_daily_loss": MAX_DAILY_LOSS,
        "max_daily_loss_pct": MAX_DAILY_LOSS_PCT,
        "margin_utilization_limit": MARGIN_UTILIZATION_LIMIT,
        "max_volatility_threshold": MAX_VOLATILITY_THRESHOLD,
        "min_trade_value": MIN_TRADE_VALUE,
        "position_limits": get_position_limits_dict(),
    }


def get_api_settings():
    """Get API settings"""
    return {"rate_limit": API_RATE_LIMIT, "timeout": API_TIMEOUT}


def get_monitoring_settings():
    """Get monitoring settings"""
    return {
        "interval": MONITORING_INTERVAL,
        "backup_frequency": BACKUP_FREQUENCY,
        "auto_square_off_time": AUTO_SQUARE_OFF_TIME,
    }


def save_current_config():
    """Save current configuration to file"""
    return _config_manager.save_current_config()


# Display configuration on import (for debugging)
if is_development():
    print("📊 TRON Configuration Loaded:")
    print(f"   Environment: {ENVIRONMENT}")
    print(f"   Paper Trade: {PAPER_TRADE}")
    print(f"   Default Capital: ₹{DEFAULT_CAPITAL:,}")
    print(f"   Max Daily Loss: ₹{MAX_DAILY_LOSS:,}")
    print(f"   Log Level: {LOG_LEVEL}")

    # Validate configuration
    validation = validate_config()
    if not validation["valid"]:
        print(f"⚠️  Configuration Issues: {validation['issues']}")
    if validation["warnings"]:
        print(f"⚠️  Configuration Warnings: {validation['warnings']}")
