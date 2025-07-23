#!/bin/bash

# TRON Trading System - Base Image Builder
# Builds the optimized base image with all dependencies

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
BASE_IMAGE_NAME="tron-base"
BASE_IMAGE_TAG="latest"
LOG_FILE="$PROJECT_DIR/logs/build-base.log"

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

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    
    if ! docker info &> /dev/null; then
        error_exit "Docker daemon is not running"
    fi
    
    if [ ! -f "$PROJECT_DIR/requirements.txt" ]; then
        error_exit "requirements.txt not found in project root"
    fi
    
    if [ ! -f "$PROJECT_DIR/Dockerfile.base" ]; then
        error_exit "Dockerfile.base not found in project root"
    fi
    
    success "Prerequisites check passed"
}

# Clean up old images
cleanup_old_images() {
    info "Cleaning up old base images..."
    
    # Remove old tron-base images (keep latest)
    OLD_IMAGES=$(docker images "$BASE_IMAGE_NAME" --format "table {{.Repository}}:{{.Tag}} {{.ID}}" | grep -v "latest" | awk '{print $2}' | head -n -1 || true)
    
    if [ -n "$OLD_IMAGES" ]; then
        echo "$OLD_IMAGES" | xargs -r docker rmi || warning "Some old images could not be removed"
        success "Old images cleaned up"
    else
        info "No old images to clean up"
    fi
}

# Build base image
build_base_image() {
    info "Building TRON base image..."
    
    cd "$PROJECT_DIR"
    
    # Get requirements hash for cache busting
    REQUIREMENTS_HASH=$(sha256sum requirements.txt | cut -d' ' -f1 | head -c 8)
    
    # Build the base image
    docker build \
        -f Dockerfile.base \
        -t "$BASE_IMAGE_NAME:$BASE_IMAGE_TAG" \
        -t "$BASE_IMAGE_NAME:$REQUIREMENTS_HASH" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        . || error_exit "Failed to build base image"
    
    success "Base image built successfully"
}

# Verify base image
verify_base_image() {
    info "Verifying base image functionality..."
    
    # Test that Python and packages are working
    info "Testing Python and basic dependencies..."
    if ! docker run --rm "$BASE_IMAGE_NAME:$BASE_IMAGE_TAG" python -c "import sys; print('Python', sys.version)"; then
        error_exit "Base image Python test failed"
    fi
    
    info "Testing FastAPI and core dependencies..."
    IMPORT_TEST=$(docker run --rm "$BASE_IMAGE_NAME:$BASE_IMAGE_TAG" python -c "
try:
    import fastapi, uvicorn, asyncio
    print('Core dependencies OK')
except ImportError as e:
    print('Import error:', e)
    exit(1)
" 2>&1)
    
    if echo "$IMPORT_TEST" | grep -q "Core dependencies OK"; then
        success "Base image verification passed"
    else
        warning "Base image verification failed with output:"
        echo "$IMPORT_TEST"
        error_exit "Base image verification failed - check dependencies"
    fi
}

# Show image information
show_image_info() {
    info "Base Image Information:"
    
    IMAGE_SIZE=$(docker images "$BASE_IMAGE_NAME:$BASE_IMAGE_TAG" --format "table {{.Size}}" | tail -n +2)
    IMAGE_ID=$(docker images "$BASE_IMAGE_NAME:$BASE_IMAGE_TAG" --format "table {{.ID}}" | tail -n +2)
    
    echo "📦 Image: $BASE_IMAGE_NAME:$BASE_IMAGE_TAG"
    echo "🆔 ID: $IMAGE_ID"
    echo "📏 Size: $IMAGE_SIZE"
    echo "🕒 Built: $(date)"
}

# Main build process
build_base() {
    log "${BLUE}🏗️  Starting TRON base image build...${NC}"
    
    check_prerequisites
    cleanup_old_images
    build_base_image
    
    # Skip verification if --skip-verify flag is passed
    if [ "$1" != "--skip-verify" ]; then
        verify_base_image
    else
        info "Skipping verification as requested"
    fi
    
    show_image_info
    
    success "🎉 Base image build completed successfully!"
    info "💡 You can now run: ./scripts/deploy.sh to deploy with the new base image"
}

# Handle command line arguments
case "${1:-build}" in
    "build"|"")
        build_base "$2"
        ;;
    "clean")
        info "Cleaning up all TRON base images..."
        docker images "$BASE_IMAGE_NAME" -q | xargs -r docker rmi || warning "Some images could not be removed"
        success "Base images cleaned up"
        ;;
    "info")
        show_image_info
        ;;
    "verify")
        verify_base_image
        ;;
    "help")
        echo "TRON Base Image Builder"
        echo ""
        echo "Usage: $0 [command] [options]"
        echo ""
        echo "Commands:"
        echo "  build [--skip-verify]  - Build the base image (default)"
        echo "  clean                  - Remove all base images"
        echo "  info                   - Show base image information"
        echo "  verify                 - Verify base image functionality"
        echo "  help                   - Show this help message"
        echo ""
        echo "Options:"
        echo "  --skip-verify         - Skip verification step during build"
        ;;
    *)
        error_exit "Unknown command: $1. Use '$0 help' for usage information."
        ;;
esac