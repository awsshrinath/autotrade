# TRON Trading System - Container Health Troubleshooting Guide

## Issue Summary
**Date**: 2025-07-24  
**Problem**: All Docker containers except nginx showing as "unhealthy" after deployment  
**Root Cause**: Docker build process failed to properly install Python dependencies from `requirements.txt`

## Diagnostic Steps Taken

### 1. Initial Container Status Assessment
```bash
docker-compose ps
docker ps -a
```

**Found**: All containers running but marked as unhealthy:
- `tron-main-runner`: Up (unhealthy)
- `tron-stock-trader`: Up (unhealthy) 
- `tron-options-trader`: Up (unhealthy)
- `tron-futures-trader`: Up (unhealthy)
- `tron-dashboard-api`: Up (unhealthy)
- `tron-frontend`: Up (unhealthy)
- `tron-log-aggregator`: Up (unhealthy)
- `tron-nginx`: Up (healthy) ✅

### 2. Health Check Analysis
```bash
curl -f -v http://localhost:8080/health  # Returns 503 Service Unavailable
curl -s http://localhost:8080/status | jq .
```

**Found**: Health server returning 503 with status "error" and message "Script failed after 3 attempts"

### 3. Container Log Analysis
```bash
docker-compose logs --tail=50 main-runner
docker-compose logs --tail=50 stock-trader
```

**Found**: 
- Script import test failures
- Warnings about missing PyYAML and pytz
- Trading scripts failing with exit code 1

### 4. Root Cause Identification
```bash
docker exec tron-main-runner python3 /app/runner/main_runner.py
```

**Found**: `ModuleNotFoundError: No module named 'pytz'`

Further investigation revealed missing critical dependencies:
- `pytz` - timezone handling
- `PyYAML` - YAML configuration parsing  
- `requests` - HTTP client library
- `kiteconnect` - trading platform API
- `pandas`, `numpy` - data processing
- `faiss-cpu` - machine learning operations
- Google Cloud packages - cloud services
- `openai` - AI integration

## Applied Fixes

### 1. Install Missing Basic Dependencies
```bash
# Install in all trading containers
docker exec --user appuser tron-main-runner pip install pytz pyyaml
docker exec --user appuser tron-stock-trader pip install pytz pyyaml  
docker exec --user appuser tron-options-trader pip install pytz pyyaml
docker exec --user appuser tron-futures-trader pip install pytz pyyaml
```

### 2. Install Core Application Dependencies
```bash
# Install critical application packages
docker exec --user appuser tron-stock-trader pip install requests pandas numpy
docker exec --user appuser tron-options-trader pip install requests pandas numpy
docker exec --user appuser tron-futures-trader pip install requests pandas numpy
```

### 3. Install Trading Platform Dependencies
```bash
# Install trading and cloud service dependencies
docker exec --user appuser tron-stock-trader pip install kiteconnect fastapi uvicorn google-cloud-firestore google-cloud-secret-manager openai
docker exec --user appuser tron-options-trader pip install kiteconnect fastapi uvicorn google-cloud-firestore google-cloud-secret-manager openai  
docker exec --user appuser tron-futures-trader pip install kiteconnect fastapi uvicorn google-cloud-firestore google-cloud-secret-manager openai
```

### 4. Install ML/AI Dependencies (Large packages - still in progress)
```bash
# Install machine learning packages (takes significant time)
docker exec --user appuser tron-stock-trader pip install faiss-cpu sentence-transformers scikit-learn
docker exec --user appuser tron-options-trader pip install faiss-cpu sentence-transformers scikit-learn
docker exec --user appuser tron-futures-trader pip install faiss-cpu sentence-transformers scikit-learn
docker exec --user appuser tron-main-runner pip install faiss-cpu sentence-transformers scikit-learn
```

### 5. Fix Dockerfile for Future Builds
Updated `/opt/tron-trading/autotrade/Dockerfile`:

```dockerfile
# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy requirements.txt for reference
COPY requirements.txt /app/requirements.txt

# Make sure scripts in .local are usable
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/home/appuser/.local/lib/python3.10/site-packages:$PYTHONPATH
```

### 6. Restart Containers
```bash
docker-compose restart main-runner stock-trader options-trader futures-trader
```

