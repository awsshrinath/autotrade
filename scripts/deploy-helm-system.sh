#!/bin/bash
#
# TRON Trading System - Helm Deployment Script
# Deploy the complete trading system using the fixed Helm chart
#

set -e

# Configuration
PROJECT_ID="autotrade-453303"
CLUSTER_NAME="tron-trading-cluster"
ZONE="asia-south1-a"
NAMESPACE="gpt"
HELM_RELEASE="tron-system"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
BLUE='\\033[0;34m'
NC='\\033[0m' # No Color

# Logging functions
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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    for tool in gcloud kubectl helm; do
        if ! command -v $tool &> /dev/null; then
            log_error "$tool is not installed. Please install it and try again."
            exit 1
        fi
    done
    
    # Check if authenticated with gcloud
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        log_error "Not authenticated with gcloud. Please run 'gcloud auth login'"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Configure kubectl
configure_kubectl() {
    log_info "Configuring kubectl for cluster: $CLUSTER_NAME"
    
    gcloud container clusters get-credentials $CLUSTER_NAME \\
        --zone $ZONE \\
        --project $PROJECT_ID
    
    if [ $? -eq 0 ]; then
        log_success "kubectl configured successfully"
    else
        log_error "Failed to configure kubectl"
        exit 1
    fi
}

# Create namespace
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -
    
    if [ $? -eq 0 ]; then
        log_success "Namespace $NAMESPACE ready"
    else
        log_error "Failed to create namespace"
        exit 1
    fi
}

# Create GCP service account secret
create_gcp_secret() {
    log_info "Creating GCP service account secret..."
    
    # Check if secret already exists
    if kubectl get secret gcp-service-account-key -n $NAMESPACE &> /dev/null; then
        log_warning "GCP service account secret already exists, skipping creation"
        return 0
    fi
    
    # Try to get service account key from Secret Manager
    if gcloud secrets versions access latest --secret="gcp-service-account-key" --project=$PROJECT_ID &> /dev/null; then
        log_info "Getting service account key from Secret Manager"
        SERVICE_ACCOUNT_KEY=$(gcloud secrets versions access latest --secret="gcp-service-account-key" --project=$PROJECT_ID)
        
        kubectl create secret generic gcp-service-account-key \\
            --from-literal=key.json="$SERVICE_ACCOUNT_KEY" \\
            --namespace=$NAMESPACE
        
        if [ $? -eq 0 ]; then
            log_success "GCP service account secret created from Secret Manager"
        else
            log_error "Failed to create GCP service account secret"
            exit 1
        fi
    else
        log_warning "GCP service account key not found in Secret Manager"
        log_warning "You may need to create this secret manually if GCP services are required"
    fi
}

# Validate Helm chart
validate_helm_chart() {
    log_info "Validating Helm chart..."
    
    # Check if Helm chart exists
    if [ ! -d "helm" ]; then
        log_error "Helm chart directory not found. Please run this script from the project root."
        exit 1
    fi
    
    # Lint the Helm chart
    helm lint helm/
    
    if [ $? -eq 0 ]; then
        log_success "Helm chart validation passed"
    else
        log_error "Helm chart validation failed"
        exit 1
    fi
}

# Deploy with Helm
deploy_helm() {
    log_info "Deploying TRON Trading System with Helm..."
    
    # Create values override file with current configuration
    cat > /tmp/tron-values-override.yaml << EOF
namespace: $NAMESPACE
gcpProjectId: $PROJECT_ID

# Enable ingress for logs.tron-trading.com
ingress:
  enabled: true
  className: "gce"
  annotations:
    kubernetes.io/ingress.class: "gce"
    kubernetes.io/ingress.global-static-ip-name: "tron-trading-ip"
    networking.gke.io/managed-certificates: "tron-trading-ssl"

# SSL configuration
ssl:
  enabled: true
  managedCertificate:
    enabled: true
    name: "tron-trading-ssl"

# Enable monitoring
monitoring:
  enabled: true
  healthCheckInterval: 30

# Service discovery
serviceDependencies:
  enabled: true
EOF
    
    # Deploy using Helm
    helm upgrade --install $HELM_RELEASE helm/ \\
        --namespace $NAMESPACE \\
        --create-namespace \\
        --values /tmp/tron-values-override.yaml \\
        --wait \\
        --timeout 15m \\
        --debug
    
    if [ $? -eq 0 ]; then
        log_success "Helm deployment completed successfully"
    else
        log_error "Helm deployment failed"
        exit 1
    fi
}

