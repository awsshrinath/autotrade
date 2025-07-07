#!/bin/bash

# A simple script to manually trigger scaling for testing purposes.
# This bypasses the need to wait for the CronJob schedule.

# Usage:
# ./manual-override.sh up   - Scales all deployments to 1 replica
# ./manual-override.sh down - Scales all deployments to 0 replicas

NAMESPACE="gpt"
DEPLOYMENTS=(
    "main-runner"
    "frontend"
    "monitoring-service"
    "stock-trader"
    "options-trader"
    "futures-trader"
    "cognitive-system"
    "nginx-proxy"
    "tron-backend"
)

scale() {
    local replicas=$1
    echo "--- Scaling all deployments to $replicas replicas in namespace '$NAMESPACE' ---"
    for dep in "${DEPLOYMENTS[@]}"; do
        echo "Scaling $dep..."
        kubectl scale deployment/"$dep" -n "$NAMESPACE" --replicas="$replicas"
    done
    echo "--- Manual scaling complete ---"
}

if [[ "$1" == "up" ]]; then
    scale 1
elif [[ "$1" == "down" ]]; then
    scale 0
else
    echo "Error: Invalid argument. Use 'up' or 'down'."
    echo "Usage: ./manual-override.sh [up|down]"
    exit 1
fi 