## Current Status (2025-07-24 09:20 UTC)

### ✅ Fixed Containers
- **tron-nginx**: Healthy
- **tron-main-runner**: Healthy (returns 200 on /health endpoint)

### ⚠️ In Progress
- **tron-stock-trader**: Installing ML dependencies
- **tron-options-trader**: Installing ML dependencies  
- **tron-futures-trader**: Installing ML dependencies

### ❌ Still Need Fixing
- **tron-dashboard-api**: Needs dependency installation
- **tron-frontend**: Needs investigation (likely different issues)
- **tron-log-aggregator**: Needs dependency installation

## Verification Commands

### Check Container Status
```bash
docker-compose ps
```

### Check Health Endpoints
```bash
curl -s http://localhost:8080/health | jq .  # main-runner
curl -s http://localhost:8081/health | jq .  # stock-trader
curl -s http://localhost:8082/health | jq .  # options-trader
curl -s http://localhost:8083/health | jq .  # futures-trader
curl -s http://localhost:8090/health | jq .  # dashboard-api
curl -s http://localhost:8095/health | jq .  # log-aggregator
curl -s http://localhost:3000 | head -20     # frontend
```

### Check Detailed Status
```bash
curl -s http://localhost:8080/status | jq .
```

### Test Manual Script Execution
```bash
docker exec --user appuser tron-stock-trader python3 -c "
import sys
sys.path.insert(0, '/app')
try:
    from stock_trading.stock_runner import *
    print('✅ stock_runner imported successfully')
except Exception as e:
    print(f'❌ Import failed: {e}')
"
```

## Remaining Tasks

### 1. Complete ML Dependency Installation
Wait for the following installations to complete (may take 10-15 minutes):
- `faiss-cpu` (31.3 MB)
- `sentence-transformers` with dependencies including:
  - `torch` (821.2 MB) 
  - `transformers` (10.8 MB)
  - NVIDIA CUDA packages (multiple GB)

### 2. Fix Dashboard API Container
Apply similar dependency fixes:
```bash
docker exec --user appuser tron-dashboard-api pip install -r /app/requirements.txt
# Or install specific missing packages as identified
```

### 3. Fix Log Aggregator Container  
```bash
docker exec --user appuser tron-log-aggregator pip install -r /app/requirements.txt
```

### 4. Investigate Frontend Container
Frontend uses Next.js, likely different issue (port binding, build problems, etc.)

### 5. Rebuild Docker Images (Recommended)
Once all fixes are confirmed working:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## Prevention Measures

### 1. Fix Docker Build Process
The root issue was incomplete dependency installation during Docker build. The builder stage properly installed packages but the final stage had path/permission issues.

### 2. Add Dependency Validation
Consider adding a validation step in `entrypoint.sh`:
```bash
# Validate critical imports before starting health server
python3 -c "import pytz, yaml, requests, kiteconnect, pandas, numpy" || exit 1
```

### 3. Improve Health Checks
The health check system worked correctly in identifying the issues. Consider adding more specific error reporting for missing dependencies.

## Key Learnings

1. **Multi-stage Docker builds** can have path/permission issues between stages
2. **Health check timeouts** should account for large dependency installations
3. **Container startup order** matters when dependencies are being installed
4. **User permissions** in containers can affect package installation locations
5. **ML packages** are very large and significantly increase build/startup time

## Files Modified

1. `/opt/tron-trading/autotrade/Dockerfile` - Added requirements.txt copy and fixed paths
2. `/opt/tron-trading/autotrade/TROUBLESHOOTING.md` - This documentation file

## Emergency Recovery Commands

If containers fail to start after fixes:

```bash
# Reset to original state
docker-compose down
docker-compose up -d

# Check logs for specific errors
docker-compose logs [service-name]

# Access container for debugging
docker exec -it [container-name] /bin/bash

# Reset user packages if corrupted
docker exec [container-name] rm -rf /home/appuser/.local
docker-compose restart [service-name]
```

---

**Next Session Resume Point**: Check ML dependency installation progress and apply fixes to dashboard-api and log-aggregator containers. Frontend container needs separate investigation for Next.js specific issues.