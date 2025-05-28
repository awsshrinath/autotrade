# Enhanced Logging System Documentation

## Overview

The Enhanced Logging System provides comprehensive, structured logging for the TRON Trading System with integrated Firestore and Google Cloud Storage (GCS) bucket support. It offers real-time logging, batch processing, categorized logging, and automatic data persistence across multiple storage backends.

## Key Features

### 🎯 Structured Logging
- **Categorized Logs**: System, Trade, Position, Strategy, Risk, Performance, Error, Cognitive, Market Data, Recovery
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Rich Metadata**: Automatic tagging with trade IDs, position IDs, symbols, strategies, and bot types
- **JSON Format**: All logs stored in structured JSON format for easy parsing and analysis

### 🔄 Multi-Backend Storage
- **Local Files**: Organized by date and category in `logs/YYYY-MM-DD/` structure
- **Firestore**: Real-time structured data storage with automatic indexing
- **GCS Buckets**: Compressed, archived logs for long-term storage and analysis
- **Automatic Failover**: Graceful degradation if cloud services are unavailable

### ⚡ Performance Optimized
- **Asynchronous Processing**: Background threads for non-blocking log operations
- **Batch Operations**: Efficient bulk uploads to reduce API calls
- **Buffer Management**: Configurable buffer sizes and flush intervals
- **Compression**: Automatic gzip compression for GCS uploads

### 🛡️ Reliability Features
- **Error Handling**: Comprehensive error handling with automatic retries
- **Graceful Shutdown**: Proper cleanup and final data flush on system exit
- **Performance Monitoring**: Built-in metrics tracking for logging system performance
- **Recovery Support**: Automatic recovery from system crashes

## Architecture

### Core Components

```
Enhanced Logger
├── LogEntry (Structured log data)
├── Local File Writer (Immediate local storage)
├── Background Processor (Async operations)
├── Firestore Uploader (Real-time cloud storage)
├── GCS Uploader (Archived storage)
└── Performance Monitor (Metrics tracking)
```

### Data Flow

```
Log Event → Queue → Background Processor → [Local Files + Firestore + GCS]
```

## Configuration

### Environment Variables

```bash
# Required for GCS integration
export GCP_PROJECT_ID="your-project-id"
export ENVIRONMENT="prod"  # or "dev", "staging"

# Optional configuration
export ENHANCED_LOGGING_BUFFER_SIZE="50"
export ENHANCED_LOGGING_FLUSH_INTERVAL="30"
export ENHANCED_LOGGING_ENABLE_GCS="true"
export ENHANCED_LOGGING_ENABLE_FIRESTORE="true"
```

### GCS Bucket Setup

Before using the enhanced logging system, create the required GCS buckets:

```bash
# Create buckets using the provided script
./scripts/create_gcs_buckets.sh -p your-project-id -r asia-south1
```

**Required Buckets:**
- `tron-trading-logs` - General system and application logs
- `tron-trade-data` - Trade execution and position data
- `tron-analysis-reports` - Performance metrics and analysis reports
- `tron-memory-backups` - System recovery and backup data

## Usage

### Basic Usage

```python
from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory

# Create logger instance
logger = create_enhanced_logger(
    session_id="my_trading_session",
    enable_gcs=True,
    enable_firestore=True
)

# Basic logging
logger.log_event(
    "System started successfully",
    LogLevel.INFO,
    LogCategory.SYSTEM,
    data={'startup_time': '2024-01-15T09:30:00'},
    source="main_system"
)
```

### Trade Logging

```python
# Log successful trade execution
trade_data = {
    'id': 'TRADE_001',
    'symbol': 'RELIANCE',
    'strategy': 'momentum',
    'direction': 'bullish',
    'quantity': 10,
    'entry_price': 2500.0,
    'stop_loss': 2450.0,
    'target': 2600.0,
    'bot_type': 'stock',
    'paper_trade': True,
    'confidence_level': 0.8
}

logger.log_trade_execution(trade_data, success=True)

# Log failed trade
logger.log_trade_execution(
    {'symbol': 'TCS', 'failure_reason': 'insufficient_margin'},
    success=False
)
```

### Position Monitoring

```python
# Log position updates
position_data = {
    'id': 'POS_001',
    'symbol': 'INFY',
    'current_price': 1825.0,
    'unrealized_pnl': 375.0,
    'quantity': 15
}

logger.log_position_update(position_data, update_type="price_update")

# Log position exits
exit_data = {
    'position_id': 'POS_001',
    'symbol': 'INFY',
    'exit_price': 1875.0,
    'exit_reason': 'target_hit',
    'pnl': 1125.0
}

logger.log_exit_execution(exit_data, success=True)
```

### Performance Metrics

