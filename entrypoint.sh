#!/bin/bash
set -e
cd /app

# Set up Python path to include the app root
export PYTHONPATH="/app:/app/runner:$PYTHONPATH"

# Ensure all necessary directories are valid Python packages
# This is critical for services that run from subdirectories
echo "Initializing Python package structure..."
for dir in runner gpt_runner runner/capital runner/enhanced_logging runner/indicators runner/market_data runner/options runner/production runner/utils gpt_runner/rag gpt_runner/log_aggregator; do
    if [ -d "$dir" ] && [ ! -f "$dir/__init__.py" ]; then
        echo "Creating __init__.py in $dir"
        touch "$dir/__init__.py"
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

# Check if this service needs health checks
if [ "$HEALTH_CHECK_ENABLED" = "true" ] && [ -n "$SERVICE_PORT" ]; then
    echo "Starting with health check wrapper on port $SERVICE_PORT"
    export RUNNER_SCRIPT="$SCRIPT_TO_RUN"
    exec python3 -u runner/health_server.py
else
    echo "Starting script directly without health checks: $SCRIPT_TO_RUN"
    # Execute the main application script
    # The -u flag ensures that the output is unbuffered and sent straight to stdout
    exec python3 -u "$SCRIPT_TO_RUN"
fi