# TRON Trading System - Project Structure

## 📁 Directory Overview

```
Tron/
├── 📚 docs/                           # Documentation
├── 🚀 deployments/                    # Kubernetes manifests
├── 🧪 tests/                          # Test files
├── 🛠️  tools/                          # Development and security tools
├── ⚙️  config/                         # Configuration files
├── 🏃 runner/                          # Core trading system
├── 📊 dashboard/                       # Trading dashboard (Streamlit)
├── 💹 stock_trading/                   # Stock trading bot
├── 📈 options_trading/                 # Options trading bot
├── 📉 futures_trading/                 # Futures trading bot
├── 🤖 agents/                          # AI agents
├── 📋 strategies/                      # Trading strategies
├── 🧠 gpt_runner/                      # GPT-based functionality
├── 🔌 mcp/                             # Model Context Protocol
├── 🏦 zerodha_token_service/           # Zerodha authentication
├── 📜 scripts/                         # Utility scripts
├── 📝 logs/                            # Local log files
└── 🔧 Core Files                       # Root-level essentials
```

## 📚 Documentation (`docs/`)

| File | Description |
|------|-------------|
| `TRADING_DASHBOARD_DEPLOYMENT.md` | Complete dashboard deployment guide |
| `ENHANCED_LOGGING_SYSTEM.md` | Enhanced logging infrastructure |
| `ENHANCED_TRADING_SYSTEM.md` | Advanced trading system features |
| `PRODUCTION_READINESS_ANALYSIS.md` | Production deployment analysis |
| `CONFIG_GUIDE.md` | Configuration management guide |
| `QUICK_START_GUIDE.md` | Quick setup instructions |
| `LOGGING_SYSTEM_REFACTOR_SUMMARY.md` | Logging system improvements |
| `FIXES_APPLIED.md` | Applied bug fixes and improvements |
| `GITHUB_ACTIONS_FIXES.md` | CI/CD pipeline fixes |
| `CLAUDE.md` | AI assistant integration guide |
| `PROJECT_STRUCTURE.md` | This file - project organization |

## 🚀 Deployments (`deployments/`)

| File | Purpose |
|------|---------|
| `namespace.yaml` | Kubernetes namespace definition |
| `main.yaml` | Main orchestrator deployment |
| `stock-trader.yaml` | Stock trading bot deployment |
| `options-trader.yaml` | Options trading bot deployment |
| `futures-trader.yaml` | Futures trading bot deployment |
| `dashboard.yaml` | Trading dashboard deployment |

## 🧪 Tests (`tests/`)

### Integration Tests
- `test_all_fixes.py` - Comprehensive fix validation
- `test_enhanced_system.py` - Enhanced system testing
- `test_enhanced_logging.py` - Logging system tests
- `test_cognitive_system.py` - AI cognitive system tests
- `test_runner_root.py` - Main runner testing

### Unit Tests
- `test_imports.py` - Import validation
- `test_imports_simple.py` - Simplified import tests
- `test_dashboard_imports.py` - Dashboard-specific imports
- `test_openai_manager.py` - OpenAI integration tests
- `test_kiteconnect_manager.py` - Zerodha API tests
- `test_gpt_monitor.py` - GPT monitoring tests
- `test_runners_all.py` - All runner components

### Component Tests
- `test_cognitive_structure.py` - Cognitive architecture tests
- `test_rag_runner.py` - RAG system tests
- `test_fetch_secrets.py` - Secret management tests

## 🛠️ Tools (`tools/`)

### Security (`tools/security/`)
- `bandit.yaml` - Security vulnerability scanner config
- `bandit_results.txt` - Security scan results
- `bandit_fail_on_high.py` - High-severity issue detection
- `.flake8` - Python code style configuration

### Development (`tools/development/`)
- `main_enhanced.py` - Enhanced development runner
- `self_evolve.py` - Self-improvement automation

## ⚙️ Configuration (`config/`)

- `manage_config.py` - Configuration management utilities
- `gpt-namespace.json` - GPT namespace configuration

## 🏃 Core Trading System (`runner/`)

### Main Components
- `main_runner_combined.py` - Main orchestrator
- `enhanced_logger.py` - Advanced logging system
- `trade_manager.py` - Trade execution management
- `cognitive_system.py` - AI decision-making system

### Logging System (`runner/logging/`)
- `__init__.py` - Logging module exports
- `log_types.py` - Structured data classes
- `firestore_logger.py` - Real-time logging
- `gcs_logger.py` - Bulk archival logging
- `lifecycle_manager.py` - Automated cleanup
- `core_logger.py` - Main logging orchestrator

