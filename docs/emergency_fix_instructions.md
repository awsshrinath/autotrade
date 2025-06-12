# Emergency Fix Instructions

## Problem Summary

The main runner was crashing due to several critical issues:

1. **Secret Manager Permission Errors** - 403 errors accessing OpenAI API key
2. **Firestore Permission Errors** - 403 errors logging to Firestore  
3. **GCS Permission Errors** - 403 errors accessing storage buckets
4. **Logger Interface Mismatches** - `'Logger' object has no attribute 'error'`
5. **Missing RAG Modules** - `gpt_runner.rag` modules not available
6. **Cognitive System Initialization Failures** - Logger compatibility issues

## Solution: Enhanced Main Runner with Fallbacks

I've created several enhanced modules with comprehensive error handling and fallbacks:

### 1. Enhanced Main Runner (`runner/main_runner_fixed.py`)

**Key Features:**
- ✅ **Comprehensive Error Handling** for all GCP service failures
- ✅ **Safe Module Imports** with fallback alternatives
- ✅ **Logger Interface Adapter** to handle different logger types
- ✅ **Emergency Mode Operation** when services are unavailable
- ✅ **Paper Trading Integration** with fallback market data
- ✅ **Graceful Degradation** of features when components fail

### 2. Enhanced OpenAI Manager (`runner/enhanced_openai_manager.py`)

**Key Features:**
- ✅ **Multiple API Key Sources** (Environment, Secret Manager, Local File)
- ✅ **Fallback Responses** when OpenAI is unavailable
- ✅ **Rule-based Strategy Selection** when GPT fails
- ✅ **Comprehensive Error Handling** for all OpenAI operations

### 3. Enhanced Cognitive System (`runner/enhanced_cognitive_system.py`)

**Key Features:**
- ✅ **Logger Interface Compatibility** with all logger types
- ✅ **Fallback Mode Operation** when cognitive modules are missing
- ✅ **Safe Imports** with alternative implementations
- ✅ **Graceful Error Handling** for all cognitive operations

### 4. Emergency Configuration (`config/emergency_config.py`)

**Key Features:**
- ✅ **Emergency Mode Settings** for degraded operations
- ✅ **Default Strategies** when selection fails
- ✅ **Component Status Tracking** for system health monitoring
- ✅ **Safe Environment Setup** without external dependencies

## How to Use the Fixed Runner

### Option 1: Direct Replacement (Recommended)

Replace the main runner with the fixed version:

```bash
# Backup original runner
cp runner/main_runner_combined.py runner/main_runner_combined.py.backup

# Use the fixed runner
cp runner/main_runner_fixed.py runner/main_runner_combined.py
```

### Option 2: Run Fixed Runner Directly

```bash
# Run the enhanced runner directly
python runner/main_runner_fixed.py
```

### Option 3: Emergency Mode

For maximum compatibility when all GCP services fail:

```bash
# Setup emergency environment
python config/emergency_config.py

# Run with emergency settings
EMERGENCY_MODE=true python runner/main_runner_fixed.py
```

## Expected Behavior with Fixed Runner

### Startup Sequence

```
🚀 TRON AUTOTRADE SYSTEM - ENHANCED STARTUP
============================================================
Current working directory: /app
Python path: ['', '/app', '/usr/local/lib/python310.zip']
✅ Basic Python modules imported successfully
✅ runner package found
⚠️ gpt_runner package not found: No module named 'gpt_runner'
✅ Basic import validation completed
Starting application...
✅ Logger imported
⚠️ TradingLogger import failed: [error details]
⚠️ FirestoreClient import failed: [permission errors]
✅ Enhanced OpenAI Manager imported
✅ Enhanced Cognitive System imported
⚠️ KiteConnectManager import failed: [permission errors]
✅ Paper Trading Manager imported
Warning: RAG modules not available: [expected]
Warning: Could not import RAG modules: [expected]
```

### Component Status Display

```
📊 Components Status:
   Logger: runner.logger
   Enhanced Logger: ❌
   Firestore: ❌
   OpenAI: ⚠️ (fallback mode)
   Cognitive System: ⚠️ (fallback mode)
   Kite Manager: ❌
   Paper Trading: ✅
   Trading Mode: PAPER
```

### Graceful Operation

- **All permission errors are caught and logged as warnings**
- **System continues operating with available components**
- **Paper trading works even when other services fail**
- **Fallback strategies and market data are used when needed**
- **Comprehensive logging shows what's working and what's not**

## Testing the Fix

### 1. Test Enhanced OpenAI Manager

```bash
python -c "
from runner.enhanced_openai_manager import EnhancedOpenAIManager
import logging
logger = logging.getLogger('test')
manager = EnhancedOpenAIManager(logger)
print('Status:', manager.get_status())
print('Available:', manager.is_available())
"
```

### 2. Test Enhanced Cognitive System

```bash
python -c "
from runner.enhanced_cognitive_system import initialize_enhanced_cognitive_system
import logging
logger = logging.getLogger('test')
system = initialize_enhanced_cognitive_system(logger)
print('System available:', system.available if system else 'None')
"
```

### 3. Test Paper Trading

```bash
python test_paper_trader.py
```

## Resolving Permission Issues (Long-term)

While the fixed runner works around permission issues, here's how to resolve them permanently:

### 1. GCP Service Account Permissions

Ensure your service account has these permissions:
```
secretmanager.versions.access
storage.buckets.get
storage.objects.get
firebase.databases.get
datastore.entities.create
```

### 2. Environment Variables

Set these for proper authentication:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export OPENAI_API_KEY="your-openai-api-key"
export PAPER_TRADE="true"
```

### 3. Firestore Rules

Update Firestore security rules to allow the service account access:
```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /{document=**} {
      allow read, write: if request.auth != null;
    }
  }
}
```

## Monitoring System Health

The fixed runner provides comprehensive health monitoring:

### 1. Startup Diagnostics
- Component availability status
- Import success/failure tracking
- Permission error detection

### 2. Runtime Monitoring
- Service health checks
- Fallback mode detection
- Error rate tracking

### 3. Graceful Degradation
- Continues operation with partial services
- Provides meaningful fallback responses
- Maintains paper trading capability

## Summary

The enhanced main runner fixes all the critical startup issues:

- ✅ **No more crashes** due to permission errors
- ✅ **Graceful handling** of missing modules
- ✅ **Logger compatibility** across different systems
- ✅ **Paper trading works** even when other services fail
- ✅ **Comprehensive error reporting** for debugging
- ✅ **Production-ready** with proper fallbacks

The system will now start successfully and operate in a degraded but functional mode until the underlying permission issues are resolved. 