```python
# Log trading performance
metrics = {
    'total_trades': 25,
    'win_rate': 72.0,
    'total_pnl': 15750.0,
    'sharpe_ratio': 1.85
}

logger.log_performance_metrics(metrics, metric_type="daily_performance")
```

### Risk Management

```python
# Log risk events
risk_data = {
    'event': 'daily_loss_limit_approached',
    'current_loss': -4500.0,
    'limit': -5000.0,
    'action_taken': 'reduce_positions'
}

logger.log_risk_event(risk_data, risk_level="high")
```

### Error Logging

```python
try:
    # Some operation that might fail
    result = risky_operation()
except Exception as e:
    logger.log_error(
        error=e,
        context={
            'operation': 'risky_operation',
            'parameters': {'param1': 'value1'}
        },
        source="trading_engine"
    )
```

### Strategy Signals

```python
# Log strategy signals
signal_data = {
    'signal_type': 'bullish_momentum',
    'symbol': 'RELIANCE',
    'confidence': 0.85,
    'indicators': {'rsi': 65.2, 'macd': 12.5},
    'entry_price': 2525.0
}

logger.log_strategy_signal(signal_data, "momentum")
```

## Log Categories and Structure

### Log Categories

| Category | Description | Storage Location |
|----------|-------------|------------------|
| `SYSTEM` | System events, startup, shutdown | `system_log.jsonl` |
| `TRADE` | Trade executions, orders | `trade_log.jsonl` |
| `POSITION` | Position updates, monitoring | `position_log.jsonl` |
| `STRATEGY` | Strategy signals, decisions | `main_log.jsonl` |
| `RISK` | Risk management events | `main_log.jsonl` |
| `PERFORMANCE` | Performance metrics | `performance_log.jsonl` |
| `ERROR` | Errors and exceptions | `error_log.jsonl` |
| `COGNITIVE` | AI/ML decisions | `main_log.jsonl` |
| `MARKET_DATA` | Market data events | `main_log.jsonl` |
| `RECOVERY` | System recovery events | `main_log.jsonl` |

### Log Entry Structure

```json
{
  "timestamp": "2024-01-15T09:30:00.123456",
  "level": "INFO",
  "category": "trade",
  "message": "Trade executed successfully: RELIANCE",
  "data": {
    "symbol": "RELIANCE",
    "quantity": 10,
    "entry_price": 2500.0,
    "execution_success": true
  },
  "source": "trade_manager",
  "session_id": "session_1705123456",
  "trade_id": "TRADE_001",
  "position_id": null,
  "strategy": "momentum",
  "symbol": "RELIANCE",
  "bot_type": "stock"
}
```

## File Organization

### Local File Structure

```
logs/
├── 2024-01-15/
│   ├── enhanced_log.jsonl      # All logs combined
│   ├── trade_log.jsonl         # Trade-specific logs
│   ├── position_log.jsonl      # Position monitoring logs
│   ├── error_log.jsonl         # Error logs
│   ├── performance_log.jsonl   # Performance metrics
│   ├── system_log.jsonl        # System events
│   └── python_log.log          # Python logging output
├── 2024-01-16/
│   └── ...
```

### Firestore Collections

```
enhanced_logs_system/          # System logs
enhanced_logs_trade/           # Trade logs
enhanced_logs_position/        # Position logs
enhanced_logs_error/           # Error logs
enhanced_logs_performance/     # Performance logs
enhanced_logs_risk/            # Risk management logs
```

### GCS Bucket Structure

```
tron-trading-logs/
├── 2024-01-15/
│   ├── system/
│   │   └── session_123_094530.json.gz
│   ├── trade/
│   │   └── session_123_094545.json.gz
│   └── summaries/
│       └── session_123_final_summary.json
```

## Performance Monitoring

### Built-in Metrics

The enhanced logger tracks its own performance:

```python
# Get performance metrics
metrics = logger.get_performance_metrics()

print(f"Logs written: {metrics['logs_written']}")
print(f"Firestore writes: {metrics['firestore_writes']}")
print(f"GCS uploads: {metrics['gcs_uploads']}")
print(f"Error rate: {metrics['error_rate']:.4f}")
print(f"Logs per second: {metrics['logs_per_second']:.2f}")
```

### Daily Summary

```python
# Create comprehensive daily summary
summary = logger.create_daily_summary()

# Summary includes:
# - Performance metrics
# - File sizes
# - Error counts
# - Upload statistics
# - Session information
```

## Integration with Existing Systems

### Backward Compatibility

The enhanced logger provides backward compatibility with the existing `Logger` class:

```python
from runner.logger import Logger

# This now uses enhanced logging internally
logger = Logger("2024-01-15")
logger.log_event("This works as before")
```

### Position Monitor Integration

```python
from runner.position_monitor import PositionMonitor

# Position monitor automatically uses enhanced logging
monitor = PositionMonitor(logger=logger)
# All position events are logged with rich metadata
```

