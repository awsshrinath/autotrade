# Enhanced Logging Integration Guide for TRON Trading System

## Overview

This guide covers the comprehensive logging system implemented for RAG (Retrieval-Augmented Generation) and MCP (Module Context Protocol) operations in the TRON trading system. The system provides dual-layer logging to both Firestore (real-time) and GCS (archival) with proper tracing and correlation.

## Architecture

### Logging Layers

1. **Firestore Collections** (Real-time access)
   - `rag_queries` - RAG query operations
   - `rag_retrievals` - Document retrieval results
   - `rag_contexts` - Final context sent to LLM
   - `rag_responses` - LLM responses using RAG
   - `rag_embeddings` - Document embedding operations
   - `mcp_contexts` - MCP context building operations
   - `mcp_decisions` - MCP decision-making processes
   - `mcp_actions` - MCP action executions
   - `mcp_reflections` - MCP reflection and learning
   - `mcp_strategies` - Strategy evolution tracking

2. **GCS Buckets** (Archival storage in asia-south1)
   - `tron-trade-logs` - Trade entry/exit logs
   - `tron-cognitive-archives` - Historical cognitive data
   - `tron-system-logs` - System performance and debug logs
   - `tron-analytics-data` - Processed data for analysis
   - `tron-compliance-logs` - Regulatory compliance data

### Folder Structure in GCS

```
logs/
├── YYYY/
│   ├── MM/
│   │   ├── DD/
│   │   │   ├── bot_type/
│   │   │   │   ├── rag_contexts_HHMMSS_v1.json.gz
│   │   │   │   ├── mcp_decisions_HHMMSS_v1.json.gz
│   │   │   │   ├── trades_detailed_HHMMSS_v1.json.gz
│   │   │   │   └── trades_summary_HHMMSS_v1.csv.gz
```

## Implementation Details

### RAG Logging Integration

#### Enhanced RAG Logger (`gpt_runner/rag/enhanced_rag_logger.py`)

```python
from gpt_runner.rag.enhanced_rag_logger import get_rag_logger

# Initialize logger
rag_logger = get_rag_logger(session_id="trading_session_123", bot_type="stock-trader")

# Log query
trace_id = rag_logger.log_rag_query(
    query_text="Find similar trading patterns for NIFTY",
    query_embedding=embedding_vector,
    context_type="strategy_context",
    metadata={"symbol": "NIFTY", "strategy": "momentum"}
)

# Log retrieval results
rag_logger.log_rag_retrieval(
    trace_id=trace_id,
    query_id=trace_id,
    retrieved_docs=documents,
    similarity_scores=[0.85, 0.78, 0.72],
    retrieval_time_ms=45.2,
    total_searched=1000,
    threshold=0.7,
    strategy="semantic"
)
```

#### Updated Retriever (`gpt_runner/rag/retriever.py`)

The retriever now automatically logs all operations:

```python
from gpt_runner.rag.retriever import retrieve_similar_context

# Enhanced retrieval with automatic logging
results = retrieve_similar_context(
    query="trading performance analysis",
    limit=5,
    threshold=0.7,
    bot_name="futures-trader",
    session_id="session_123",
    context_type="performance_analysis"
)
```

### MCP Logging Integration

#### Enhanced MCP Logger (`mcp/enhanced_mcp_logger.py`)

```python
from mcp.enhanced_mcp_logger import get_mcp_logger, MCPDecisionType, MCPActionStatus

# Initialize logger
mcp_logger = get_mcp_logger(session_id="mcp_session_456", bot_type="options-trader")

# Log context building
context_trace_id = mcp_logger.log_mcp_context(
    context_request={"include_trades": True, "include_rag": True},
    context_sources=["firestore_trades", "rag_retrieval", "market_monitor"],
    context_data=context_dict,
    build_time_ms=120.5,
    completeness_score=0.85
)

# Log decision making
decision_trace_id = mcp_logger.log_mcp_decision(
    context_id=context_trace_id,
    decision_type=MCPDecisionType.STRATEGY_SUGGESTION,
    input_analysis={"market_trend": "bullish", "volatility": "moderate"},
    reasoning="Based on recent performance and market conditions...",
    confidence=0.78,
    actions=[{"type": "adjust_sl", "value": "2%"}],
    risk_assessment={"risk_level": "medium"},
    expected_impact={"profit_potential": "high"},
    decision_time_ms=89.3
)
```

#### Enhanced Context Builder (`mcp/context_builder.py`)

