#!/bin/bash
set -e
cd /app

# Set up Python path with comprehensive coverage
export PYTHONPATH="/app:/app/runner:/app/gpt_runner:/app/runner/utils:/app/runner/enhanced_logging:$PYTHONPATH"

# Ensure all necessary directories are valid Python packages
# Create directories if they don't exist and add __init__.py files
echo "Initializing Python package structure..."
PACKAGE_DIRS=(
    "runner"
    "runner/capital"
    "runner/enhanced_logging" 
    "runner/indicators"
    "runner/market_data"
    "runner/options"
    "runner/production"
    "runner/utils"
    "runner/strategies"
    "gpt_runner"
    "gpt_runner/rag"
    "gpt_runner/log_aggregator"
    "stock_trading"
    "futures_trading"
    "options_trading"
    "strategies"
    "config"
    "utils"
    "services"
)

for dir in "${PACKAGE_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo "Creating directory: $dir"
        mkdir -p "$dir"
    fi
    if [ ! -f "$dir/__init__.py" ]; then
        echo "Creating __init__.py in $dir"
        touch "$dir/__init__.py"
    fi
done

# Validate critical files exist
echo "Validating critical files..."
CRITICAL_FILES=(
    "runner/config.py"
    "runner/logger.py"
    "runner/health_server.py"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ CRITICAL: Missing file $file"
        exit 1
    fi
done

# Basic validation before execution
echo "--- Environment Validation ---"
echo "Python Version: $(python3 --version)"
echo "PYTHONPATH: $PYTHONPATH"
echo "Working Directory: $(pwd)"
echo "Runner Script: $RUNNER_SCRIPT"
echo "Service Port: ${SERVICE_PORT:-'Not set'}"
echo "Health Check Required: ${HEALTH_CHECK_ENABLED:-'Not set'}"
echo "--- Starting Application ---"

# Determine script to run - from args or environment variable
SCRIPT_TO_RUN=""
if [ $# -gt 0 ]; then
    # Script passed as argument
    SCRIPT_TO_RUN="$1"
    echo "Script from args: $SCRIPT_TO_RUN"
elif [ -n "$RUNNER_SCRIPT" ]; then
    # Script from environment variable
    SCRIPT_TO_RUN="$RUNNER_SCRIPT"
    echo "Script from env: $SCRIPT_TO_RUN"
else
    echo "❌ ERROR: No script specified via args or RUNNER_SCRIPT environment variable"
    exit 1
fi

# Validate the script exists
if [ ! -f "$SCRIPT_TO_RUN" ]; then
    echo "❌ ERROR: Script file not found: $SCRIPT_TO_RUN"
    echo "Available files in /app:"
    find /app -name "*.py" | head -20
    exit 1
fi

# Test import of the script before running
echo "Testing script import..."
if ! python3 -c "import sys; sys.path.insert(0, '/app'); import importlib.util; spec = importlib.util.spec_from_file_location('test_module', '$SCRIPT_TO_RUN'); spec.loader.load_module(spec)" 2>/dev/null; then
    echo "⚠️  WARNING: Script import test failed, but continuing anyway..."
else
    echo "✅ Script import test passed"
fi

# Set default environment variables if not provided
export PAPER_TRADE="${PAPER_TRADE:-true}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export ENVIRONMENT="${ENVIRONMENT:-development}"

# Set the script path for the health server wrapper
export RUNNER_SCRIPT="$SCRIPT_TO_RUN"

# Use health server wrapper if health checks are enabled, otherwise run script directly
if [ "${HEALTH_CHECK_ENABLED}" = "true" ]; then
    echo "🏥 Starting application with health server wrapper on port ${SERVICE_PORT:-8080}..."
    exec python3 -u -m runner.health_server
else
    echo "🏃 Executing main application script directly: $SCRIPT_TO_RUN"
    exec python3 -u "$SCRIPT_TO_RUN"
fi