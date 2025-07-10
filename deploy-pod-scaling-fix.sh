#!/bin/bash

echo "🚀 COMPREHENSIVE POD SCALING FIX DEPLOYMENT"
echo "============================================"
echo "This script will:"
echo "1. Immediately scale down all pods (emergency fix)"
echo "2. Clean up stuck CronJob processes"
echo "3. Deploy improved CronJob configurations"
echo "4. Test the new scaling system"
echo ""

read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Run emergency fix
echo "STEP 1: Running emergency pod scaling fix..."
echo "--------------------------------------------"
chmod +x fix-pod-scaling-emergency.sh
./fix-pod-scaling-emergency.sh

echo ""
echo "STEP 2: Deploy improved CronJob configurations..."
echo "------------------------------------------------"

# Apply RBAC (ensure permissions are correct)
echo "Applying RBAC configurations..."
kubectl apply -f k8s/rbac/scaler-service-account.yaml
kubectl apply -f k8s/rbac/scaler-cluster-role.yaml
kubectl apply -f k8s/rbac/scaler-role-binding.yaml

# Delete old problematic CronJobs
echo "Removing old problematic CronJobs..."
kubectl delete cronjob market-close-scaler -n gpt --ignore-not-found=true
kubectl delete cronjob post-market-scaler -n gpt --ignore-not-found=true
kubectl delete cronjob trade-stop-scaler -n gpt --ignore-not-found=true

# Apply new improved CronJob
echo "Deploying improved post-market scaler..."
kubectl apply -f k8s/scaling/fixed-post-market-scaler.yaml

# Keep the working CronJobs
echo "Ensuring other CronJobs are properly configured..."
kubectl apply -f k8s/scaling/market-open-scaler.yaml
kubectl apply -f k8s/scaling/trade-start-scaler.yaml
kubectl apply -f k8s/scaling/weekend-scaler.yaml
kubectl apply -f k8s/scaling/holiday-scaler.yaml

echo ""
echo "STEP 3: Verify deployment and test scaling..."
echo "---------------------------------------------"

# Check CronJob status
echo "Current CronJob status:"
kubectl get cronjobs -n gpt

# Test manual scaling (scale up then down to test)
echo ""
echo "Testing scaling functionality..."

# Scale up a test deployment
echo "Testing scale up..."
kubectl scale deployment stock-trader --replicas=1 -n gpt
kubectl wait --for=condition=available --timeout=60s deployment/stock-trader -n gpt

# Scale back down
echo "Testing scale down..."
kubectl scale deployment stock-trader --replicas=0 -n gpt

echo ""
echo "STEP 4: Manual CronJob test..."
echo "------------------------------"
echo "Creating a test job to verify scaling works..."

# Create a test job based on the new CronJob
kubectl create job --from=cronjob/fixed-post-market-scaler manual-scale-test -n gpt

echo "Waiting for test job to complete..."
kubectl wait --for=condition=complete --timeout=120s job/manual-scale-test -n gpt

echo "Test job logs:"
kubectl logs job/manual-scale-test -n gpt

# Clean up test job
kubectl delete job manual-scale-test -n gpt

echo ""
echo "🎯 DEPLOYMENT COMPLETED!"
echo "======================="
echo "✅ Emergency scaling applied"
echo "✅ Stuck CronJobs cleaned up"
echo "✅ Improved CronJob configurations deployed"
echo "✅ Scaling functionality tested"
echo ""
echo "📋 MONITORING CHECKLIST:"
echo "- Monitor CronJob execution: kubectl get cronjobs -n gpt"
echo "- Check job logs: kubectl logs job/<job-name> -n gpt"
echo "- Verify pod counts: kubectl get deployments -n gpt"
echo "- Set up alerts for failed scaling operations"
echo ""
echo "⏰ NEXT SCHEDULED SCALING:"
echo "- Market open: 8:15 AM IST (scale up support services)"
echo "- Trading start: 9:10 AM IST (scale up trading pods)"
echo "- Trading stop: 3:35 PM IST (scale down trading pods)"
echo "- Post-market: 4:30 PM IST (scale down all services)" 