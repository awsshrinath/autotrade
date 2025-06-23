#!/bin/bash
#
# TRON Trading System - Fix Stuck Namespace
# Force cleanup of stuck namespace and resources
#

set -e

NAMESPACE="gpt"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if namespace exists and is stuck
check_namespace_status() {
    log_info "Checking namespace status..."
    
    if kubectl get namespace $NAMESPACE &> /dev/null; then
        STATUS=$(kubectl get namespace $NAMESPACE -o jsonpath='{.status.phase}')
        log_warning "Namespace $NAMESPACE exists with status: $STATUS"
        
        if [ "$STATUS" = "Terminating" ]; then
            log_error "Namespace is stuck in Terminating state!"
            return 1
        fi
    else
        log_success "Namespace $NAMESPACE does not exist"
        return 0
    fi
}

# Force delete all resources in namespace
force_delete_resources() {
    log_info "Force deleting all resources in namespace $NAMESPACE..."
    
    # Delete all deployments with force
    kubectl delete deployments --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete all services
    kubectl delete services --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete all configmaps
    kubectl delete configmaps --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete all secrets
    kubectl delete secrets --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete all ingress
    kubectl delete ingress --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete all pods with force
    kubectl delete pods --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    # Delete any remaining resources
    kubectl delete all --all -n $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    log_success "Resources deleted"
}

# Remove finalizers from namespace
remove_namespace_finalizers() {
    log_info "Removing finalizers from namespace..."
    
    # Get the namespace and remove finalizers
    kubectl get namespace $NAMESPACE -o json | \
        jq '.spec.finalizers = []' | \
        kubectl replace --raw "/api/v1/namespaces/$NAMESPACE/finalize" -f - &> /dev/null || true
    
    log_success "Finalizers removed"
}

# Force delete namespace using API
force_delete_namespace() {
    log_info "Force deleting namespace using Kubernetes API..."
    
    # Try to patch the namespace to remove finalizers
    kubectl patch namespace $NAMESPACE -p '{"spec":{"finalizers":[]}}' --type=merge &> /dev/null || true
    
    # Force delete the namespace
    kubectl delete namespace $NAMESPACE --force --grace-period=0 &> /dev/null || true
    
    log_success "Namespace force deletion attempted"
}

# Alternative method using kubectl proxy
force_delete_with_proxy() {
    log_info "Attempting force delete using kubectl proxy..."
    
    # Start kubectl proxy in background
    kubectl proxy --port=8080 &
    PROXY_PID=$!
    sleep 2
    
    # Get namespace info and remove finalizers
    curl -k -H "Content-Type: application/json" -X PUT \
        --data-binary @- \
        http://localhost:8080/api/v1/namespaces/$NAMESPACE/finalize << EOF
{
  "kind": "Namespace",
  "apiVersion": "v1",
  "metadata": {
    "name": "$NAMESPACE"
  },
  "spec": {
    "finalizers": []
  }
}
EOF
    
    # Kill proxy
    kill $PROXY_PID 2>/dev/null || true
    
    log_success "Proxy method attempted"
}

# Wait for namespace to be completely gone
wait_for_namespace_deletion() {
    log_info "Waiting for namespace to be completely deleted..."
    
    for i in {1..60}; do
        if ! kubectl get namespace $NAMESPACE &> /dev/null; then
            log_success "Namespace $NAMESPACE is completely deleted"
            return 0
        fi
        
        echo -n "."
        sleep 2
    done
    
    log_error "Namespace still exists after 2 minutes"
    return 1
}

# Main execution
main() {
    log_info "Starting namespace cleanup for: $NAMESPACE"
    
    # Check current status
    if check_namespace_status; then
        log_success "Namespace is already clean, nothing to do"
        exit 0
    fi
    
    log_warning "Attempting to force cleanup stuck namespace..."
    
    # Method 1: Force delete all resources
    force_delete_resources
    sleep 5
    
    # Method 2: Remove finalizers
    remove_namespace_finalizers
    sleep 5
    
    # Method 3: Force delete namespace
    force_delete_namespace
    sleep 5
    
    # Check if it worked
    if check_namespace_status; then
        log_success "Namespace cleanup successful!"
        exit 0
    fi
    
    # Method 4: Use proxy method (more aggressive)
    force_delete_with_proxy
    sleep 10
    
    # Final check
    if wait_for_namespace_deletion; then
        log_success "Namespace cleanup completed successfully!"
    else
        log_error "Failed to delete namespace. Manual intervention may be required."
        echo
        log_info "Manual cleanup commands:"
        log_info "1. kubectl get namespace $NAMESPACE -o yaml"
        log_info "2. kubectl patch namespace $NAMESPACE -p '{\"spec\":{\"finalizers\":[]}}' --type=merge"
        log_info "3. kubectl delete namespace $NAMESPACE --force --grace-period=0"
        exit 1
    fi
}

# Handle Ctrl+C
trap 'log_warning "Cleanup interrupted"; exit 1' INT

main "$@"