# Docker Volume Mount Migration: Storage-Optimized Deployment

## Project Context
Migrate a TRON trading system from a storage-heavy Docker rebuild approach to an efficient volume mount strategy. The current system rebuilds 6.6GB Docker images for every code change, causing storage issues on a 50GB VM disk. The goal is to reduce storage usage by 95% and deployment time by 90% while maintaining all functionality.

## Current Problem
- Each Docker service rebuilds a 6.6GB image on every code change
- Multiple services (stock-trader, options-trader, futures-trader, main-runner, dashboard-api) each create separate large images
- 50GB VM disk fills up after just a few deployments
- Build process takes 10-15 minutes per deployment
- Storage waste: 26.4GB per deployment cycle

## Target Solution
- Single base image (2GB) containing all dependencies
- Source code mounted as volumes (no image rebuilds for code changes)
- Deployment time reduced to seconds
- Storage usage reduced from 26GB+ to ~2GB total
- Preserve all current functionality and services

## Current Architecture Analysis Needed

### 1. Analyze Current docker-compose.yml
Examine the existing docker-compose.yml structure and identify:
- All services that build custom images
- Volume mounts currently in use
- Environment variables and configurations
- Network settings and service dependencies
- Port mappings and health checks

### 2. Analyze Current Dockerfiles
For each service directory, examine Dockerfiles to understand:
- Base images being used
- System dependencies installed
- Python packages and requirements.txt usage
- File copying patterns
- Entry points and command structures
- Working directories and permissions

### 3. Identify Common Dependencies
Extract shared components across all services:
- Python version and base image
- System packages (gcc, g++, curl, etc.)
- Python packages from requirements.txt
- Environment setup (timezone, users, etc.)
- Google Cloud SDK or other tools

## Migration Requirements

### 1. Create Optimized Base Image
**Create Dockerfile.base that includes:**
- Lightweight Python base (python:3.10-slim)
- All system dependencies needed across services
- All Python packages from requirements.txt
- Google Cloud SDK (if needed for GCP integration)
- Proper working directory structure
- User setup and permissions
- **DO NOT copy application source code**

**Base image should:**
- Be reusable across all trading services
- Include all dependencies but no application code
- Be optimized for size (use multi-stage builds if needed)
- Have proper security settings
- Support both development and production environments

### 2. Update docker-compose.yml for Volume Mounts
**Transform each service to use:**
- The common base image instead of individual builds
- Volume mounts for source code directories
- Volume mounts for configuration files
- Volume mounts for logs and data directories
- Proper environment variable setup
- Command overrides to run application code from mounted volumes

**Preserve all existing:**
- Service names and networking
- Port mappings
- Environment variables
- Restart policies
- Health checks
- Dependencies between services

### 3. Create Deployment Scripts
**Generate automated deployment scripts:**

**deploy.sh:**
- Check for code changes via git
- Detect if dependencies (requirements.txt) changed
- Rebuild base image only if dependencies changed
- Restart services with new code
- Provide status feedback and error handling
- Include rollback capability

**build-base.sh:**
- Build and tag the base image
- Clean up old base images
- Verify base image functionality
- Provide build status and size information

**update-code.sh:**
- Pull latest code from git
- Restart services without rebuilding
- Verify services are running correctly
- Log deployment actions

### 4. Development Workflow Support
**Create development-friendly setup:**
- Hot reload capability for code changes
- Development environment variables
- Debug mode support
- Local development docker-compose.dev.yml
- Code volume mounts that preserve file permissions

### 5. Optimization Requirements

**Storage Optimization:**
- Minimize base image size through multi-stage builds
- Use .dockerignore to exclude unnecessary files
- Implement automatic cleanup of old images
- Configure Docker daemon for log rotation

**Performance Optimization:**
- Leverage Docker layer caching effectively
- Optimize Python package installation
- Use --no-cache-dir for pip installs
- Minimize build context size

**Security Optimization:**
- Run containers as non-root user
- Implement proper file permissions
- Secure volume mount configurations
- Environment variable security

## Implementation Instructions

### 1. File Structure Changes
Create the following new files and modify existing ones:

**New Files to Create:**
- `Dockerfile.base` - Shared base image with dependencies
- `docker-compose.volume.yml` - Volume mount configuration
- `scripts/deploy.sh` - Automated deployment script
- `scripts/build-base.sh` - Base image build script  
- `scripts/update-code.sh` - Code update script
- `.dockerignore` - Optimize build context
- `docker-compose.dev.yml` - Development environment

**Files to Modify:**
- `docker-compose.yml` - Update to use volume mounts
- Individual service Dockerfiles (remove or simplify)
- `requirements.txt` - Optimize if needed

