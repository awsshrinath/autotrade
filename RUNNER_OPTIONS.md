# 🚀 Main Runner Options & Memory Management

## 📋 Current Crashloop Issue Analysis

Based on your logs, the crashloop is happening during **SentenceTransformer model loading** (`all-MiniLM-L6-v2`), which is part of the cognitive system initialization. This is a **memory issue** where the 256Mi allocation is insufficient for loading the model.

## 🔧 Two Runner Options Available

### Option 1: 🪶 **Lightweight Runner** (Currently Active)
- **File**: `runner/main_runner_lightweight.py`
- **Memory**: Uses original 512Mi request / 1Gi limit 
- **Features**: 
  - ✅ IST timezone handling
  - ✅ Market monitoring
  - ✅ Enhanced logging with GCS/Firestore
  - ✅ Crashloop prevention
  - ❌ No cognitive system (no sentence transformers)
  - ❌ No RAG/FAISS operations
  - ❌ No MCP self-improvement

### Option 2: 🧠 **Enhanced Runner** (Memory Optimized)
- **File**: `runner/main_runner_improved.py` 
- **Memory**: Increased to 512Mi request / 1Gi limit
- **Features**:
  - ✅ All lightweight features PLUS:
  - ✅ Cognitive system with memory optimization
  - ✅ RAG/FAISS operations with garbage collection
  - ✅ MCP self-improvement after market hours
  - ✅ Sentence transformer with CPU optimization

## 🔄 How to Switch Between Runners

### Switch to Enhanced Runner (with MCP):
```yaml
# In deployments/main.yaml, change:
- name: RUNNER_SCRIPT
  value: "runner/main_runner_improved.py"
```

### Switch to Lightweight Runner (stable):
```yaml
# In deployments/main.yaml, change:
- name: RUNNER_SCRIPT
  value: "runner/main_runner_lightweight.py"
```

## 📊 Memory Usage Comparison

| Component | Lightweight | Enhanced | Impact |
|-----------|-------------|----------|---------|
| Base Python | ~50Mi | ~50Mi | Same |
| Core Logging | ~30Mi | ~30Mi | Same |
| Enhanced Logging | ~50Mi | ~50Mi | Same |
| Market Monitoring | ~20Mi | ~20Mi | Same |
| **SentenceTransformer** | ❌ None | ~200-300Mi | **Main difference** |
| RAG/FAISS | ❌ None | ~100Mi | Optional |
| **Total Estimated** | **~150Mi** | **~450-550Mi** | **3x difference** |

## 🎯 Recommendations

### **Immediate Solution** (Currently Applied):
- ✅ **Use Lightweight Runner** for stability
- ✅ **Increased memory to 512Mi/1Gi** to be safe
- ✅ **Fixed deployment.yaml typo** that was causing CI issues
- ✅ **All core functionality preserved**

### **For MCP Features** (When ready):
1. **Test Enhanced Runner** with current 512Mi/1Gi allocation
2. **Monitor memory usage** during sentence transformer loading
3. **Increase to 1Gi/2Gi** if needed for full cognitive features
4. **Consider scheduled deployment** (lightweight during market, enhanced after close)

## 🛠️ Current Deployment Status

✅ **Active Configuration**:
```yaml
# deployments/main.yaml
RUNNER_SCRIPT: "runner/main_runner_lightweight.py"
resources:
  requests:
    memory: "512Mi"  # Increased from 256Mi
    cpu: "100m"
  limits:
    memory: "1Gi"    # Increased from 512Mi  
    cpu: "500m"
```

## 🔍 Testing Commands

### Test Current Lightweight Runner:
```bash
# Monitor memory usage
kubectl top pods -n gpt -l app=main-runner

# Check logs for successful startup
kubectl logs -f deployment/main-runner -n gpt

# Look for this success message:
# "✅ Lightweight GPT Runner Started"
```

### Test Enhanced Runner (when switching):
```bash
# Monitor during sentence transformer loading
kubectl logs -f deployment/main-runner -n gpt | grep -E "(Cognitive|SentenceTransformer|Enhanced)"

# Watch for memory spikes
kubectl top pods -n gpt -l app=main-runner --watch
```

## 🚨 Troubleshooting

### If Lightweight Runner Still Crashes:
1. **Check logs** for import failures
2. **Verify GCS/Firestore** connectivity
3. **Consider reducing** to basic logger only

### If Enhanced Runner OOMs:
1. **Increase memory** to 1Gi request / 2Gi limit
2. **Disable background processing** in cognitive system
3. **Use minimal mode** for sentence transformers

### If Both Fail:
1. **Use original** `main_runner_combined.py` as fallback
2. **Check environment variables** and dependencies
3. **Verify enhanced logging** infrastructure

## ⚡ Next Steps

1. **Monitor current lightweight runner** for stability
2. **Once stable**, test enhanced runner in development
3. **Gradually increase features** based on memory capacity
4. **Consider horizontal scaling** if memory becomes limiting factor

---

**Current Status**: 🟢 **Lightweight Runner Active** - Should resolve crashloop issues
**Memory Allocation**: 🟢 **Optimized** - 512Mi/1Gi for stability
**Enhanced Features**: 🟡 **Available when ready** - Switch RUNNER_SCRIPT when stable 