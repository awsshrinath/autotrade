#!/bin/bash
set -e
cd /app

# Set up Python path properly - order matters!
export PYTHONPATH="/app:$PYTHONPATH"

# Ensure package structure exists
if [ ! -f "gpt_runner/__init__.py" ]; then
    echo "# Makes gpt_runner a Python package" > gpt_runner/__init__.py
fi

if [ ! -d "gpt_runner/rag" ]; then
    mkdir -p gpt_runner/rag
fi

if [ ! -f "gpt_runner/rag/__init__.py" ]; then
    echo "# Makes rag a Python package" > gpt_runner/rag/__init__.py
fi

# Ensure runner package structure exists (needed for futures/options traders)
if [ ! -f "runner/__init__.py" ]; then
    echo "# Makes runner a Python package" > runner/__init__.py
fi

# Ensure runner subdirectories are packages
for subdir in utils strategies; do
    if [ -d "runner/$subdir" ] && [ ! -f "runner/$subdir/__init__.py" ]; then
        echo "# Makes runner.$subdir a Python package" > runner/$subdir/__init__.py
    fi
done

# Debug: Show Python path and file structure
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Files in gpt_runner: $(ls -la gpt_runner/ 2>/dev/null || echo 'Directory not found')"
echo "Files in gpt_runner/rag: $(ls -la gpt_runner/rag/ 2>/dev/null || echo 'Directory not found')"
echo "Files in runner: $(ls -la runner/ 2>/dev/null || echo 'Directory not found')"
echo "Runner package check: $(python3 -c 'import runner; print("✓ runner package importable")' 2>/dev/null || echo '✗ runner package not importable')"

# Test basic imports before running - avoid problematic ones for now
python3 -c "
import sys
import os
print('Python version:', sys.version)
print('Current working directory:', os.getcwd())
print('Python path:', sys.path[:3])  # Show first 3 entries

# Test basic module imports
try:
    import datetime
    import time
    print('✓ Basic Python modules imported successfully')
except Exception as e:
    print(f'✗ Basic imports failed: {e}')
    exit(1)

# Test if gpt_runner is importable
try:
    import gpt_runner
    print('✓ gpt_runner package found')
except Exception as e:
    print(f'✗ gpt_runner package not found: {e}')

# Don't test problematic imports here - let the main script handle them gracefully
print('✓ Basic import validation completed')
"

echo "Starting application..."
# Run the specified script
exec python3 -u "$RUNNER_SCRIPT"