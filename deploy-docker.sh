#!/bin/bash

# TRON Docker Deployment Script
# Single Instance Deployment

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$SCRIPT_DIR/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success() {
    log "${GREEN}✓ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠ $1${NC}"
}

# Info message
info() {
    log "${BLUE}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed. Please install Docker first."
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed. Please install Docker Compose first."
    fi
    
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running. Please start Docker first."
    fi
    
    success "Prerequisites check passed"
}

# Backup existing deployment
backup_existing() {
    if [ -f "docker-compose.yml" ] && docker-compose ps | grep -q "Up"; then
        info "Backing up existing deployment..."
        mkdir -p "$BACKUP_DIR"
        
        # Backup configuration files
        cp docker-compose.yml "$BACKUP_DIR/" 2>/dev/null || true
        cp .env.docker "$BACKUP_DIR/" 2>/dev/null || true
        cp nginx.conf "$BACKUP_DIR/" 2>/dev/null || true
        
        # Backup logs
        if [ -d "logs" ]; then
            cp -r logs "$BACKUP_DIR/" 2>/dev/null || true
        fi
        
        success "Backup created at $BACKUP_DIR"
    fi
}

# Stop existing services
stop_services() {
    info "Stopping existing services..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down --remove-orphans || warning "Some services failed to stop cleanly"
    fi
    
    success "Services stopped"
}

# Create necessary directories
create_directories() {
    info "Creating necessary directories..."
    
    mkdir -p logs/{main-runner,stock-trader,options-trader,futures-trader,dashboard-api,frontend,nginx,log-aggregator}
    mkdir -p data
    mkdir -p backups
    
    success "Directories created"
}

# Validate configuration
validate_config() {
    info "Validating configuration..."
    
    if [ ! -f ".env.docker" ]; then
        error_exit ".env.docker file not found. Please ensure it exists."
    fi
    
    if [ ! -f "docker-compose.yml" ]; then
        error_exit "docker-compose.yml file not found. Please ensure it exists."
    fi
    
    if [ ! -f "gpt-runner-sa-key.json" ]; then
        warning "GCP service account key not found. Some features may not work."
        info "Please place your gcp-runner-sa-key.json file in the current directory."
    fi
    
    success "Configuration validation passed"
}

# Pull latest images
pull_images() {
    info "Pulling latest Docker images..."
    
    if ! docker-compose pull; then
        warning "Failed to pull some images. Continuing with local images."
    else
        success "Images pulled successfully"
    fi
}

# Build local images if needed
build_images() {
    info "Building Docker images..."
    
    if ! docker-compose build; then
        error_exit "Failed to build Docker images"
    fi
    
    success "Images built successfully"
}

# Start services
start_services() {
    info "Starting TRON services..."
    
    if ! docker-compose up -d; then
        error_exit "Failed to start services"
    fi
    
    success "Services started"
}

# Wait for services to be healthy
wait_for_health() {
    info "Waiting for services to become healthy..."
    
    local max_attempts=30
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose ps | grep -q "Up (healthy)"; then
            success "Services are healthy"
            return 0
        fi
        
        info "Waiting for health checks... (attempt $((attempt + 1))/$max_attempts)"
        sleep 10
        attempt=$((attempt + 1))
    done
    
    warning "Health check timeout. Some services may still be starting."
    docker-compose ps
}

# Display service status
show_status() {
    info "Service Status:"
    docker-compose ps
    
    echo ""
    info "Service URLs:"
    echo "🌐 Frontend Dashboard: http://localhost:3000"
    echo "🔧 Dashboard API: http://localhost:8090"
    echo "📈 Main Trading Runner: http://localhost:8080"
    echo "📊 Stock Trader: http://localhost:8081"
    echo "📊 Options Trader: http://localhost:8082"
    echo "📊 Futures Trader: http://localhost:8083"
    echo "📋 Log Aggregator: http://localhost:8095"
    echo "🌐 Nginx Proxy: http://localhost:80"
    
    echo ""
    info "Quick Commands:"
    echo "📋 View logs: docker-compose logs -f [service-name]"
    echo "🔍 Check status: docker-compose ps"
    echo "🛑 Stop services: docker-compose down"
    echo "🔄 Restart: docker-compose restart [service-name]"
}

# Test basic functionality
test_services() {
    info "Testing service endpoints..."
    
    sleep 10  # Give services time to start
    
    # Test health endpoints
    local services=("8080" "8081" "8082" "8083" "8090")
    for port in "${services[@]}"; do
        if curl -f -s "http://localhost:$port/health" > /dev/null 2>&1; then
            success "Health check passed for port $port"
        else
            warning "Health check failed for port $port"
        fi
    done
    
    # Test frontend
    if curl -f -s "http://localhost:3000" > /dev/null 2>&1; then
        success "Frontend is responding"
    else
        warning "Frontend is not responding"
    fi
}

# Main deployment function
deploy() {
    log "${BLUE}🚀 Starting TRON Docker deployment...${NC}"
    
    check_prerequisites
    backup_existing
    stop_services
    create_directories
    validate_config
    
    # Try to pull images first, then build if needed
    if ! pull_images; then
        build_images
    fi
    
    start_services
    wait_for_health
    test_services
    show_status
    
    success "🎉 TRON deployment completed successfully!"
    info "📝 Deployment log saved to: $LOG_FILE"
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy"|"")
        deploy
        ;;
    "stop")
        info "Stopping TRON services..."
        docker-compose down
        success "Services stopped"
        ;;
    "restart")
        info "Restarting TRON services..."
        docker-compose restart
        success "Services restarted"
        ;;
    "status")
        docker-compose ps
        ;;
    "logs")
        docker-compose logs -f "${2:-}"
        ;;
    "update")
        info "Updating TRON services..."
        docker-compose pull
        docker-compose up -d
        success "Services updated"
        ;;
    "clean")
        info "Cleaning up Docker resources..."
        docker-compose down --remove-orphans
        docker system prune -f
        success "Cleanup completed"
        ;;
    "help")
        echo "TRON Docker Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy   - Deploy TRON services (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  status   - Show service status"
        echo "  logs     - Show logs (optionally for specific service)"
        echo "  update   - Pull latest images and restart"
        echo "  clean    - Stop services and clean up Docker resources"
        echo "  help     - Show this help message"
        ;;
    *)
        error_exit "Unknown command: $1. Use '$0 help' for usage information."
        ;;
esac