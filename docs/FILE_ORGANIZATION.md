# TRON Project File Organization Guide

## 📁 Directory Structure Overview

This document outlines the organized file structure for the TRON automated trading platform to ensure maintainability and easy navigation.

## 🏗️ Root Directory Structure

```
TRON/
├── 📁 .cursor/           # Cursor IDE configuration and rules
├── 📁 .github/           # GitHub Actions workflows and configurations
├── 📁 .taskmaster/       # Task Master project management files
├── 📁 agents/           # AI agent configurations
├── 📁 config/           # Application configuration files
├── 📁 dashboard/        # Trading dashboard UI
├── 📁 deployments/      # Kubernetes deployment manifests
├── 📁 docs/             # All documentation (organized by category)
├── 📁 examples/         # Example configurations and code
├── 📁 fixes/            # Bug fixes and patches
├── 📁 futures_trading/  # Futures trading specific code
├── 📁 gpt_runner/       # GPT-powered trading components
├── 📁 logs/             # Log files and monitoring data
├── 📁 mcp/              # MCP (Model Context Protocol) configurations
├── 📁 node_modules/     # Node.js dependencies (auto-generated)
├── 📁 options_trading/  # Options trading specific code
├── 📁 runner/           # Core trading engine and runners
├── 📁 scripts/          # Utility and maintenance scripts
├── 📁 stock_trading/    # Stock trading specific code
├── 📁 strategies/       # Trading strategy implementations
├── 📁 tasks/            # Task Master generated task files
├── 📁 tests/            # Unit and integration tests
├── 📁 tools/            # Development and debugging tools
├── 📁 zerodha_token_service/ # Token management service
├── 📄 .gitignore        # Git ignore rules
├── 📄 Dockerfile        # Container build instructions
├── 📄 entrypoint.sh     # Container entry point script
├── 📄 main.py           # Main application entry point
├── 📄 package.json      # Node.js package configuration
├── 📄 README.md         # Main project documentation
└── 📄 requirements.txt  # Python dependencies
```

## 📚 Documentation Organization (`docs/`)

### Core Documentation
- **README.md** - Main project overview and setup instructions
- **PRODUCTION_READINESS_ANALYSIS.md** - Comprehensive production readiness assessment

### Categorized Documentation
```
docs/
├── 📁 analysis/         # Analysis reports and considerations
│   ├── CLAUDE_CONSIDERATIONS_*.md
│   └── PRODUCTION_READINESS_REPORT.md
├── 📁 deployment/       # Deployment guides and configurations
│   ├── DEPLOYMENT_CHANGES.md
│   └── RUNNER_OPTIONS.md
├── 📁 fixes/           # Bug fix documentation
│   ├── GCS_BUCKET_REGION_FIX.md
│   ├── PAPER_TRADING_CRITICAL_FIXES.md
│   ├── POD_ERROR_FIXES_COMPLETE.md
│   └── URGENT_SERVICE_ACCOUNT_FIX_SUMMARY.md
├── 📁 testing/         # Test files and documentation
│   └── test_*.py files
└── 📁 validation/      # Validation scripts and reports
    ├── validate_*.py files
    └── verify_*.py files
```

## 🔧 Scripts Organization (`scripts/`)

```
scripts/
├── 📁 fixes/           # Bug fix and maintenance scripts
│   ├── claude_lifecycle_fix.py
│   ├── debug_secret_access.py
│   ├── final_error_fixes.py
│   ├── fix_*.py files
│   ├── run_fixed_main.py
│   └── standalone_paper_trader.py
└── 📁 maintenance/     # Regular maintenance scripts
    └── (future maintenance scripts)
```

## 🧪 Testing Organization (`tests/`)

```
tests/
├── test_cognitive_system.py      # Cognitive system tests
├── test_enhanced_logging.py      # Logging system tests
├── test_market_monitor.py        # Market monitoring tests
├── test_runner_integration.py    # Integration tests
├── test_strategy_selector.py     # Strategy selection tests
├── test_trade_manager.py         # Trade management tests
└── test_volatility_regime_logic.py # Volatility regime tests
```

## 📦 Core Application Structure

### Trading Engine (`runner/`)
- **main_runner_combined.py** - Main orchestrator
- **trade_manager.py** - Trade execution
- **enhanced_trade_manager.py** - Advanced trade management
- **risk_governor.py** - Risk management
- **strategy_selector.py** - Strategy selection logic
- **capital_manager.py** - Capital allocation
- **market_monitor.py** - Market data and analysis

### Cognitive System (`runner/`)
- **cognitive_system.py** - Main cognitive engine
- **cognitive_memory.py** - Memory management
- **thought_journal.py** - Decision logging
- **cognitive_state_machine.py** - State management
- **metacognition.py** - Self-analysis
- **gcp_memory_client.py** - GCP persistence

### Enhanced Logging (`runner/enhanced_logging/`)
- **core_logger.py** - Main logging interface
- **gcs_logger.py** - Cloud Storage logging
- **firestore_logger.py** - Firestore logging
- **lifecycle_manager.py** - Log lifecycle management
- **log_types.py** - Structured log types

## 🔒 File Organization Rules

### ✅ KEEP IN ROOT DIRECTORY
- **Essential files only**: main.py, requirements.txt, Dockerfile, README.md
- **Configuration files**: .gitignore, package.json, entrypoint.sh
- **Auto-generated files**: package-lock.json (when needed)

### ❌ AVOID IN ROOT DIRECTORY
- Test files (→ `tests/` or `docs/testing/`)
- Fix scripts (→ `scripts/fixes/`)
- Documentation files (→ `docs/` with appropriate subdirectory)
- Validation scripts (→ `docs/validation/`)
- Analysis reports (→ `docs/analysis/`)
- Log files (→ `logs/`)
- Temporary files (clean up immediately)

### 📋 Future File Placement Guidelines

#### When creating new files, follow these rules:

1. **Documentation** → `docs/[category]/`
   - Analysis reports → `docs/analysis/`
   - Deployment guides → `docs/deployment/`
   - Bug fix docs → `docs/fixes/`
   - Testing docs → `docs/testing/`

2. **Scripts** → `scripts/[purpose]/`
   - Fix scripts → `scripts/fixes/`
   - Maintenance → `scripts/maintenance/`
   - Utilities → `scripts/utilities/`

3. **Tests** → `tests/`
   - All test files with `test_` prefix

4. **Application Code** → Appropriate module directory
   - Trading logic → `runner/`
   - Strategies → `strategies/`
   - Configuration → `config/`

5. **Infrastructure** → `deployments/`
   - Kubernetes manifests
   - Docker configurations

## 🎯 Benefits of This Organization

### ✅ Improved Maintainability
- Clear separation of concerns
- Easy to locate specific types of files
- Reduced root directory clutter

### ✅ Better Collaboration
- Team members can quickly find relevant files
- Consistent file placement across features
- Clear ownership and responsibility

### ✅ Enhanced Development Experience
- Faster navigation in IDEs
- Logical grouping of related files
- Easier code reviews and debugging

### ✅ Production Readiness
- Clean deployment artifacts
- Organized documentation for operations
- Clear separation of development vs production files

## 🔄 Maintenance

This file organization should be maintained by:
1. Following the placement rules for new files
2. Regularly reviewing and cleaning up temporary files
3. Moving misplaced files to appropriate directories
4. Updating this documentation when new categories are needed

---
*File Organization Guide - Updated: December 26, 2024*
*Maintains clean root directory and logical file organization* 