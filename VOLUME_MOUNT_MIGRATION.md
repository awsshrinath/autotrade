# TRON Trading System - Volume Mount Migration Guide

## 🎯 Migration Benefits

This migration transforms your TRON system from storage-heavy Docker rebuilds to efficient volume mounts:

- **Storage Usage**: Reduced from 26GB+ to ~2GB (90%+ reduction)
- **Deployment Time**: Reduced from 15 minutes to 30 seconds (95%+ reduction)
- **Developer Experience**: Code changes apply instantly, no rebuilds needed
- **Cost Efficiency**: Smaller disk requirements, faster iterations

## 📋 Pre-Migration Checklist

1. **Backup Current System**:
   ```bash
   cp docker-compose.yml docker-compose.yml.backup
   cp -r logs logs_backup
   ```

2. **Ensure Prerequisites**:
   - Docker and Docker Compose installed
   - At least 5GB free disk space (for migration)
   - Git repository (optional, for automated updates)

3. **Stop Current Services**:
   ```bash
   docker-compose down
   ```

## 🚀 Migration Steps

### Step 1: Build Base Image
```bash
# Build the optimized base image with all dependencies
./scripts/build-base.sh

# Verify the base image
./scripts/build-base.sh verify
```

### Step 2: Deploy with Volume Mounts
```bash
# Deploy using the new volume mount configuration
./scripts/deploy.sh

# Monitor deployment progress
./scripts/deploy.sh logs
```

### Step 3: Verify Migration Success
```bash
# Check service status
./scripts/deploy.sh status

# Test all endpoints
curl http://localhost:8080/health  # Main runner
curl http://localhost:8081/health  # Stock trader
curl http://localhost:8082/health  # Options trader
curl http://localhost:8083/health  # Futures trader
curl http://localhost:8090/health  # Dashboard API
curl http://localhost:3000         # Frontend
```

## 🛠️ New Deployment Workflow

### Daily Development Workflow
```bash
# Make code changes in your favorite editor
# Changes are immediately available in containers (no rebuild needed!)

# Update code from git and restart services
./scripts/update-code.sh

# Or restart just one service
./scripts/update-code.sh service stock-trader
```

### Dependency Updates
```bash
# Only when requirements.txt changes
./scripts/deploy.sh rebuild
```

### Quick Operations
```bash
# View logs
./scripts/deploy.sh logs [service-name]

# Check status
./scripts/deploy.sh status

# Stop all services  
./scripts/deploy.sh stop

# Restart all services
./scripts/deploy.sh restart
```

## 📁 File Structure Changes

### New Files Created:
- `Dockerfile.base` - Optimized base image with dependencies
- `docker-compose.volume.yml` - Volume mount configuration
- `docker-compose.dev.yml` - Development environment
- `scripts/deploy.sh` - Main deployment script
- `scripts/build-base.sh` - Base image builder
- `scripts/update-code.sh` - Code update without rebuild
- `VOLUME_MOUNT_MIGRATION.md` - This guide

### Key Differences:
- **Before**: Each service built its own 6GB image
- **After**: All services share one 2GB base image + volume mounts
- **Code Changes**: No image rebuilds, just service restarts
- **Dependencies**: Base image rebuild only when requirements.txt changes

## 🔧 Development Mode

For active development with hot reload:

```bash
# Use development compose file
docker-compose -f docker-compose.dev.yml up -d

# Features:
# - Hot reload enabled
# - Debug ports exposed (5678-5683)
# - Read-write volume mounts
# - No auto-restart (easier debugging)
```

## 📊 Storage Monitoring

Monitor your storage usage:

```bash
# Check Docker storage usage
docker system df

# Check image sizes
docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"

# Clean up old images (optional)
docker system prune -f
```

## 🚨 Troubleshooting

### Common Issues:

1. **Permission Errors**:
   ```bash
   # Fix volume mount permissions
   sudo chown -R 1001:1001 logs/ data/
   ```

2. **Service Won't Start**:
   ```bash
   # Check logs for specific service
   ./scripts/deploy.sh logs service-name
   
   # Verify base image
   ./scripts/build-base.sh verify
   ```

3. **Module Import Errors**:
   ```bash
   # Ensure Python path is correct
   docker exec -it tron-main-runner python -c "import sys; print(sys.path)"
   ```

4. **Performance Issues**:
   ```bash
   # Check resource usage
   docker stats
   
   # Monitor service health
   ./scripts/deploy.sh status
   ```

### Rollback Procedure:

If migration fails, rollback to original setup:

```bash
# Stop volume mount deployment
./scripts/deploy.sh stop

# Restore original compose file
cp docker-compose.yml.backup docker-compose.yml

# Start with original configuration
docker-compose up -d
```

## 🎯 Success Validation

Your migration is successful when:

- ✅ All services start and pass health checks
- ✅ API endpoints respond correctly
- ✅ Frontend loads and displays data
- ✅ Trading functionality works as before
- ✅ Logs are being written correctly
- ✅ Code changes apply without rebuilds
- ✅ Total Docker storage < 5GB

## 📈 Performance Expectations

### Before Migration:
- **Storage**: 26GB+ (multiple 6GB images)
- **Deployment**: 15+ minutes (full rebuilds)
- **Code Changes**: 10+ minutes (rebuild + deploy)

### After Migration:
- **Storage**: ~2GB (single base image + volumes)
- **Deployment**: 30 seconds (volume mounts)
- **Code Changes**: 10 seconds (service restart only)

## 🔄 Maintenance

### Weekly Tasks:
```bash
# Update base image if dependencies changed
./scripts/build-base.sh

# Clean up old Docker resources
docker system prune -f
```

### Monthly Tasks:
```bash
# Update all code and dependencies
git pull
./scripts/deploy.sh rebuild
```

## 💡 Best Practices

1. **Version Control**: Commit all configuration changes
2. **Monitoring**: Regularly check service health and logs
3. **Backups**: Keep backups of working configurations
4. **Testing**: Test changes in development mode first
5. **Documentation**: Update team on new deployment procedures

## 🎉 Migration Complete!

Your TRON trading system now uses efficient volume mounts for:
- 🚀 Faster deployments
- 💾 Minimal storage usage  
- ⚡ Instant code updates
- 🛠️ Better developer experience
- 💰 Reduced infrastructure costs

Happy trading! 📈