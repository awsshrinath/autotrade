#!/bin/bash

# This script provides manual override capabilities for scaling deployments.
# It's intended for emergency use or manual testing.

set -euo pipefail

DEPLOYMENTS_TO_SCALE=(
  "stock-trader"
  "options-trader"
  "futures-trader"
  "cognitive-system"
)

function scale_up() {
  echo "--- Scaling UP all market-hour deployments to 1 replica ---"
  for dep in "${DEPLOYMENTS_TO_SCALE[@]}"; do
    echo "Scaling up $dep..."
    kubectl scale deployment "$dep" --replicas=1
  done
  echo "--- Manual scale-up complete ---"
}

function scale_down() {
  echo "--- Scaling DOWN all market-hour deployments to 0 replicas ---"
  for dep in "${DEPLOYMENTS_TO_SCALE[@]}"; do
    echo "Scaling down $dep..."
    kubectl scale deployment "$dep" --replicas=0
  done
  echo "--- Manual scale-down complete ---"
}

function status() {
  echo "--- Current replica status for deployments ---"
  kubectl get deployments -l "app in (main-runner, dashboard, monitoring-service, stock-trader, options-trader, futures-trader, cognitive-system)" -o custom-columns="NAME:.metadata.name,REPLICAS:.spec.replicas,AVAILABLE:.status.availableReplicas"
}

function usage() {
  echo "Usage: $0 [up|down|status]"
  echo "  up      : Scales all market-hour deployments to 1 replica."
  echo "  down    : Scales all market-hour deployments to 0 replicas."
  echo "  status  : Shows the current replica status of all relevant deployments."
}

if [[ $# -eq 0 ]]; then
  usage
  exit 1
fi

case "$1" in
  up)
    scale_up
    ;;
  down)
    scale_down
    ;;
  status)
    status
    ;;
  *)
    usage
    exit 1
    ;;
esac 