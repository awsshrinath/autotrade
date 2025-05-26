"""
Centralized Configuration Management System
Loads configuration from YAML/JSON files instead of environment variables
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging


@dataclass
class TradingConfig:
    """Trading configuration data class"""

    # Environment settings
    environment: str = "development"
    paper_trade: bool = True

    # Capital settings
    default_capital: float = 100000
    max_daily_loss: float = 1000
    max_daily_loss_pct: float = 2.0

    # Position sizing limits
    stock_position_limit: float = 0.1
    option_position_limit: float = 0.05
    future_position_limit: float = 0.15

    # Risk management
    margin_utilization_limit: float = 0.8
    max_volatility_threshold: float = 0.05
    min_trade_value: float = 1000

    # API settings
    api_rate_limit: int = 3
    api_timeout: int = 10

    # Monitoring settings
    monitoring_interval: int = 30
    backup_frequency: int = 300
    auto_square_off_time: str = "15:20"

    # Logging settings
    log_level: str = "INFO"

    # Strategy settings
    scalp_config: Dict = None

    # Alert settings
    alerts_email_enabled: bool = False
    alerts_slack_enabled: bool = False
    alerts_webhook_url: str = ""

    def __post_init__(self):
        if self.scalp_config is None:
            self.scalp_config = {
                "min_price": 100,
                "max_price": 120,
                "sl_buffer": 30,
                "target_buffer": 60,
                "quantity": 75,
            }


class ConfigManager:
    """Centralized configuration manager that loads from files"""

    def __init__(self, config_dir: str = None, environment: str = None):
        # Determine config directory
        if config_dir is None:
            self.config_dir = Path(__file__).parent
        else:
            self.config_dir = Path(config_dir)

        # Determine environment
        self.environment = environment or self._detect_environment()

        # Initialize configuration
        self.config = TradingConfig()
        self._load_configuration()

        # Set up logging
        self._setup_logging()

        logging.info(
            f"ConfigManager initialized - Environment: {self.environment}, "
            f"Paper Trade: {self.config.paper_trade}"
        )

    def _detect_environment(self) -> str:
        """Detect environment from various sources"""
        # Check environment variable first (if needed)
        env_var = os.getenv("TRON_ENV", os.getenv("ENVIRONMENT", "")).lower()
        if env_var:
            return env_var

        # Check for environment-specific config files
        for env in ["production", "staging", "development"]:
            if (self.config_dir / f"{env}.yaml").exists():
                return env

        # Default to development
        return "development"

    def _load_configuration(self):
        """Load configuration from files"""
        # Load base configuration
        base_config = (
            self._load_config_file("base.yaml")
            or self._load_config_file("base.json")
            or {}
        )

        # Load environment-specific configuration
        env_config = (
            self._load_config_file(f"{self.environment}.yaml")
            or self._load_config_file(f"{self.environment}.json")
            or {}
        )

        # Load local overrides (for development)
        local_config = (
            self._load_config_file("local.yaml")
            or self._load_config_file("local.json")
            or {}
        )

        # Merge configurations (local overrides env, env overrides base)
        merged_config = {**base_config, **env_config, **local_config}

        # Update configuration object
        self._update_config_from_dict(merged_config)

        logging.info(f"Configuration loaded from: base + {self.environment} + local")

    def _load_config_file(self, filename: str) -> Optional[Dict]:
        """Load configuration from a specific file"""
        filepath = self.config_dir / filename

        if not filepath.exists():
            return None

        try:
            with open(filepath, "r") as f:
                if filename.endswith(".yaml") or filename.endswith(".yml"):
                    return yaml.safe_load(f)
                elif filename.endswith(".json"):
                    return json.load(f)
                else:
                    logging.warning(f"Unsupported config file format: {filename}")
                    return None
        except Exception as e:
            logging.error(f"Error loading config file {filename}: {e}")
            return None

    def _update_config_from_dict(self, config_dict: Dict[str, Any]):
        """Update configuration object from dictionary"""
        for key, value in config_dict.items():
            # Convert camelCase/snake_case to match dataclass fields
            normalized_key = key.lower().replace("-", "_")

            if hasattr(self.config, normalized_key):
                setattr(self.config, normalized_key, value)
            else:
                logging.warning(f"Unknown configuration key: {key}")

    def _setup_logging(self):
        """Set up logging based on configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def _setup_logging(self):
        """Set up logging based on configuration"""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return getattr(self.config, key, default)

    def set(self, key: str, value: Any):
        """Set configuration value (runtime only)"""
        if hasattr(self.config, key):
            setattr(self.config, key, value)
        else:
            raise ValueError(f"Unknown configuration key: {key}")

    def is_paper_trade(self) -> bool:
        """Check if paper trading is enabled"""
        return self.config.paper_trade

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == "development"

    def get_environment_info(self) -> Dict[str, Any]:
        """Get environment information"""
        return {
            "environment": self.environment,
            "paper_trade": self.config.paper_trade,
            "config_dir": str(self.config_dir),
            "log_level": self.config.log_level,
            "default_capital": self.config.default_capital,
            "max_daily_loss": self.config.max_daily_loss,
        }

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration"""
        issues = []
        warnings = []

        # Validate capital settings
        if self.config.default_capital <= 0:
            issues.append("default_capital must be positive")

        if self.config.max_daily_loss <= 0:
            issues.append("max_daily_loss must be positive")

        if self.config.max_daily_loss > self.config.default_capital:
            warnings.append("max_daily_loss is greater than default_capital")

        # Validate position limits
        if not (0 < self.config.stock_position_limit <= 1):
            issues.append("stock_position_limit must be between 0 and 1")

        if not (0 < self.config.option_position_limit <= 1):
            issues.append("option_position_limit must be between 0 and 1")

        if not (0 < self.config.future_position_limit <= 1):
            issues.append("future_position_limit must be between 0 and 1")

        # Validate risk settings
        if not (0 < self.config.margin_utilization_limit <= 1):
            issues.append("margin_utilization_limit must be between 0 and 1")

        if self.config.max_volatility_threshold <= 0:
            issues.append("max_volatility_threshold must be positive")

        # Production-specific validations
        if self.is_production() and self.config.paper_trade:
            warnings.append("Running in production with paper_trade=True")

        if not self.is_production() and not self.config.paper_trade:
            warnings.append("Running in non-production with paper_trade=False")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "environment": self.environment,
            "paper_trade": self.config.paper_trade,
        }

    def save_current_config(self, filename: str = None):
        """Save current configuration to file"""
        if filename is None:
            filename = f"generated_{self.environment}.yaml"

        filepath = self.config_dir / filename

        config_dict = {
            "environment": self.environment,
            "paper_trade": self.config.paper_trade,
            "default_capital": self.config.default_capital,
            "max_daily_loss": self.config.max_daily_loss,
            "max_daily_loss_pct": self.config.max_daily_loss_pct,
            "stock_position_limit": self.config.stock_position_limit,
            "option_position_limit": self.config.option_position_limit,
            "future_position_limit": self.config.future_position_limit,
            "margin_utilization_limit": self.config.margin_utilization_limit,
            "max_volatility_threshold": self.config.max_volatility_threshold,
            "min_trade_value": self.config.min_trade_value,
            "api_rate_limit": self.config.api_rate_limit,
            "api_timeout": self.config.api_timeout,
            "monitoring_interval": self.config.monitoring_interval,
            "backup_frequency": self.config.backup_frequency,
            "auto_square_off_time": self.config.auto_square_off_time,
            "log_level": self.config.log_level,
            "scalp_config": self.config.scalp_config,
            "alerts_email_enabled": self.config.alerts_email_enabled,
            "alerts_slack_enabled": self.config.alerts_slack_enabled,
            "alerts_webhook_url": self.config.alerts_webhook_url,
        }

        try:
            with open(filepath, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

            logging.info(f"Configuration saved to: {filepath}")
            return True
        except Exception as e:
            logging.error(f"Error saving configuration: {e}")
            return False


# Global configuration instance
_config_manager = None


def get_config() -> ConfigManager:
    """Get global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def init_config(config_dir: str = None, environment: str = None) -> ConfigManager:
    """Initialize configuration manager with specific parameters"""
    global _config_manager
    _config_manager = ConfigManager(config_dir, environment)
    return _config_manager


def get_trading_config() -> TradingConfig:
    """Get trading configuration object"""
    return get_config().config


# Convenience functions for backward compatibility
def get_paper_trade() -> bool:
    """Check if paper trading is enabled"""
    return get_config().is_paper_trade()


def get_default_capital() -> float:
    """Get default capital"""
    return get_config().get("default_capital", 100000)


def get_max_daily_loss() -> float:
    """Get maximum daily loss"""
    return get_config().get("max_daily_loss", 1000)


def get_position_limits() -> Dict[str, float]:
    """Get position size limits"""
    config = get_config()
    return {
        "stock": config.get("stock_position_limit", 0.1),
        "option": config.get("option_position_limit", 0.05),
        "future": config.get("future_position_limit", 0.15),
    }
