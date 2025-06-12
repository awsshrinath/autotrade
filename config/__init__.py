"""
Configuration Package for TRON Trading System
Provides centralized configuration management
"""

# Make config a Python package
from .config_manager import (
    ConfigManager,
    TradingConfig,
    get_config,
    get_trading_config,
    init_config,
    get_paper_trade,
    get_default_capital,
    get_max_daily_loss,
    get_position_limits
)

__all__ = [
    'ConfigManager',
    'TradingConfig', 
    'get_config',
    'get_trading_config',
    'init_config',
    'get_paper_trade',
    'get_default_capital',
    'get_max_daily_loss',
    'get_position_limits'
]
