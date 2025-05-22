#!/bin/bash
set -e
cd /app
exec python -u "$RUNNER_SCRIPT"