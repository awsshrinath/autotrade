#!/bin/bash

# Docker Health Check Script for TRON Trading Services
# This script performs comprehensive health checks for services running in Docker containers

set -e

# Configuration
HEALTH_PORT=${SERVICE_PORT:-8080}
HEALTH_ENDPOINT="/health"
TIMEOUT=10
RETRIES=3

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Health check function
check_health() {
    local url="http://localhost:${HEALTH_PORT}${HEALTH_ENDPOINT}"
    
    log "Checking health endpoint: $url"
    
    # Try to curl the health endpoint
    for i in $(seq 1 $RETRIES); do
        if curl -f -s --max-time $TIMEOUT "$url" > /dev/null 2>&1; then
            log "${GREEN}✓ Health check passed${NC}"
            return 0
        else
            log "${YELLOW}⚠ Health check attempt $i/$RETRIES failed${NC}"
            if [ $i -lt $RETRIES ]; then
                sleep 2
            fi
        fi
    done
    
    log "${RED}✗ Health check failed after $RETRIES attempts${NC}"
    return 1
}

# Process check function
check_process() {
    local script_name="${RUNNER_SCRIPT:-main_runner.py}"
    
    log "Checking if Python process is running: $script_name"
    
    if pgrep -f "$script_name" > /dev/null 2>&1; then
        log "${GREEN}✓ Python process is running${NC}"
        return 0
    else
        log "${RED}✗ Python process not found${NC}"
        return 1
    fi
}

# Memory check function
check_memory() {
    local memory_threshold=90  # 90% memory usage threshold
    
    log "Checking memory usage"
    
    if command -v free > /dev/null 2>&1; then
        local memory_usage=$(free | grep Mem | awk '{printf "%.0f", ($3/$2) * 100.0}')
        
        if [ "$memory_usage" -lt "$memory_threshold" ]; then
            log "${GREEN}✓ Memory usage: ${memory_usage}%${NC}"
            return 0
        else
            log "${YELLOW}⚠ High memory usage: ${memory_usage}%${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠ Cannot check memory usage (free command not available)${NC}"
        return 0  # Don't fail health check if we can't check memory
    fi
}

# Disk space check function
check_disk() {
    local disk_threshold=90  # 90% disk usage threshold
    local check_path="/app/logs"
    
    log "Checking disk space for: $check_path"
    
    if [ -d "$check_path" ]; then
        local disk_usage=$(df "$check_path" | tail -1 | awk '{print $5}' | sed 's/%//')
        
        if [ "$disk_usage" -lt "$disk_threshold" ]; then
            log "${GREEN}✓ Disk usage: ${disk_usage}%${NC}"
            return 0
        else
            log "${YELLOW}⚠ High disk usage: ${disk_usage}%${NC}"
            return 1
        fi
    else
        log "${YELLOW}⚠ Cannot check disk space (path $check_path not found)${NC}"
        return 0  # Don't fail health check if path doesn't exist
    fi
}

# GCP connectivity check function (optional)
check_gcp_connectivity() {
    local credentials_file="${GOOGLE_APPLICATION_CREDENTIALS:-/app/gpt-runner-sa-key.json}"
    
    log "Checking GCP connectivity"
    
    if [ -f "$credentials_file" ]; then
        log "${GREEN}✓ GCP credentials file exists${NC}"
        
        # Optional: Test actual GCP connectivity (disabled by default to avoid API quota usage)
        # if python3 -c "from google.cloud import firestore; firestore.Client()" 2>/dev/null; then
        #     log "${GREEN}✓ GCP connectivity test passed${NC}"
        # else
        #     log "${YELLOW}⚠ GCP connectivity test failed${NC}"
        # fi
        
        return 0
    else
        log "${YELLOW}⚠ GCP credentials file not found: $credentials_file${NC}"
        return 0  # Don't fail health check for missing credentials in development
    fi
}

# Main health check function
main() {
    log "Starting Docker health check for TRON service"
    log "Service: ${RUNNER_SCRIPT:-main_runner.py}"
    log "Port: $HEALTH_PORT"
    
    local exit_code=0
    
    # Primary health check (HTTP endpoint)
    if ! check_health; then
        exit_code=1
    fi
    
    # Secondary checks (process, memory, disk)
    if ! check_process; then
        exit_code=1
    fi
    
    if ! check_memory; then
        # Memory check failure is a warning, not a failure
        log "${YELLOW}⚠ Memory check warning (service still considered healthy)${NC}"
    fi
    
    if ! check_disk; then
        # Disk check failure is a warning, not a failure
        log "${YELLOW}⚠ Disk check warning (service still considered healthy)${NC}"
    fi
    
    # Optional GCP connectivity check
    check_gcp_connectivity
    
    if [ $exit_code -eq 0 ]; then
        log "${GREEN}✓ Overall health check PASSED${NC}"
    else
        log "${RED}✗ Overall health check FAILED${NC}"
    fi
    
    exit $exit_code
}

# Run main function
main "$@"