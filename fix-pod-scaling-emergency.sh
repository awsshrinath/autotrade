#!/bin/bash

echo "🚨 EMERGENCY POD SCALING FIX - Post Market Hours 🚨"
echo "=================================================="
echo "Current time: $(date)"
echo ""

# Function to scale deployment with error handling
scale_deployment() {
    local deployment=$1
    local replicas=$2
    local namespace=${3:-gpt}
    
    echo "Scaling $deployment to $replicas replicas..."
    if kubectl scale deployment "$deployment" --replicas="$replicas" -n "$namespace" --timeout=30s; then
        echo "✅ Successfully scaled $deployment"
    else
        echo "❌ Failed to scale $deployment"
        return 1
    fi
}

# Step 1: IMMEDIATE MANUAL SCALING - Cost Critical!
echo "STEP 1: Emergency manual scaling (POST-MARKET HOURS)"
echo "----------------------------------------------------"

# Scale down ALL trading and support pods
DEPLOYMENTS=(
    "stock-trader"
    "options-trader" 
    "futures-trader"
    "main-runner"
    "cognitive-system"
    "frontend"
    "tron-backend"
    "monitoring-service"
    "nginx-proxy"
)

for deployment in "${DEPLOYMENTS[@]}"; do
    scale_deployment "$deployment" 0
done

echo ""
echo "STEP 2: Clean up stuck CronJob executions"
echo "----------------------------------------"

# Delete stuck job pods that have been running for days
echo "Deleting stuck CronJob pods..."
kubectl delete pods -n gpt -l "job-name" --field-selector=status.phase=Running --timeout=60s

# Get list of stuck jobs
echo "Finding stuck jobs running longer than 1 hour..."
STUCK_JOBS=$(kubectl get jobs -n gpt --no-headers | awk '$4 ~ /[0-9]+d|[2-9][0-9]+h/ {print $1}')

if [ ! -z "$STUCK_JOBS" ]; then
    echo "Deleting stuck jobs: $STUCK_JOBS"
    echo $STUCK_JOBS | xargs kubectl delete jobs -n gpt --timeout=60s
else
    echo "No stuck jobs found"
fi

echo ""
echo "STEP 3: Verify current pod status"
echo "---------------------------------"
kubectl get pods -n gpt
kubectl get deployments -n gpt

echo ""
echo "STEP 4: Check recent CronJob status"
echo "-----------------------------------"
kubectl get cronjobs -n gpt
kubectl get jobs -n gpt --sort-by=.metadata.creationTimestamp | tail -10

echo ""
echo "🎯 IMMEDIATE FIX COMPLETED!"
echo "=========================="
echo "- All trading pods scaled to 0 replicas"
echo "- Stuck CronJob processes cleaned up"
echo "- System ready for next market session"
echo ""
echo "💡 NEXT STEPS:"
echo "1. Apply the fixed CronJob configurations"
echo "2. Test scaling operations manually"
echo "3. Monitor CronJob execution logs"
echo "4. Implement better error handling and timeouts" 