#!/bin/bash

# Fix Helm deployment issues
echo "🔧 Fixing Helm deployment issues..."

# Function to force delete namespace if stuck in terminating state
force_delete_namespace() {
    local namespace=$1
    echo "🔨 Force deleting namespace $namespace..."
    
    # Get all finalizers and remove them
    kubectl get namespace $namespace -o json | jq '.spec.finalizers = []' | kubectl replace --raw "/api/v1/namespaces/$namespace/finalize" -f - || true
    
    # If that doesn't work, patch it directly
    kubectl patch namespace $namespace -p '{"spec":{"finalizers":[]}}' --type=merge || true
    
    # Final nuclear option - edit the namespace directly
    kubectl get namespace $namespace -o json | jq 'del(.spec.finalizers)' | kubectl replace --raw "/api/v1/namespaces/$namespace" -f - || true
}

# Function to wait for namespace deletion with timeout
wait_for_namespace_deletion() {
    local namespace=$1
    local timeout=300  # 5 minutes
    local elapsed=0
    
    echo "⏳ Waiting for namespace $namespace to be deleted (timeout: 5 minutes)..."
    
    while kubectl get namespace $namespace >/dev/null 2>&1; do
        if [ $elapsed -ge $timeout ]; then
            echo "⚠️ Namespace deletion timed out after 5 minutes, using force deletion..."
            force_delete_namespace $namespace
            break
        fi
        
        sleep 10
        elapsed=$((elapsed + 10))
        echo "⏳ Still waiting... (${elapsed}s elapsed)"
    done
    
    # Wait a bit more to ensure it's really gone
    sleep 5
    
    if kubectl get namespace $namespace >/dev/null 2>&1; then
        echo "❌ Failed to delete namespace $namespace"
        return 1
    else
        echo "✅ Namespace $namespace successfully deleted"
        return 0
    fi
}

# Delete any existing Helm release (if exists)
echo "🗑️ Cleaning up existing Helm releases..."
helm uninstall tron-system -n gpt --ignore-not-found || true

# Delete the entire namespace to ensure clean slate
echo "🗑️ Deleting namespace gpt for clean deployment..."
kubectl delete namespace gpt --ignore-not-found=true

# Wait for namespace deletion with force fallback
wait_for_namespace_deletion gpt

# Update Helm dependencies
echo "📦 Updating Helm dependencies..."
helm dependency update ./helm

# Install the Helm chart
echo "🚀 Installing Helm chart..."
helm install tron-system ./helm -n gpt --create-namespace

# Check deployment status
echo "✅ Checking deployment status..."
kubectl get pods -n gpt
kubectl get services -n gpt

echo "🎉 Deployment fix complete!"