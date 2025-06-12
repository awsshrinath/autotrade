#!/bin/bash

# TRON Trading Dashboard Deployment Script
# This script builds and deploys the trading dashboard

set -e

# Configuration
PROJECT_ID="autotrade-453303"
REGION="asia-south1"
REPOSITORY="gpt-repo"
IMAGE_NAME="trading-dashboard"
NAMESPACE="gpt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
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
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if gcloud is installed
    if ! command -v gcloud &> /dev/null; then
        log_error "gcloud CLI is not installed. Please install Google Cloud SDK first."
        exit 1
    fi
    
    log_success "All prerequisites are installed."
}

# Build Docker image
build_image() {
    log_info "Building Docker image..."
    
    # Get current timestamp for tagging
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)
    IMAGE_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:${TIMESTAMP}"
    LATEST_TAG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${IMAGE_NAME}:latest"
    
    # Build the image
    docker build -t ${IMAGE_TAG} -t ${LATEST_TAG} -f dashboard/Dockerfile .
    
    if [ $? -eq 0 ]; then
        log_success "Docker image built successfully: ${IMAGE_TAG}"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Push image to registry
push_image() {
    log_info "Pushing image to Google Container Registry..."
    
    # Configure Docker to use gcloud as credential helper
    gcloud auth configure-docker ${REGION}-docker.pkg.dev
    
    # Push both tags
    docker push ${IMAGE_TAG}
    docker push ${LATEST_TAG}
    
    if [ $? -eq 0 ]; then
        log_success "Image pushed successfully to registry"
    else
        log_error "Failed to push image to registry"
        exit 1
    fi
}

# Deploy to Kubernetes
deploy_to_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Update the deployment YAML with the new image tag
    sed -i.bak "s|image: .*trading-dashboard:.*|image: ${IMAGE_TAG}|g" deployments/dashboard.yaml
    
    # Apply the deployment
    kubectl apply -f deployments/dashboard.yaml
    
    if [ $? -eq 0 ]; then
        log_success "Deployment applied successfully"
    else
        log_error "Failed to apply deployment"
        exit 1
    fi
    
    # Restore original deployment file
    mv deployments/dashboard.yaml.bak deployments/dashboard.yaml
}

# Wait for deployment to be ready
wait_for_deployment() {
    log_info "Waiting for deployment to be ready..."
    
    kubectl rollout status deployment/trading-dashboard -n ${NAMESPACE} --timeout=300s
    
    if [ $? -eq 0 ]; then
        log_success "Deployment is ready"
    else
        log_error "Deployment failed or timed out"
        exit 1
    fi
}

# Get service information
get_service_info() {
    log_info "Getting service information..."
    
    # Get service details
    kubectl get service dashboard-service -n ${NAMESPACE}
    
    # Get external IP if available
    EXTERNAL_IP=$(kubectl get service dashboard-service -n ${NAMESPACE} -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
    
    if [ ! -z "$EXTERNAL_IP" ]; then
        log_success "Dashboard is accessible at: http://${EXTERNAL_IP}"
        log_info "Login credentials:"
        log_info "  Username: admin"
        log_info "  Password: tron2024"
    else
        log_warning "External IP not yet assigned. Please check again in a few minutes."
        log_info "You can check the service status with:"
        log_info "  kubectl get service dashboard-service -n ${NAMESPACE}"
    fi
}

# Run health check
health_check() {
    log_info "Running health check..."
    
    # Wait a bit for the service to be ready
    sleep 30
    
    # Get pod status
    kubectl get pods -n ${NAMESPACE} -l app=trading-dashboard
    
    # Check if pods are running
    RUNNING_PODS=$(kubectl get pods -n ${NAMESPACE} -l app=trading-dashboard --field-selector=status.phase=Running --no-headers | wc -l)
    
    if [ $RUNNING_PODS -gt 0 ]; then
        log_success "Dashboard pods are running successfully"
    else
        log_warning "Dashboard pods may not be running properly. Check pod logs:"
        log_info "  kubectl logs -n ${NAMESPACE} -l app=trading-dashboard"
    fi
}

# Main deployment function
main() {
    log_info "Starting TRON Trading Dashboard deployment..."
    
    # Parse command line arguments
    SKIP_BUILD=false
    SKIP_PUSH=false
    LOCAL_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --skip-push)
                SKIP_PUSH=true
                shift
                ;;
            --local-only)
                LOCAL_ONLY=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --skip-build    Skip Docker image build"
                echo "  --skip-push     Skip pushing image to registry"
                echo "  --local-only    Build image for local testing only"
                echo "  -h, --help      Show this help message"
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Check prerequisites
    check_prerequisites
    
    # Build image if not skipped
    if [ "$SKIP_BUILD" = false ]; then
        build_image
    fi
    
    # For local-only deployment, just build and exit
    if [ "$LOCAL_ONLY" = true ]; then
        log_success "Local build completed. You can run the dashboard with:"
        log_info "  docker run -p 8501:8501 ${LATEST_TAG}"
        exit 0
    fi
    
    # Push image if not skipped
    if [ "$SKIP_PUSH" = false ]; then
        push_image
    fi
    
    # Deploy to Kubernetes
    deploy_to_k8s
    
    # Wait for deployment
    wait_for_deployment
    
    # Get service information
    get_service_info
    
    # Run health check
    health_check
    
    log_success "Dashboard deployment completed successfully!"
    log_info "You can monitor the deployment with:"
    log_info "  kubectl get pods -n ${NAMESPACE} -l app=trading-dashboard -w"
}

# Run main function
main "$@" 