### Core Services
- `firestore_client.py` - Firestore database client
- `kiteconnect_manager.py` - Zerodha API integration
- `openai_manager.py` - OpenAI API client
- `market_monitor.py` - Market data monitoring
- `strategy_selector.py` - Strategy selection logic

### Cognitive Components
- `cognitive_state_machine.py` - AI state management
- `thought_journal.py` - Decision tracking
- `gpt_self_improvement_monitor.py` - Self-improvement

### Utilities
- `logger.py` - Basic logging utilities
- `common_utils.py` - Shared utilities

## 📊 Trading Dashboard (`dashboard/`)

### Core Application
- `app.py` - Main Streamlit application
- `Dockerfile` - Container configuration
- `requirements.txt` - Python dependencies

### Components (`dashboard/components/`)
- `overview.py` - Dashboard overview page
- `live_trades.py` - Real-time trade monitoring
- `pnl_analysis.py` - Profit/loss analysis
- `system_health.py` - System status monitoring

### Utilities (`dashboard/utils/`)
- Various utility functions for dashboard operations

### Data (`dashboard/data/`)
- Dashboard-specific data files

## 💹 Trading Bots

### Stock Trading (`stock_trading/`)
- `stock_runner.py` - Stock trading bot main runner
- `strategies/` - Stock-specific strategies

### Options Trading (`options_trading/`)
- `options_runner.py` - Options trading bot main runner
- Various options-specific components

### Futures Trading (`futures_trading/`)
- `futures_runner.py` - Futures trading bot main runner
- Futures-specific trading logic

## 🤖 AI Components

### GPT Runner (`gpt_runner/`)
- `gpt_runner.py` - GPT-based analysis
- `rag/` - Retrieval-Augmented Generation system

### RAG System (`gpt_runner/rag/`)
- `faiss_firestore_adapter.py` - Vector database sync
- `rag_worker.py` - RAG processing
- `retriever.py` - Context retrieval
- `embedder.py` - Text embedding
- `vector_store.py` - Vector storage
- `gpt_self_improvement_monitor.py` - AI self-improvement

### Agents (`agents/`)
- AI trading agents and decision-making components

### Strategies (`strategies/`)
- Shared trading strategies across all bots

## 🔌 Model Context Protocol (`mcp/`)

- `context_builder.py` - MCP context building
- `prompt_template.py` - Prompt templates
- `response_parser.py` - Response parsing

## 🏦 Authentication (`zerodha_token_service/`)

- Zerodha authentication and token management services

## 📜 Scripts (`scripts/`)

- Utility scripts for maintenance and deployment

## 🔧 Core Files (Root Level)

| File | Purpose |
|------|---------|
| `main.py` | Legacy main entry point |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Main container configuration |
| `entrypoint.sh` | Container startup script |
| `.gitignore` | Git ignore patterns |
| `README.md` | Project overview |

## 📝 Logs (`logs/`)

- Local development logs (not committed to git)
- Runtime log files for debugging

## 🔄 File Organization Principles

### 1. **Separation of Concerns**
- Each directory has a specific purpose
- Related files are grouped together
- Clear boundaries between components

### 2. **Documentation First**
- All major components have documentation
- README files in each major directory
- Comprehensive guides for deployment and usage

### 3. **Test Coverage**
- Tests organized by type (unit, integration, component)
- Test files mirror the main code structure
- Automated testing for critical components

### 4. **Security and Quality**
- Security tools in dedicated directory
- Code quality configurations centralized
- Automated vulnerability scanning

### 5. **Deployment Ready**
- All deployment configs in deployments/
- Environment-specific configurations
- Kubernetes-native approach

## 🚀 Getting Started

1. **Read the documentation**: Start with `docs/QUICK_START_GUIDE.md`
2. **Set up environment**: Follow `docs/CONFIG_GUIDE.md`
3. **Deploy dashboard**: Use `docs/TRADING_DASHBOARD_DEPLOYMENT.md`
4. **Run tests**: Execute tests from `tests/` directory
5. **Deploy system**: Use configs in `deployments/`

## 🔄 Maintenance

### Regular Tasks
- Review security scan results in `tools/security/`
- Update documentation in `docs/`
- Run test suite from `tests/`
- Monitor logs in `logs/` and GCS buckets

### Development Workflow
1. Make changes in appropriate directories
2. Run tests: `pytest tests/`
3. Update documentation if needed
4. Commit and push (triggers CI/CD)
5. Monitor deployment via GitHub Actions

---

**Last Updated**: 2024-05-30
**Version**: 2.0
**Maintainer**: TRON Trading Team 