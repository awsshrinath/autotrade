# TRON - Automated Trading System

## Project Overview
TRON is a comprehensive automated trading platform that supports stock, futures, and options trading using the Zerodha API. The system integrates GPT-based decision-making, cloud deployment on Google Kubernetes Engine (GKE), and real-time market analysis with sophisticated risk management.

## Architecture

### Core Components
- **Multi-Asset Trading**: Supports stocks, futures, and options
- **Strategy Engine**: Pluggable trading strategies (VWAP, ORB, Scalp, Range Reversal)
- **GPT Integration**: AI-driven market analysis and self-improvement monitoring
- **Risk Management**: Comprehensive risk governor with daily loss limits
- **Cloud Infrastructure**: GKE Autopilot deployment with CI/CD pipelines
- **Data Storage**: Firestore integration for trade logging and analysis

### Key Modules

#### Trading Runners
- `stock_trading/stock_runner.py` - Stock trading bot
- `options_trading/options_runner.py` - Options trading bot  
- `futures_trading/futures_runner.py` - Futures trading bot
- `runner/main_runner_combined.py` - Combined multi-asset runner

#### Core Runner Components (`runner/`)
- `kiteconnect_manager.py` - Zerodha API integration
- `trade_manager.py` - Trade execution and position management
- `strategy_selector.py` - Dynamic strategy selection based on market conditions
- `risk_governor.py` - Risk management and position sizing
- `market_monitor.py` - Real-time market sentiment analysis
- `gpt_self_improvement_monitor.py` - AI-powered performance analysis
- `firestore_client.py` - Database operations
- `logger.py` - Centralized logging system

#### Trading Strategies (`strategies/` and per-asset folders)
- `base_strategy.py` - Abstract base class for all strategies
- `vwap_strategy.py` - Volume Weighted Average Price strategy
- `opening_range_strategy.py` - Opening Range Breakout (ORB)
- `scalp_strategy.py` - High-frequency scalping strategy
- `range_reversal.py` - Range-bound reversal strategy

#### Utilities (`runner/utils/`)
- `technical_indicators.py` - Technical analysis functions
- `instrument_utils.py` - Market instrument utilities
- `option_utils.py` - Options-specific calculations
- `strike_picker.py` - Options strike selection logic

## Configuration

### Environment Variables
```bash
PAPER_TRADE=true                 # Toggle paper/live trading
DEFAULT_CAPITAL=100000          # Default capital per bot
LOG_LEVEL=INFO                  # Logging verbosity
RUNNER_SCRIPT=runner/main_runner_combined.py  # Entry point script
```

### Trading Configuration (`runner/config.py`)
- Paper trading toggle
- Capital allocation settings
- Scalping strategy parameters
- Logging configuration

## Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run specific trading bot
python stock_trading/stock_runner.py
python options_trading/options_runner.py
python futures_trading/futures_runner.py

# Run combined runner
python runner/main_runner_combined.py

# Main entry point
python main.py
```

### Testing
```bash
# Run all tests
pytest

# Lint code
flake8 .

