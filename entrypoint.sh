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
echo "--- Starting Application ---"

# Execute the main application script passed as an environment variable
# The -u flag ensures that the output is unbuffered and sent straight to stdout
exec python3 -u "$RUNNER_SCRIPT"