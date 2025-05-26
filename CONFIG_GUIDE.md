# 📊 TRON Configuration Management Guide

## Overview

TRON now uses a **file-based configuration system** instead of environment variables. This provides better organization, version control, and environment management.

## 🏗️ Configuration Structure

```
config/
├── base.yaml           # Common settings for all environments
├── development.yaml    # Development environment settings  
├── staging.yaml        # Staging environment settings
├── production.yaml     # Production environment settings
├── local.yaml         # Local overrides (gitignored)
└── local.yaml.example # Template for local config
```

## 🔧 Configuration Hierarchy

Settings are loaded in order of precedence:

1. **Base config** (`base.yaml`) - Default values
2. **Environment config** (`{environment}.yaml`) - Environment-specific overrides
3. **Local config** (`local.yaml`) - Personal/local overrides

## 📝 Configuration Files

### Base Configuration (`config/base.yaml`)

Contains default settings shared across all environments:

```yaml
# Environment Settings
environment: "development"
paper_trade: true

# Capital Management
default_capital: 100000
max_daily_loss_pct: 2.0
min_trade_value: 1000

# Position Size Limits
stock_position_limit: 0.10    # 10% max per stock
option_position_limit: 0.05   # 5% max per option
future_position_limit: 0.15   # 15% max per future

# Risk Management
margin_utilization_limit: 0.80  # 80% max margin
max_volatility_threshold: 0.05  # 5% circuit breaker

# API Settings
api_rate_limit: 3              # requests per second
api_timeout: 10                # seconds

# Monitoring
monitoring_interval: 30        # seconds
auto_square_off_time: "15:20"

# Logging
log_level: "INFO"
```

### Development Configuration (`config/development.yaml`)

Safe settings for development and testing:

```yaml
environment: "development"
paper_trade: true  # Always paper trade in dev

# Conservative settings
default_capital: 100000
max_daily_loss: 1000           # ₹1,000 max loss
stock_position_limit: 0.05     # 5% max per stock
margin_utilization_limit: 0.30 # 30% max margin
log_level: "DEBUG"             # Verbose logging
```

### Staging Configuration (`config/staging.yaml`)

Production-like settings with paper trading:

```yaml
environment: "staging"
paper_trade: true  # Always paper trade in staging

# Production-like amounts
default_capital: 500000
max_daily_loss: 10000          # ₹10,000 max loss
margin_utilization_limit: 0.60 # 60% max margin
monitoring_interval: 60        # 1 minute monitoring
```

### Production Configuration (`config/production.yaml`)

Live trading settings with maximum safety:

```yaml
environment: "production"
paper_trade: false  # LIVE TRADING

# Production amounts
default_capital: 1000000       # ₹10 Lakh
max_daily_loss: 50000          # ₹50,000 max loss
margin_utilization_limit: 0.80 # 80% max margin
monitoring_interval: 30        # 30 seconds monitoring

# Enhanced features
alerts_email_enabled: true
alerts_slack_enabled: true
```

### Local Configuration (`config/local.yaml`)

Personal overrides for local development:

```yaml
# Override any setting for local development
paper_trade: true
default_capital: 50000
max_daily_loss: 500
log_level: "DEBUG"

# Personal settings
development:
  mock_market_data: true
  enable_debug_mode: true
```

## 🚀 Usage

### 1. Basic Usage

The system automatically detects the environment and loads appropriate configuration:

```python
# Configuration is loaded automatically
from runner import config

print(f"Environment: {config.ENVIRONMENT}")
print(f"Paper Trade: {config.PAPER_TRADE}")
print(f"Capital: ₹{config.DEFAULT_CAPITAL:,}")
```

### 2. Environment Detection

Environment is detected in this order:

1. `TRON_ENV` environment variable
2. `ENVIRONMENT` environment variable  
3. Presence of environment-specific config files
4. Defaults to `development`

### 3. Manual Environment Setting

```python
from config.config_manager import init_config

# Initialize with specific environment
config_manager = init_config(environment="production")
```

### 4. Configuration Management CLI

Use the management script for configuration operations:

```bash
# Show current configuration
python manage_config.py show

# Validate configuration
python manage_config.py validate

# Test all environments
python manage_config.py test

# Switch environment
python manage_config.py switch production

# Create local config file
python manage_config.py init-local

# Export configuration
python manage_config.py export production --format yaml
```

## 🔍 Configuration Validation

### Automatic Validation

Configuration is automatically validated on startup:

```python
from runner.config import validate_config

validation = validate_config()
if not validation['valid']:
    print(f"Issues: {validation['issues']}")
```

### Manual Validation

```bash
# Validate current config
python manage_config.py validate

# Validate specific environment
python manage_config.py validate --env production

# Test all environments
python manage_config.py test
```

### Validation Rules

The system validates:

- **Value ranges**: Capital, limits, timeouts within reasonable bounds
- **Type checking**: Ensure numeric values are numbers
- **Business logic**: Daily loss ≤ capital, position limits ≤ 100%
- **Environment consistency**: Production settings are appropriate
- **Critical settings**: Values that could break the system

