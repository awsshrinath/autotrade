# Cursor IDE Configuration for TRON Trading System

## Project Overview
TRON is a sophisticated automated trading platform with multi-asset support (stocks, options, futures) featuring GPT-powered AI decision making, cloud deployment on GKE, and comprehensive risk management.

## IDE Setup Instructions

### 1. Python Environment
```bash
# Install required Python version
python --version  # Should be 3.10+

# Install dependencies
pip install -r requirements.txt

# For FAISS compatibility issues:
pip install faiss-cpu==1.7.4 numpy==1.24.4
```

### 2. Environment Variables
Create `.env` file in project root:
```bash
# Trading Configuration
PAPER_TRADE=true
DEFAULT_CAPITAL=100000
LOG_LEVEL=INFO
RUNNER_SCRIPT=runner/main_runner_combined.py

# Google Cloud Configuration (for local development)
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GCP_PROJECT_ID=your-project-id
GCP_REGION=asia-south1

# Zerodha API (for local testing)
KITE_API_KEY=your-api-key
KITE_API_SECRET=your-api-secret
```

### 3. Cursor Extensions Recommendations
Install these extensions for optimal development experience:

#### Essential Extensions
- **Python** - Python IntelliSense and debugging
- **Pylance** - Advanced Python language server
- **Python Docstring Generator** - Auto-generate docstrings
- **GitLens** - Enhanced Git capabilities
- **Thunder Client** - API testing
- **YAML** - YAML language support for Kubernetes manifests

#### Cloud & DevOps Extensions
- **Kubernetes** - Kubernetes manifest support and cluster management
- **Docker** - Container development support
- **Google Cloud Code** - GCP integration
- **GitHub Actions** - CI/CD workflow support

#### Code Quality Extensions
- **Black Formatter** - Python code formatting
- **Flake8** - Python linting
- **Bandit** - Security linting for Python
- **autoDocstring** - Automatic docstring generation

### 4. Cursor Settings Configuration
Add to your Cursor settings.json:

```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.linting.banditEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "files.exclude": {
        "**/__pycache__": true,
        "**/*.pyc": true,
        "**/node_modules": true,
        "**/.git": true,
        "**/.DS_Store": true,
        "**/logs/*.log": true,
        "**/logs/*.jsonl": true
    },
    "python.analysis.extraPaths": [
        "./",
        "./runner",
        "./gpt_runner",
        "./strategies"
    ],
    "kubernetes.defaultNamespace": "gpt",
    "yaml.schemas": {
        "kubernetes": "deployments/*.yaml"
    }
}
```