### Trade Manager Integration

```python
from runner.enhanced_trade_manager import EnhancedTradeManager

# Trade manager uses enhanced logging for all operations
trade_manager = EnhancedTradeManager(logger=logger)
# All trades logged with comprehensive data
```

## Testing and Validation

### Run Comprehensive Tests

```bash
# Test the enhanced logging system
python test_enhanced_logging.py
```

### Test Output

The test suite validates:
- ✅ Basic logging functionality
- ✅ Trade execution logging
- ✅ Position monitoring logging
- ✅ Performance metrics logging
- ✅ Risk management logging
- ✅ Strategy signal logging
- ✅ Error handling and logging
- ✅ System health monitoring
- ✅ Batch logging performance
- ✅ Firestore integration
- ✅ GCS bucket integration
- ✅ Daily summary creation

## Troubleshooting

### Common Issues

1. **GCS Authentication Error**
   ```bash
   # Ensure proper authentication
   gcloud auth application-default login
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
   ```

2. **Firestore Permission Error**
   ```bash
   # Check Firestore rules and IAM permissions
   gcloud projects get-iam-policy PROJECT_ID
   ```

3. **Bucket Access Error**
   ```bash
   # Verify bucket exists and permissions
   gsutil ls -b gs://tron-trading-logs
   ```

4. **High Memory Usage**
   ```python
   # Reduce buffer size and flush interval
   logger = create_enhanced_logger(
       session_id="session",
       enable_gcs=True,
       enable_firestore=True
   )
   logger.buffer_size = 25  # Reduce from default 50
   logger.flush_interval = 15  # Reduce from default 30
   ```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check logger performance
metrics = logger.get_performance_metrics()
print(f"Queue size: {metrics['queue_size']}")
print(f"Buffer size: {metrics['buffer_size']}")
print(f"Error rate: {metrics['error_rate']}")
```

### Log Analysis

```bash
# Analyze local logs
cat logs/2024-01-15/trade_log.jsonl | jq '.data.symbol' | sort | uniq -c

# Check GCS uploads
gsutil ls -l gs://tron-trading-logs/2024-01-15/

# Query Firestore
# Use Firebase console or gcloud firestore commands
```

## Best Practices

### Performance Optimization

1. **Use Appropriate Log Levels**
   - Use DEBUG sparingly in production
   - Use INFO for important events
   - Use WARNING/ERROR for issues

2. **Batch Operations**
   - Let the system handle batching automatically
   - Don't manually flush unless necessary

3. **Data Size Management**
   - Keep log data concise but informative
   - Use metadata fields for structured data

### Security Considerations

1. **Sensitive Data**
   - Never log passwords, API keys, or personal data
   - Use data masking for sensitive information

2. **Access Control**
   - Implement proper IAM for GCS buckets
   - Use Firestore security rules

3. **Data Retention**
   - Configure lifecycle policies for GCS buckets
   - Implement data retention policies

### Monitoring and Alerting

1. **Set up monitoring for:**
   - Log volume and growth
   - Error rates
   - GCS bucket usage
   - Firestore read/write quotas

2. **Create alerts for:**
   - High error rates
   - Failed uploads
   - Storage quota approaching limits

## Cost Optimization

### GCS Storage Costs

- Logs are automatically compressed (gzip)
- Lifecycle policies delete old data
- Use appropriate storage classes

### Firestore Costs

- Batch writes reduce costs
- Index only necessary fields
- Monitor read/write operations

### Optimization Tips

```python
# Reduce logging frequency for high-volume events
if should_log_detailed():  # Custom logic
    logger.log_position_update(data, "detailed_update")
else:
    logger.log_position_update(summary_data, "summary_update")
```

## Migration Guide

### From Basic Logger

```python
# Old way
logger = Logger("2024-01-15")
logger.log_event("Trade executed")

# New way (backward compatible)
logger = Logger("2024-01-15")  # Now uses enhanced logging
logger.log_event("Trade executed")

# Or use enhanced features directly
enhanced_logger = create_enhanced_logger()
enhanced_logger.log_trade_execution(trade_data, success=True)
```

### Data Migration

1. **Existing Logs**: No migration needed, new system works alongside
2. **Firestore Data**: Existing collections remain unchanged
3. **GCS Buckets**: Create new buckets using provided scripts

## Support and Maintenance

### Regular Maintenance

1. **Monitor storage usage**
2. **Review and update lifecycle policies**
3. **Check error rates and performance metrics**
4. **Update IAM permissions as needed**

### Backup and Recovery

1. **GCS buckets have versioning enabled**
2. **Firestore has automatic backups**
3. **Local logs are preserved for immediate access**

---

**Note**: This enhanced logging system is designed for production use with comprehensive error handling, performance optimization, and data persistence. Always test in a development environment before deploying to production. 