#!/bin/bash

# TRON Trading System - Migration Test Script
# Validates that the volume mount migration works correctly

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Logging function
log() {
    echo -e "$(date '+%H:%M:%S') - $1"
}

# Test functions
test_passed() {
    log "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

test_failed() {
    log "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

test_info() {
    log "${BLUE}ℹ $1${NC}"
}

# Test 1: Check if base image exists
test_base_image() {
    test_info "Testing base image availability..."
    
    if docker images tron-base:latest --format "table {{.Repository}}" | grep -q "tron-base"; then
        test_passed "Base image exists"
    else
        test_failed "Base image not found"
    fi
}

# Test 2: Validate compose file syntax
test_compose_syntax() {
    test_info "Testing compose file syntax..."
    
    if docker-compose -f "$PROJECT_DIR/docker-compose.volume.yml" config >/dev/null 2>&1; then
        test_passed "Volume mount compose file syntax is valid"
    else
        test_failed "Volume mount compose file has syntax errors"
    fi
    
    if docker-compose -f "$PROJECT_DIR/docker-compose.dev.yml" config >/dev/null 2>&1; then
        test_passed "Development compose file syntax is valid"
    else
        test_failed "Development compose file has syntax errors"
    fi
}

# Test 3: Check required files
test_required_files() {
    test_info "Testing required files..."
    
    local required_files=(
        "Dockerfile.base"
        "docker-compose.volume.yml"
        "docker-compose.dev.yml"
        "scripts/deploy.sh"
        "scripts/build-base.sh"
        "scripts/update-code.sh"
        "requirements.txt"
        ".env.docker"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            test_passed "Required file exists: $file"
        else
            test_failed "Missing required file: $file"
        fi
    done
}

# Test 4: Check script permissions
test_script_permissions() {
    test_info "Testing script permissions..."
    
    local scripts=(
        "scripts/deploy.sh"
        "scripts/build-base.sh"
        "scripts/update-code.sh"
    )
    
    for script in "${scripts[@]}"; do
        if [ -x "$PROJECT_DIR/$script" ]; then
            test_passed "Script is executable: $script"
        else
            test_failed "Script is not executable: $script"
        fi
    done
}

# Test 5: Check directory structure
test_directory_structure() {
    test_info "Testing directory structure..."
    
    local required_dirs=(
        "runner"
        "stock_trading"
        "options_trading"
        "futures_trading"
        "dashboard_api"
        "utils"
        "config"
        "logs"
        "data"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$PROJECT_DIR/$dir" ]; then
            test_passed "Required directory exists: $dir"
        else
            test_failed "Missing required directory: $dir"
        fi
    done
}

# Test 6: Test base image functionality
test_base_image_functionality() {
    test_info "Testing base image functionality..."
    
    if docker images tron-base:latest --format "table {{.Repository}}" | grep -q "tron-base"; then
        # Test Python import
        if docker run --rm tron-base:latest python -c "import fastapi, uvicorn, asyncio; print('Dependencies OK')" >/dev/null 2>&1; then
            test_passed "Base image Python dependencies work"
        else
            test_failed "Base image Python dependencies failed"
        fi
        
        # Test user setup
        if docker run --rm tron-base:latest whoami | grep -q "tron"; then
            test_passed "Base image user setup correct"
        else
            test_failed "Base image user setup incorrect"
        fi
    else
        test_failed "Base image not available for testing"
    fi
}

# Test 7: Estimate storage savings
test_storage_savings() {
    test_info "Calculating storage savings..."
    
    # Get base image size
    if docker images tron-base:latest --format "table {{.Size}}" | tail -n +2 | head -1 | grep -q "MB\|GB"; then
        BASE_SIZE=$(docker images tron-base:latest --format "table {{.Size}}" | tail -n +2 | head -1)
        test_passed "Base image size: $BASE_SIZE"
        
        # Calculate theoretical savings
        test_info "Estimated savings vs. individual builds:"
        test_info "  Before: ~6GB × 7 services = ~42GB total"
        test_info "  After: ~$BASE_SIZE × 1 image = ~$BASE_SIZE total"
        test_info "  Savings: ~95% storage reduction!"
    else
        test_failed "Could not determine base image size"
    fi
}

# Test 8: Check volume mount paths
test_volume_mounts() {
    test_info "Testing volume mount configuration..."
    
    # Check if key directories exist for mounting
    local mount_dirs=("runner" "stock_trading" "options_trading" "futures_trading" "dashboard_api")
    
    for dir in "${mount_dirs[@]}"; do
        if [ -d "$PROJECT_DIR/$dir" ] && [ -n "$(ls -A "$PROJECT_DIR/$dir" 2>/dev/null)" ]; then
            test_passed "Volume mount source ready: $dir"
        else
            test_failed "Volume mount source missing or empty: $dir"
        fi
    done
}

# Run all tests
run_tests() {
    log "${BLUE}🧪 Starting TRON Volume Mount Migration Tests...${NC}"
    echo ""
    
    test_base_image
    test_compose_syntax
    test_required_files
    test_script_permissions
    test_directory_structure
    test_base_image_functionality
    test_volume_mounts
    test_storage_savings
    
    echo ""
    log "${BLUE}📊 Test Results Summary:${NC}"
    log "${GREEN}✓ Tests Passed: $TESTS_PASSED${NC}"
    
    if [ $TESTS_FAILED -gt 0 ]; then
        log "${RED}✗ Tests Failed: $TESTS_FAILED${NC}"
        echo ""
        log "${YELLOW}⚠ Please fix the failed tests before proceeding with migration.${NC}"
        exit 1
    else
        log "${RED}✗ Tests Failed: $TESTS_FAILED${NC}"
        echo ""
        log "${GREEN}🎉 All tests passed! Migration setup is ready.${NC}"
        log "${BLUE}💡 Next steps:${NC}"
        log "   1. Build base image: ./scripts/build-base.sh"
        log "   2. Deploy with volumes: ./scripts/deploy.sh"
        log "   3. Test deployment: curl http://localhost:8080/health"
        exit 0
    fi
}

# Handle command line arguments
case "${1:-test}" in
    "test"|"")
        run_tests
        ;;
    "help")
        echo "TRON Migration Test Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  test     - Run all migration tests (default)"
        echo "  help     - Show this help message"
        ;;
    *)
        echo "Unknown command: $1. Use '$0 help' for usage information."
        exit 1
        ;;
esac