```python
from mcp.context_builder import EnhancedMCPContextBuilder

# Create enhanced context builder
builder = EnhancedMCPContextBuilder(session_id="context_session_789")

# Build comprehensive context with logging
context = builder.build_mcp_context(
    bot_name="stock-trader",
    context_request={
        "include_trades": True,
        "include_capital": True,
        "include_market": True,
        "include_rag": True,
        "include_historical": True,
        "time_range_hours": 48
    }
)
```

## Firestore Collection Schemas

### RAG Collections

#### `rag_queries`
```json
{
  "trace_id": "rag_a1b2c3d4_1640995200",
  "session_id": "trading_session_123",
  "bot_type": "stock-trader",
  "query_text": "Find similar trading patterns for NIFTY",
  "query_embedding": [0.1, 0.2, ...],
  "timestamp": "2024-01-01T10:30:00Z",
  "context_type": "strategy_context",
  "query_metadata": {
    "symbol": "NIFTY",
    "strategy": "momentum"
  }
}
```

#### `rag_retrievals`
```json
{
  "trace_id": "rag_a1b2c3d4_1640995200",
  "query_id": "rag_a1b2c3d4_1640995200",
  "retrieved_documents": [...],
  "similarity_scores": [0.85, 0.78, 0.72],
  "retrieval_time_ms": 45.2,
  "total_documents_searched": 1000,
  "threshold_used": 0.7,
  "retrieval_strategy": "semantic",
  "timestamp": "2024-01-01T10:30:01Z"
}
```

### MCP Collections

#### `mcp_contexts`
```json
{
  "trace_id": "mcp_e5f6g7h8_1640995300",
  "session_id": "mcp_session_456",
  "bot_type": "options-trader",
  "context_request": {
    "include_trades": true,
    "include_rag": true
  },
  "context_sources": ["firestore_trades", "rag_retrieval"],
  "context_data": {...},
  "build_time_ms": 120.5,
  "context_completeness": 0.85,
  "timestamp": "2024-01-01T10:35:00Z"
}
```

#### `mcp_decisions`
```json
{
  "trace_id": "mcp_i9j0k1l2_1640995400",
  "context_id": "mcp_e5f6g7h8_1640995300",
  "decision_type": "strategy_suggestion",
  "input_analysis": {
    "market_trend": "bullish",
    "volatility": "moderate"
  },
  "decision_reasoning": "Based on recent performance...",
  "confidence_score": 0.78,
  "recommended_actions": [...],
  "risk_assessment": {...},
  "expected_impact": {...},
  "decision_time_ms": 89.3,
  "timestamp": "2024-01-01T10:36:00Z"
}
```

## Sample Queries

### Firestore Queries

#### Get Recent RAG Operations for a Bot
```python
from google.cloud import firestore

db = firestore.Client()

# Get recent RAG queries for stock-trader
rag_queries = db.collection('rag_queries')\
    .where('bot_type', '==', 'stock-trader')\
    .where('timestamp', '>=', datetime.now() - timedelta(hours=24))\
    .order_by('timestamp', direction=firestore.Query.DESCENDING)\
    .limit(50)\
    .stream()

for query in rag_queries:
    print(f"Query: {query.to_dict()['query_text'][:50]}...")
```

#### Get MCP Decisions by Confidence Score
```python
# Get high-confidence MCP decisions
high_confidence_decisions = db.collection('mcp_decisions')\
    .where('confidence_score', '>=', 0.8)\
    .where('timestamp', '>=', datetime.now() - timedelta(days=7))\
    .order_by('confidence_score', direction=firestore.Query.DESCENDING)\
    .stream()

for decision in high_confidence_decisions:
    data = decision.to_dict()
    print(f"Decision: {data['decision_type']} - Confidence: {data['confidence_score']}")
```

#### Trace Complete RAG-MCP Flow
```python
# Find related logs by trace correlation
def trace_rag_mcp_flow(session_id: str):
    # Get RAG queries
    rag_queries = db.collection('rag_queries')\
        .where('session_id', '==', session_id)\
        .stream()
    
    # Get MCP contexts
    mcp_contexts = db.collection('mcp_contexts')\
        .where('session_id', '==', session_id)\
        .stream()
    
    # Get MCP decisions
    mcp_decisions = db.collection('mcp_decisions')\
        .stream()
    
    # Correlate by timestamp and trace IDs
    return {
        'rag_queries': [q.to_dict() for q in rag_queries],
        'mcp_contexts': [c.to_dict() for c in mcp_contexts],
        'mcp_decisions': [d.to_dict() for d in mcp_decisions]
    }
```

### GCS Queries

#### List Archived RAG Contexts
```python
from google.cloud import storage

client = storage.Client()
bucket = client.bucket('tron-cognitive-archives')

# List RAG context files for a specific date
blobs = bucket.list_blobs(prefix='logs/2024/01/01/stock-trader/rag_contexts')
for blob in blobs:
    print(f"RAG Context Archive: {blob.name}")
```