### 5. Launch Configuration
Create `.vscode/launch.json` for debugging:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Main Runner Combined",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/runner/main_runner_combined.py",
            "cwd": "${workspaceFolder}",
            "env": {
                "PAPER_TRADE": "true",
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Stock Trading Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/stock_trading/stock_runner.py",
            "cwd": "${workspaceFolder}",
            "env": {
                "PAPER_TRADE": "true",
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Options Trading Bot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/options_trading/options_runner.py",
            "cwd": "${workspaceFolder}",
            "env": {
                "PAPER_TRADE": "true",
                "PYTHONPATH": "${workspaceFolder}"
            },
            "console": "integratedTerminal"
        },
        {
            "name": "Test All Runners",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/test_runners_all.py",
            "cwd": "${workspaceFolder}",
            "console": "integratedTerminal"
        }
    ]
}
```

### 6. Code Navigation Shortcuts

#### Key File Patterns
- **Main Entry Points**: `main.py`, `runner/main_runner_combined.py`
- **Trading Bots**: `*_trading/*_runner.py`
- **Strategies**: `strategies/*.py`, `*_trading/strategies/*.py`
- **Core Runner**: `runner/*.py`
- **GPT/RAG**: `gpt_runner/`, `gpt_runner/rag/`
- **Configuration**: `config/*.yaml`
- **Deployments**: `deployments/*.yaml`
- **Tests**: `test_*.py`, `tests/*.py`

#### Important Directories Structure
```
TRON/
├── main.py                     # Entry point
├── runner/                     # Core trading infrastructure
│   ├── main_runner_combined.py # Main orchestrator
│   ├── trade_manager.py        # Trade execution
│   ├── strategy_selector.py    # Strategy selection
│   ├── risk_governor.py        # Risk management
│   └── utils/                  # Trading utilities
├── *_trading/                  # Asset-specific bots
│   ├── *_runner.py            # Bot entry points
│   └── strategies/            # Asset-specific strategies
├── strategies/                 # Base strategy implementations
├── gpt_runner/                # GPT integration
│   └── rag/                   # RAG system for AI learning
├── config/                    # Configuration files
├── deployments/               # Kubernetes manifests
└── tests/                     # Test suite
```

### 7. Development Workflow

#### Local Development
```bash
# Run individual components
python main.py
python runner/main_runner_combined.py
python stock_trading/stock_runner.py

# Run tests
pytest
python test_runners_all.py

# Lint and format
flake8 .
black .
bandit -r . -c bandit.yaml
```

#### Debugging Tips
1. **Set PAPER_TRADE=true** for safe testing
2. **Use integrated terminal** for real-time logging
3. **Check logs/ directory** for detailed execution logs
4. **Monitor Firestore** for strategy plans and trade data
5. **Use breakpoints** in strategy selection and trade execution logic

#### Docker Development
```bash
# Build locally
docker build -t tron-local .

# Run with environment
docker run -e PAPER_TRADE=true -e RUNNER_SCRIPT=runner/main_runner_combined.py tron-local
```

#### Kubernetes Development
```bash
# Apply to local cluster
kubectl apply -f deployments/

# Check logs
kubectl logs -f deployment/main-runner -n gpt

# Port forward for debugging
kubectl port-forward service/main-runner 8080:80 -n gpt
```

### 8. Code Quality Configuration

#### .flake8 Configuration
Already configured in project root with appropriate line length and exclusions.

#### Bandit Security Configuration
Custom `bandit.yaml` configured to skip test files and focus on security issues.

#### Git Hooks (Optional)
```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Manual run
pre-commit run --all-files
```

### 9. AI/GPT Development

#### RAG System Development
- **Vector Store**: `gpt_runner/rag/vector_store.py`
- **Embeddings**: `gpt_runner/rag/embedder.py`
- **Retrieval**: `gpt_runner/rag/retriever.py`
- **Self-Improvement**: `gpt_runner/rag/gpt_self_improvement_monitor.py`

#### Strategy Development
- **Base Class**: `strategies/base_strategy.py`
- **VWAP Strategy**: `strategies/vwap_strategy.py`
- **ORB Strategy**: `strategies/opening_range_strategy.py`
- **Scalping**: `strategies/scalp_strategy.py`

### 10. Troubleshooting

#### Common Issues
1. **FAISS Import Errors**: Use specific versions (`faiss-cpu==1.7.4`)
2. **Package Structure**: Ensure `__init__.py` files exist in `gpt_runner/rag/`
3. **Import Paths**: Set `PYTHONPATH` to project root
4. **Kubernetes Permissions**: Ensure service account has proper roles
5. **API Limits**: Check Zerodha API quotas and rate limits

#### Debug Commands
```bash
# Test imports
python -c "from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss"

# Test trading components
python test_kiteconnect_manager.py
python test_openai_manager.py

# Check configuration
python manage_config.py --validate
```

### 11. Production Deployment

#### CI/CD Pipeline
- **GitHub Actions**: `.github/workflows/`
- **Docker Build**: Automated on push to main
- **GKE Deployment**: Automated rollout
- **Security Scanning**: Bandit + dependency checks

#### Monitoring
- **Logs**: `kubectl logs` and Firestore collections
- **Metrics**: GKE cluster metrics
- **Alerts**: Trade failures and system errors

---

## Quick Start Checklist

- [ ] Install Python 3.10+
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Install Cursor extensions (Python, Kubernetes, Docker)
- [ ] Configure environment variables
- [ ] Set up launch configurations
- [ ] Test local development: `python main.py`
- [ ] Verify tests pass: `pytest`
- [ ] Configure kubectl for cluster access
- [ ] Test deployment: `kubectl apply -f deployments/`

## Support

For development questions, refer to:
- **Main Documentation**: `README.md`
- **Configuration Guide**: `CONFIG_GUIDE.md`
- **Architecture Details**: `CLAUDE.md`
- **Production Readiness**: `PRODUCTION_READINESS_ANALYSIS.md`