# Security scan
bandit -r . -c bandit.yaml
```

### Code Quality
- **Linting**: Flake8 configuration in `.flake8`
- **Security**: Bandit scanning with custom `bandit.yaml` config
- **Testing**: Pytest framework with tests in `tests/` directory

## Deployment

### Docker
- **Multi-stage builds** for different trading bots
- **Base image**: `python:3.10-slim`
- **Entry point**: Configurable via `RUNNER_SCRIPT` environment variable
- **Health checks**: Built-in readiness probes

### Kubernetes (GKE Autopilot)
- **Namespace**: `gpt` for all trading components
- **Deployments**: Separate deployments for each trading bot type
- **Service Account**: `gpt-runner-sa` with appropriate GCP permissions
- **Resource limits**: 512Mi memory, 250m CPU requests per pod

### CI/CD Pipeline
1. **Continuous Integration** (`.github/workflows/ci.yml`):
   - Python 3.10 testing environment
   - Dependency installation with FAISS compatibility
   - Flake8 linting
   - Bandit security scanning with fail-on-high configuration
   - Pytest test execution

2. **Continuous Deployment** (`.github/workflows/deploy.yaml`):
   - Multi-image Docker builds for each trading bot
   - Google Artifact Registry push
   - GKE cluster validation
   - Kubernetes manifest deployment
   - Rolling deployment updates

### Infrastructure
- **Container Registry**: Google Artifact Registry (`asia-south1-docker.pkg.dev`)
- **Cluster**: GKE Autopilot in configurable region
- **Images**: 
  - `gpt-runner` - Main combined runner
  - `stock-trader` - Stock trading bot
  - `options-trader` - Options trading bot  
  - `futures-trader` - Futures trading bot

## Strategy System

### Strategy Selection Logic
The system uses `StrategySelector` to dynamically choose strategies based on:
- **Market Sentiment**: VIX levels, pre-market data
- **Bot Type**: Stock/futures/options specific defaults
- **Market Direction**: Bullish/bearish/neutral sentiment analysis

### Strategy Implementation Pattern
All strategies inherit from `BaseStrategy` and implement:
- `find_trade_opportunities(market_data)` - Signal generation
- `should_exit_trade(trade)` - Exit logic

### Risk Management
`RiskGovernor` enforces:
- Maximum daily loss limits (default: ₹500)
- Trade count limits (default: 3 per day)
- Market hours enforcement (cutoff: 15:00)
- Real-time PnL tracking

## Data Flow

1. **Market Data**: Fetched via `MarketDataFetcher` from Zerodha API
2. **Strategy Selection**: `StrategySelector` chooses optimal strategy
3. **Signal Generation**: Selected strategy analyzes market data
4. **Risk Validation**: `RiskGovernor` validates trade parameters
5. **Trade Execution**: `TradeManager` executes via Kite API
6. **Logging**: All activities logged to Firestore and local files
7. **Performance Analysis**: GPT monitor analyzes and suggests improvements

## Key Features

### GPT Integration
- **Self-Improvement**: Automated performance analysis and strategy suggestions
- **Market Analysis**: GPT-powered sentiment analysis
- **Code Enhancement**: Automated bug detection and improvement suggestions

### Multi-Asset Support
- **Stocks**: VWAP-based strategies with technical indicators
- **Options**: Scalping with dynamic strike selection
- **Futures**: Opening range breakout strategies

### Monitoring & Observability
- **Centralized Logging**: Structured JSON logging to files and Firestore
- **Performance Tracking**: PnL tracking, win rate analysis
- **Error Reporting**: Automated error detection and reporting
- **Health Checks**: Kubernetes-ready health endpoints

## File Structure Guide

```
├── main.py                     # Main application entry point
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Container build configuration
├── entrypoint.sh              # Container startup script
├── runner/                     # Core trading infrastructure
│   ├── main_runner_combined.py # Combined multi-asset runner
│   ├── trade_manager.py       # Trade execution engine
│   ├── strategy_selector.py   # Dynamic strategy selection
│   ├── risk_governor.py       # Risk management
│   └── utils/                 # Trading utilities
├── strategies/                 # Base strategy implementations
├── stock_trading/             # Stock-specific trading logic
├── options_trading/           # Options-specific trading logic
├── futures_trading/           # Futures-specific trading logic
├── gpt_runner/               # GPT integration and RAG system
├── deployments/              # Kubernetes manifests
├── .github/workflows/        # CI/CD pipeline definitions
└── tests/                    # Test suite
```

## Security & Compliance

### Secret Management
- **Google Secret Manager** integration for API keys
- **Environment-based** configuration for sensitive data
- **No hardcoded credentials** in source code

### Security Scanning
- **Bandit** static analysis with custom configuration
- **High-severity** issue detection and CI/CD blocking
- **Dependency scanning** for known vulnerabilities

### Access Control
- **Service Account** based GCP authentication
- **Namespace isolation** in Kubernetes
- **Resource limits** and security contexts

## Troubleshooting

### Common Issues
1. **FAISS Installation**: Use specific versions (`faiss-cpu==1.7.4`, `numpy==1.24.4`)
2. **Bandit Failures**: Check `bandit_results.txt` for security issues
3. **Trade Execution**: Verify `PAPER_TRADE` environment variable
4. **API Limits**: Check Zerodha API rate limits and quotas
5. **Memory Issues**: Monitor pod resource usage in GKE

### Debugging
- **Logs Location**: `logs/` directory for local runs
- **Firestore Logs**: Check `trades` and `monitoring` collections
- **Pod Logs**: `kubectl logs -n gpt <pod-name>`
- **Health Checks**: Monitor readiness probe endpoints

### Development Commands
```bash
# Test individual components
python test_kiteconnect_manager.py
python test_openai_manager.py
python test_runners_all.py

# Generate backtest reports
python tools/backtest_report_generator.py

# Run GPT monitoring
python test_gpt_monitor.py
```

This documentation provides a comprehensive guide for understanding, developing, and maintaining the TRON automated trading system.