#### Download and Analyze Historical Data
```python
import gzip
import json

def analyze_historical_rag_performance(date_str: str, bot_type: str):
    bucket = client.bucket('tron-cognitive-archives')
    
    # List all RAG files for the date
    prefix = f'logs/{date_str.replace("-", "/")}/{bot_type}/rag_'
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    total_queries = 0
    avg_retrieval_time = 0
    
    for blob in blobs:
        if 'rag_retrievals' in blob.name:
            # Download and decompress
            compressed_data = blob.download_as_bytes()
            json_data = gzip.decompress(compressed_data).decode('utf-8')
            retrievals = json.loads(json_data)
            
            total_queries += len(retrievals)
            avg_retrieval_time += sum(r['retrieval_time_ms'] for r in retrievals)
    
    return {
        'total_queries': total_queries,
        'avg_retrieval_time_ms': avg_retrieval_time / total_queries if total_queries > 0 else 0
    }
```

## Performance Monitoring

### Real-time Dashboards

#### RAG Performance Metrics
```python
def get_rag_performance_metrics(hours: int = 24):
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=hours)
    
    # Query retrieval performance
    retrievals = db.collection('rag_retrievals')\
        .where('timestamp', '>=', start_time)\
        .stream()
    
    metrics = {
        'total_retrievals': 0,
        'avg_retrieval_time': 0,
        'avg_similarity_score': 0,
        'success_rate': 0
    }
    
    retrieval_times = []
    similarity_scores = []
    
    for retrieval in retrievals:
        data = retrieval.to_dict()
        metrics['total_retrievals'] += 1
        retrieval_times.append(data['retrieval_time_ms'])
        similarity_scores.extend(data['similarity_scores'])
    
    if retrieval_times:
        metrics['avg_retrieval_time'] = sum(retrieval_times) / len(retrieval_times)
        metrics['avg_similarity_score'] = sum(similarity_scores) / len(similarity_scores)
        metrics['success_rate'] = len([t for t in retrieval_times if t < 100]) / len(retrieval_times)
    
    return metrics
```

#### MCP Decision Analysis
```python
def analyze_mcp_decision_patterns(days: int = 7):
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    decisions = db.collection('mcp_decisions')\
        .where('timestamp', '>=', start_time)\
        .stream()
    
    analysis = {
        'decision_types': {},
        'confidence_distribution': [],
        'avg_decision_time': 0,
        'success_patterns': {}
    }
    
    for decision in decisions:
        data = decision.to_dict()
        
        # Count decision types
        decision_type = data['decision_type']
        analysis['decision_types'][decision_type] = analysis['decision_types'].get(decision_type, 0) + 1
        
        # Track confidence
        analysis['confidence_distribution'].append(data['confidence_score'])
        
        # Track decision time
        analysis['avg_decision_time'] += data['decision_time_ms']
    
    return analysis
```

## Error Handling and Fallbacks

### Graceful Degradation
```python
# RAG with fallback
def safe_rag_retrieval(query: str, bot_name: str):
    try:
        return retrieve_similar_context(query, bot_name=bot_name)
    except Exception as e:
        # Log error and return empty results
        print(f"RAG retrieval failed: {e}")
        return []

# MCP with fallback
def safe_mcp_context(bot_name: str):
    try:
        builder = EnhancedMCPContextBuilder()
        return builder.build_mcp_context(bot_name)
    except Exception as e:
        # Return minimal context
        return {
            "bot": bot_name,
            "error": str(e),
            "actions_allowed": ["log_reflection"]
        }
```

## Lifecycle Management

### Automatic Cleanup
- GCS lifecycle policies automatically delete old logs
- Firestore TTL removes expired documents
- Version tracking prevents duplicate uploads

### Cost Optimization
- Compressed storage (gzip) reduces costs by ~70%
- Batched uploads minimize API calls
- Regional storage (asia-south1) reduces latency and costs

## Integration Checklist

- [x] RAG enhanced logging implemented
- [x] MCP enhanced logging implemented
- [x] Firestore collections configured
- [x] GCS buckets with lifecycle policies
- [x] Trace correlation system
- [x] Performance monitoring queries
- [x] Error handling and fallbacks
- [x] Documentation and examples

## Next Steps

1. **Deploy Enhanced Loggers**: Update all RAG and MCP modules
2. **Configure Monitoring**: Set up dashboards for real-time metrics
3. **Test Integration**: Verify logging across all trading bots
4. **Optimize Performance**: Monitor and tune based on usage patterns
5. **Extend Analytics**: Build ML models on logged data for insights 