### 2. Volume Mount Strategy
**For each service, implement:**
```yaml
service-name:
  image: tron-base  # Shared base image
  volumes:
    - ./path/to/service/code:/app/src  # Source code
    - ./config:/app/config:ro          # Configuration (read-only)
    - ./logs:/app/logs                 # Logs (read-write)
    - ./data:/app/data                 # Data persistence
  working_dir: /app
  command: ["python", "src/main.py"]  # Run from mounted code
  environment:
    - PYTHONPATH=/app/src
  restart: unless-stopped
```

### 3. Base Image Design
**Multi-stage Dockerfile.base:**
```dockerfile
# Build stage for dependencies
FROM python:3.10-slim as builder
# Install build dependencies and Python packages
# Clean up build artifacts

# Runtime stage
FROM python:3.10-slim
# Copy only installed packages from builder
# Set up runtime environment
# Create non-root user
# Do NOT copy application source code
```

### 4. Automated Deployment Logic
**deploy.sh should:**
1. Check current git commit hash
2. Pull latest changes
3. Compare old vs new commit
4. If requirements.txt changed: rebuild base image
5. If only code changed: restart services
6. Verify all services are healthy
7. Provide clear status messages
8. Handle errors gracefully

### 5. Development Experience
**Ensure developers can:**
- Make code changes and see them reflected immediately
- Debug applications easily
- Switch between development and production modes
- Access logs and monitoring data
- Run individual services for testing

## Validation Requirements

### 1. Functionality Verification
After migration, verify that:
- All trading services start successfully
- API endpoints respond correctly
- Database connections work
- External API integrations function
- Logging and monitoring operate normally
- Cognitive engine and memory systems work
- Risk management systems function properly

### 2. Performance Verification
Confirm that:
- Service startup time is under 30 seconds
- Memory usage is within expected limits
- CPU utilization is normal
- Network connectivity is maintained
- File I/O performance is acceptable

### 3. Storage Verification
Validate that:
- Total Docker storage usage is under 5GB
- No image rebuilds occur for code changes
- Base image reuse works across services
- Volume mounts have correct permissions
- Log rotation prevents disk space issues

## Error Handling and Rollback

### 1. Migration Safety
Implement safeguards:
- Backup current working docker-compose.yml
- Create rollback scripts
- Test migration on development environment first
- Provide clear migration steps and verification
- Document troubleshooting procedures

### 2. Common Issues Resolution
Address potential problems:
- File permission issues with volume mounts
- Path resolution problems in Python imports
- Environment variable differences
- Service dependency timing issues
- Network connectivity changes

## Success Criteria

### 1. Storage Reduction
- Total Docker storage usage reduced by 80%+
- No full image rebuilds for code changes
- Base image reused across all services
- Cleanup scripts maintain storage efficiency

### 2. Deployment Speed
- Code deployment time under 60 seconds
- Service restart time under 30 seconds
- Dependency updates under 5 minutes
- Zero downtime for code updates

### 3. Developer Experience
- Single command deployment
- Immediate code change reflection
- Easy debugging and logging access
- Clear error messages and status feedback

### 4. System Reliability
- All trading functionality preserved
- Service auto-restart on failure
- Proper health checks and monitoring
- Graceful handling of errors

## Implementation Notes

### 1. Preserve Existing Functionality
- Maintain all current API endpoints
- Keep existing configuration mechanisms
- Preserve logging and monitoring setups
- Maintain security and authentication
- Keep all trading logic and cognitive systems intact

### 2. Follow Best Practices
- Use official Python slim images
- Implement proper multi-stage builds
- Follow Docker security guidelines
- Use appropriate file permissions
- Implement proper signal handling

### 3. Documentation and Maintenance
- Document the new deployment process
- Create troubleshooting guides
- Provide migration rollback procedures
- Include monitoring and maintenance tasks
- Document volume mount configurations

## Expected Outcomes

After successful migration:
- **Storage Usage:** Reduced from 26GB+ to ~2GB (90%+ reduction)
- **Deployment Time:** Reduced from 15 minutes to 30 seconds (95%+ reduction)
- **Developer Productivity:** Immediate code changes, no rebuild waits
- **System Reliability:** Same functionality with improved maintainability
- **Cost Efficiency:** Smaller disk requirements, faster deployments
- **Operational Excellence:** Automated scripts, easy rollbacks, clear monitoring

This migration will transform the TRON trading system from a storage-heavy, slow-deploying setup into an efficient, developer-friendly, production-ready system while maintaining all trading functionality and performance characteristics.