# Wait for pods to be ready
wait_for_pods() {
    log_info "Waiting for pods to be ready..."
    
    # Wait for all pods to be ready (max 10 minutes)
    kubectl wait --for=condition=ready pod --all -n $NAMESPACE --timeout=600s
    
    if [ $? -eq 0 ]; then
        log_success "All pods are ready"
    else
        log_warning "Some pods may not be ready. Checking pod status..."
        kubectl get pods -n $NAMESPACE
    fi
}

# Verify deployment
verify_deployment() {
    log_info "Verifying deployment..."
    
    echo
    log_info "=== DEPLOYMENT STATUS ==="
    
    # Show pods
    echo
    log_info "Pods:"
    kubectl get pods -n $NAMESPACE -o wide
    
    # Show services
    echo
    log_info "Services:"
    kubectl get services -n $NAMESPACE
    
    # Show ingress
    echo
    log_info "Ingress:"
    kubectl get ingress -n $NAMESPACE
    
    # Show configmaps
    echo
    log_info "ConfigMaps:"
    kubectl get configmaps -n $NAMESPACE
    
    # Show secrets
    echo
    log_info "Secrets:"
    kubectl get secrets -n $NAMESPACE
    
    # Check if log aggregator is accessible
    echo
    log_info "Testing service connectivity..."
    
    # Port forward test for log aggregator
    log_info "Testing log aggregator service (port 8001)..."
    timeout 10 kubectl port-forward -n $NAMESPACE svc/log-aggregator-service 8001:8001 &> /dev/null &
    PF_PID=$!
    sleep 2
    
    if curl -s http://localhost:8001/health &> /dev/null; then
        log_success "Log aggregator service is accessible"
    else
        log_warning "Log aggregator service may not be ready yet"
    fi
    
    # Kill port forward
    kill $PF_PID 2>/dev/null || true
    
    echo
    log_success "Deployment verification completed"
}

# Get deployment info
show_deployment_info() {
    echo
    log_info "=== DEPLOYMENT INFORMATION ==="
    
    # Get external IPs
    EXTERNAL_IPS=$(kubectl get services -n $NAMESPACE -o jsonpath='{.items[?(@.spec.type=="LoadBalancer")].status.loadBalancer.ingress[0].ip}')
    
    if [ ! -z "$EXTERNAL_IPS" ]; then
        echo
        log_info "External IPs:"
        echo "$EXTERNAL_IPS"
    fi
    
    # Get ingress information
    INGRESS_IPS=$(kubectl get ingress -n $NAMESPACE -o jsonpath='{.items[*].status.loadBalancer.ingress[0].ip}')
    
    if [ ! -z "$INGRESS_IPS" ]; then
        echo
        log_info "Ingress IPs:"
        echo "$INGRESS_IPS"
    fi
    
    echo
    log_info "Access URLs:"
    log_info "- Logs Dashboard: https://logs.tron-trading.com"
    log_info "- API Backend: https://api.tron-trading.com"
    log_info "- Dashboard: http://<external-ip>:8501 (if LoadBalancer ready)"
    
    echo
    log_info "Useful commands:"
    log_info "- View logs: kubectl logs -f deployment/main-runner -n $NAMESPACE"
    log_info "- Get pods: kubectl get pods -n $NAMESPACE"
    log_info "- Port forward log aggregator: kubectl port-forward -n $NAMESPACE svc/log-aggregator-service 8001:8001"
    log_info "- Port forward dashboard: kubectl port-forward -n $NAMESPACE svc/trading-dashboard-service 8501:8501"
}

# Cleanup function
cleanup() {
    rm -f /tmp/tron-values-override.yaml
}

# Main execution
main() {
    log_info "Starting TRON Trading System Helm deployment..."
    
    # Set trap for cleanup
    trap cleanup EXIT
    
    check_prerequisites
    configure_kubectl
    create_namespace
    create_gcp_secret
    validate_helm_chart
    deploy_helm
    wait_for_pods
    verify_deployment
    show_deployment_info
    
    echo
    log_success "🎉 TRON Trading System deployment completed successfully!"
    log_info "The system should now be running and accessible via the URLs above."
}

# Script options
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "verify")
        configure_kubectl
        verify_deployment
        show_deployment_info
        ;;
    "clean")
        log_warning "This will delete the entire Helm release: $HELM_RELEASE"
        read -p "Are you sure? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            helm uninstall $HELM_RELEASE -n $NAMESPACE
            kubectl delete namespace $NAMESPACE
            log_success "Cleanup completed"
        fi
        ;;
    *)
        echo "Usage: $0 [deploy|verify|clean]"
        echo "  deploy  - Deploy the complete system (default)"
        echo "  verify  - Verify existing deployment"
        echo "  clean   - Remove the deployment"
        exit 1
        ;;
esac