## 🛠️ Advanced Usage

### 1. Accessing Configuration in Code

```python
from config.config_manager import get_trading_config, get_config

# Get configuration object
config = get_trading_config()
print(f"Paper trade: {config.paper_trade}")

# Get configuration manager
config_manager = get_config()
print(f"Environment: {config_manager.environment}")

# Check environment
if config_manager.is_production():
    print("Running in production!")
```

### 2. Runtime Configuration Changes

```python
from config.config_manager import get_config

config_manager = get_config()

# Change setting at runtime (not saved to file)
config_manager.set('paper_trade', True)

# Save current config to file
config_manager.save_current_config('my_config.yaml')
```

### 3. Configuration Comparison

```python
from config.config_validator import ConfigValidator

validator = ConfigValidator()

# Compare two configurations
dev_config = ConfigManager(environment="development").config
prod_config = ConfigManager(environment="production").config

comparison = validator.compare_configs(dev_config, prod_config)
print(f"Differences: {comparison['differences']}")
```

## 🔄 Migration from Environment Variables

### Old Way (Environment Variables)
```bash
export PAPER_TRADE=true
export DEFAULT_CAPITAL=100000
export MAX_DAILY_LOSS=1000
python main.py
```

### New Way (Configuration Files)
```bash
# Configuration automatically loaded from files
python main.py

# Or specify environment
TRON_ENV=production python main.py
```

### Backward Compatibility

All existing code continues to work:

```python
# These still work exactly the same
from runner import config

print(config.PAPER_TRADE)
print(config.DEFAULT_CAPITAL)
print(config.SCALP_CONFIG)
```

## 🚨 Security Considerations

### 1. Secret Management

**DO NOT** put sensitive data in configuration files:

```yaml
# ❌ DON'T DO THIS
zerodha_api_key: "your_api_key"
zerodha_api_secret: "your_secret"

# ✅ DO THIS INSTEAD
# Keep using Google Secret Manager for sensitive data
```

### 2. File Permissions

Protect configuration files:

```bash
# Make config files read-only
chmod 644 config/*.yaml

# Keep local.yaml out of version control
echo "config/local.yaml" >> .gitignore
```

### 3. Production Safety

```yaml
# Production configuration should always be reviewed
environment: "production"
paper_trade: false  # Set to true for safety testing

# Use conservative limits
max_daily_loss: 50000
margin_utilization_limit: 0.80
```

## 🐛 Troubleshooting

### Common Issues

1. **"No configuration found"**
   ```bash
   # Ensure config directory exists with base.yaml
   ls config/base.yaml
   ```

2. **"Invalid configuration"**
   ```bash
   # Validate configuration
   python manage_config.py validate
   ```

3. **"Environment not detected"**
   ```bash
   # Set environment explicitly
   TRON_ENV=development python main.py
   ```

4. **"YAML parsing error"**
   ```bash
   # Check YAML syntax
   python -c "import yaml; yaml.safe_load(open('config/base.yaml'))"
   ```

### Debug Configuration Loading

```python
from config.config_manager import get_config

config_manager = get_config()
env_info = config_manager.get_environment_info()
print(f"Config loaded from: {env_info}")

# Validate configuration
validation = config_manager.validate_configuration()
if not validation['valid']:
    print(f"Issues: {validation['issues']}")
```

## 📊 Configuration Reference

### Complete Settings List

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `environment` | string | "development" | Environment name |
| `paper_trade` | boolean | true | Enable paper trading |
| `default_capital` | float | 100000 | Starting capital (₹) |
| `max_daily_loss` | float | 1000 | Max daily loss (₹) |
| `max_daily_loss_pct` | float | 2.0 | Max daily loss (%) |
| `stock_position_limit` | float | 0.10 | Max % per stock position |
| `option_position_limit` | float | 0.05 | Max % per option position |
| `future_position_limit` | float | 0.15 | Max % per future position |
| `margin_utilization_limit` | float | 0.80 | Max margin utilization |
| `max_volatility_threshold` | float | 0.05 | Volatility circuit breaker |
| `min_trade_value` | float | 1000 | Minimum trade value (₹) |
| `api_rate_limit` | int | 3 | API requests per second |
| `api_timeout` | int | 10 | API timeout (seconds) |
| `monitoring_interval` | int | 30 | Health check interval (sec) |
| `backup_frequency` | int | 300 | Backup frequency (sec) |
| `auto_square_off_time` | string | "15:20" | Auto square off time |
| `log_level` | string | "INFO" | Logging level |

### Environment Defaults

| Setting | Development | Staging | Production |
|---------|-------------|---------|------------|
| `paper_trade` | true | true | false |
| `default_capital` | 100,000 | 500,000 | 1,000,000 |
| `max_daily_loss` | 1,000 | 10,000 | 50,000 |
| `stock_position_limit` | 5% | 8% | 10% |
| `margin_utilization_limit` | 30% | 60% | 80% |
| `log_level` | DEBUG | INFO | INFO |
| `monitoring_interval` | 120s | 60s | 30s |

This configuration system provides **flexibility, safety, and maintainability** for managing TRON across different environments! 🚀