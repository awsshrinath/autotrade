#!/bin/bash
set -e
cd /app

# Set up Python path properly
export PYTHONPATH="/app:/app/runner:/app/gpt_runner:$PYTHONPATH"

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

# Debug: Show Python path and file structure
echo "Python path: $PYTHONPATH"
echo "Current directory: $(pwd)"
echo "Files in gpt_runner: $(ls -la gpt_runner/ 2>/dev/null || echo 'Directory not found')"
echo "Files in gpt_runner/rag: $(ls -la gpt_runner/rag/ 2>/dev/null || echo 'Directory not found')"

# Test imports before running
python3 -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')
sys.path.insert(0, '/app/gpt_runner')

try:
    from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
    print('✓ Successfully imported faiss_firestore_adapter')
except Exception as e:
    print(f'✗ Failed to import faiss_firestore_adapter: {e}')

try:
    from gpt_runner.rag.rag_worker import embed_logs_for_today
    print('✓ Successfully imported rag_worker')
except Exception as e:
    print(f'✗ Failed to import rag_worker: {e}')
"

# Run the specified script
exec python3 -u "$RUNNER_SCRIPT"