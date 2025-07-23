#!/bin/bash

# TRON Trading System - Code Update Script
# Updates code without rebuilding images (volume mount advantage)

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.volume.yml"
LOG_FILE="$PROJECT_DIR/logs/code-update.log"

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

# Info message
info() {
    log "${BLUE}ℹ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠ $1${NC}"
}

# Check if services are running
check_services_running() {
    info "Checking if services are running..."
    
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        error_exit "No services are currently running. Run './scripts/deploy.sh' first."
    fi
    
    success "Services are running"
}

# Check for git changes
check_git_changes() {
    info "Checking for code changes..."
    
    if ! command -v git &> /dev/null; then
        warning "Git not available. Skipping change detection."
        return 0
    fi
    
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        warning "Not a git repository. Skipping change detection."
        return 0
    fi
    
    cd "$PROJECT_DIR"
    
    # Check if there are uncommitted changes
    if ! git diff --quiet; then
        info "Uncommitted changes detected"
    fi
    
    # Check if we're behind remote
    git fetch origin >/dev/null 2>&1 || true
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/main 2>/dev/null || git rev-parse origin/master 2>/dev/null || echo "$LOCAL")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        info "New commits available on remote"
        return 1
    else
        info "Code is up to date with remote"
        return 0
    fi
}

# Pull latest code
pull_latest_code() {
    info "Pulling latest code from git..."
    
    if ! command -v git &> /dev/null || [ ! -d "$PROJECT_DIR/.git" ]; then
        warning "Git not available or not a git repository. Skipping git pull."
        return 0
    fi
    
    cd "$PROJECT_DIR"
    
    # Stash any local changes
    git stash push -m "Auto-stash before update $(date)" >/dev/null 2>&1 || true
    
    # Pull latest changes
    if git pull origin main >/dev/null 2>&1 || git pull origin master >/dev/null 2>&1; then
        success "Code updated successfully"
    else
        warning "Failed to pull latest code. Continuing with local code."
    fi
}

# Check if requirements changed
check_requirements_changed() {
    info "Checking if dependencies changed..."
    
    if [ -f "$PROJECT_DIR/.last_requirements_hash" ]; then
        CURRENT_HASH=$(sha256sum "$PROJECT_DIR/requirements.txt" | cut -d' ' -f1)
        LAST_HASH=$(cat "$PROJECT_DIR/.last_requirements_hash")
        
        if [ "$CURRENT_HASH" != "$LAST_HASH" ]; then
            warning "Dependencies changed! Base image rebuild required."
            info "Run './scripts/deploy.sh rebuild' to update dependencies."
            return 1
        fi
    fi
    
    info "No dependency changes detected"
    return 0
}

# Restart specific services
restart_service() {
    local service=$1
    info "Restarting $service..."
    
    if docker-compose -f "$COMPOSE_FILE" restart "$service"; then
        success "$service restarted successfully"
    else
        error_exit "Failed to restart $service"
    fi
}

# Restart all services
restart_all_services() {
    info "Restarting all services to pick up code changes..."
    
    # Get list of running services
    local services=$(docker-compose -f "$COMPOSE_FILE" ps --services --filter status=running)
    
    for service in $services; do
        restart_service "$service"
    done
    
    success "All services restarted"
}

# Wait for services to be ready
wait_for_services() {
    info "Waiting for services to be ready..."
    
    local max_attempts=15
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        local ready_count=0
        local total_count=0
        
        for service in $(docker-compose -f "$COMPOSE_FILE" ps --services --filter status=running); do
            ((total_count++))
            if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up.*healthy\\|Up (healthy)"; then
                ((ready_count++))
            fi
        done
        
        if [ $ready_count -eq $total_count ] && [ $total_count -gt 0 ]; then
            success "All services are ready ($ready_count/$total_count)"
            return 0
        fi
        
        info "Waiting for services... ($ready_count/$total_count ready, attempt $((attempt + 1))/$max_attempts)"
        sleep 5
        attempt=$((attempt + 1))
    done
    
    warning "Some services may still be starting up"
}

# Verify services are working
verify_services() {
    info "Verifying services are working..."
    
    sleep 5  # Give services a moment
    
    local services=("8080:main-runner" "8081:stock-trader" "8082:options-trader" "8083:futures-trader" "8090:dashboard-api")
    local failed_services=()
    
    for service_info in "${services[@]}"; do
        IFS=':' read -r port name <<< "$service_info"
        if curl -f -s --max-time 5 "http://localhost:$port/health" > /dev/null 2>&1; then
            success "$name is responding"
        else
            warning "$name health check failed"
            failed_services+=("$name")
        fi
    done
    
    if [ ${#failed_services[@]} -eq 0 ]; then
        success "All services are working correctly"
    else
        warning "Some services may need more time to start: ${failed_services[*]}"
    fi
}

# Show update summary
show_update_summary() {
    info "Update Summary:"
    
    echo "🔄 Code update completed at $(date)"
    echo "📊 Services status:"
    docker-compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}"
    
    echo ""
    echo "💡 Quick verification commands:"
    echo "   Check logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "   Check status: docker-compose -f $COMPOSE_FILE ps"
    echo "   Test endpoints: curl http://localhost:8080/health"
}

# Main update function
update_code() {
    log "${BLUE}🔄 Starting TRON code update...${NC}"
    
    check_services_running
    
    # Handle git operations
    if check_git_changes; then
        info "No remote changes detected"
    else
        pull_latest_code
    fi
    
    # Check if base image needs rebuilding
    if ! check_requirements_changed; then
        # Requirements changed, need full rebuild
        warning "Dependencies changed. Use './scripts/deploy.sh rebuild' instead."
        exit 1
    fi
    
    restart_all_services
    wait_for_services
    verify_services
    show_update_summary
    
    success "🎉 Code update completed successfully!"
    info "⚡ Total update time: ~30 seconds (no image rebuilds needed!)"
}

# Handle command line arguments
case "${1:-update}" in
    "update"|"")
        update_code
        ;;
    "pull")
        info "Pulling latest code without restart..."
        pull_latest_code
        success "Code pulled. Run '$0 restart' to apply changes."
        ;;
    "restart")
        info "Restarting services to apply code changes..."
        check_services_running
        restart_all_services
        wait_for_services
        verify_services
        success "Services restarted with updated code"
        ;;
    "service")
        if [ -z "$2" ]; then
            error_exit "Service name required. Usage: $0 service <service-name>"
        fi
        check_services_running
        restart_service "$2"
        success "Service $2 restarted"
        ;;
    "verify")
        verify_services
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "help")
        echo "TRON Code Update Script"
        echo ""
        echo "Usage: $0 [command] [args]"
        echo ""
        echo "Commands:"
        echo "  update   - Pull code and restart services (default)"
        echo "  pull     - Pull latest code without restart"
        echo "  restart  - Restart all services"
        echo "  service  - Restart specific service (requires service name)"
        echo "  verify   - Verify all services are working"
        echo "  status   - Show service status"
        echo "  help     - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 update          # Full code update"
        echo "  $0 service stock-trader  # Restart just stock trader"
        echo "  $0 pull            # Just pull code"
        ;;
    *)
        error_exit "Unknown command: $1. Use '$0 help' for usage information."
        ;;
esac