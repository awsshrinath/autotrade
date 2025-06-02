# Paper Trading Module Documentation

## Overview

The Paper Trading Module is a comprehensive simulation system that allows testing trading strategies with realistic margin calculations, capital allocation, and performance tracking without risking real money.

## Key Features

### 1. Capital Allocation & Margin Management
- **Total Capital**: ₹1,00,000 distributed across segments
- **Stocks**: 40% (₹40,000) - Full amount required (no leverage)
- **Options**: 30% (₹30,000) - Premium × lot size × quantity
- **Futures**: 30% (₹30,000) - Realistic margin requirements
  - NIFTY Futures: ₹60,000 per lot
  - BANKNIFTY Futures: ₹40,000 per lot
  - Stock Futures: 15% of notional value

### 2. Realistic Margin Calculations
```python
# Example margin calculations
Stock margin = price × quantity                    # ₹2,500 × 10 = ₹25,000
Options margin = premium × lot_size × quantity     # ₹120 × 50 × 1 = ₹6,000
NIFTY futures = ₹60,000 per lot                   # Fixed margin
BANKNIFTY futures = ₹40,000 per lot               # Fixed margin
```

### 3. Trade Execution & Monitoring
- **Entry**: Validates margin availability before execution
- **Monitoring**: Continuous SL/Target tracking
- **Exit**: Automatic closure on SL/Target hit or EOD square-off
- **Rejection**: Logs insufficient margin trades to Firestore

### 4. Performance Tracking
- **Daily/Weekly/Monthly** P&L calculation
- **Segment-wise** performance (Stocks, Options, Futures)
- **Win rate** and average win/loss metrics
- **Return percentage** based on total capital

## File Structure

```
runner/
├── paper_trader.py              # Main paper trading module
├── paper_trader_integration.py  # Integration with main system
└── firestore_client.py         # Database logging (existing)

test_paper_trader.py            # Standalone test script
docs/
└── paper_trader_documentation.md # This documentation
```

## Core Classes

### 1. PaperTrader
Main class that handles all paper trading operations.

```python
from runner.paper_trader import PaperTrader, create_paper_trader

# Initialize paper trader
trader = PaperTrader(logger=logger, firestore_client=firestore_client)

# Or use factory function (respects config)
trader = create_paper_trader(logger=logger, firestore_client=firestore_client)
```

### 2. PaperTrade
Dataclass representing individual trades.

```python
@dataclass
class PaperTrade:
    trade_id: str
    symbol: str
    segment: SegmentType
    strategy: str
    direction: str  # bullish/bearish
    entry_price: float
    quantity: int
    stop_loss: float
    target: float
    margin_used: float
    entry_time: datetime.datetime
    # ... additional fields
```

### 3. CapitalAllocation
Tracks capital distribution and usage.

```python
@dataclass
class CapitalAllocation:
    total_capital: float = 100000.0
    stocks_allocation: float = 40000.0
    options_allocation: float = 30000.0
    futures_allocation: float = 30000.0
    # Available and used amounts tracked separately
```

## Usage Examples

### Basic Trade Execution

```python
# Create trade signal
trade_signal = {
    "symbol": "RELIANCE",
    "entry_price": 2500.0,
    "quantity": 10,
    "stop_loss": 2450.0,
    "target": 2600.0,
    "direction": "bullish"
}

# Execute paper trade
trade = trader.execute_paper_trade(trade_signal, "vwap")
if trade:
    print(f"Trade executed: {trade.symbol}")
else:
    print("Trade rejected (insufficient margin)")
```

### Position Monitoring

```python
# Monitor positions with current market data
market_data = {
    "RELIANCE": 2550.0,  # Current price
    "NIFTY24NOVFUT": 24100.0
}

trader.monitor_and_exit_trades(market_data)
```

### Performance Analysis

```python
# Get performance summary
summary = trader.calculate_performance_summary("daily")
print(f"Daily P&L: ₹{summary.total_pnl:.2f}")
print(f"Return: {summary.return_percentage:.2f}%")
print(f"Win Rate: {summary.win_rate:.1f}%")

# Get dashboard data
dashboard_data = trader.get_dashboard_data()
print(f"Active trades: {dashboard_data['active_trades']}")
print(f"Margin utilization: {dashboard_data['margin_utilization']}")
```

## Integration with Main System

### Using PaperTradingManager

```python
from runner.paper_trader_integration import PaperTradingManager

# Initialize manager
trading_manager = PaperTradingManager(logger=logger)

# Execute trade (paper or real based on config)
trade = trading_manager.execute_trade(trade_signal, "vwap")

# Run complete trading session
trading_manager.run_trading_session(market_data)

# Get dashboard data
dashboard_data = trading_manager.get_dashboard_data()
```

## Firestore Integration

### Collections Created
- `paper_trades/{date}` - Individual trade records
- `performance_summary_daily` - Daily performance summaries
- `performance_summary_weekly` - Weekly performance summaries
- `performance_summary_monthly` - Monthly performance summaries

### Trade Document Structure
```json
{
  "trade_id": "RELIANCE_vwap_1638360000",
  "symbol": "RELIANCE",
  "segment": "stocks",
  "strategy": "vwap",
  "direction": "bullish",
  "entry_price": 2500.0,
  "quantity": 10,
  "stop_loss": 2450.0,
  "target": 2600.0,
  "margin_used": 25000.0,
  "entry_time": "2024-12-01T09:30:00",
  "exit_price": 2550.0,
  "exit_time": "2024-12-01T10:15:00",
  "pnl": 500.0,
  "status": "closed_target",
  "exit_reason": "Target reached"
}
```

## Configuration

### Paper Trading Toggle
The system respects the `PAPER_TRADE` configuration:

```python
# In config.py or environment
PAPER_TRADE = True  # Enable paper trading

# Factory function automatically checks config
trader = create_paper_trader()  # Returns PaperTrader if enabled, None if disabled
```

### Capital Scaling (Optional)
Dynamic capital scaling based on performance:

```python
# Automatically scales capital up by 10% if monthly return > 10%
trader.monthly_performance_update()
```

## Testing

### Run Comprehensive Tests
```bash
python test_paper_trader.py
```

### Test Results Summary
- ✅ **Capital Allocation**: Proper distribution across segments
- ✅ **Margin Calculations**: Realistic margin requirements
- ✅ **Trade Execution**: Successful execution with margin validation
- ✅ **Trade Rejection**: Proper rejection for insufficient margin
- ✅ **Position Monitoring**: Automatic SL/Target tracking
- ✅ **Performance Tracking**: Accurate P&L and metrics calculation
- ✅ **Dashboard Integration**: Complete data for UI display

## Key Benefits

1. **Risk-Free Testing**: Test strategies without real money
2. **Realistic Simulation**: Accurate margin and lot size calculations
3. **Comprehensive Tracking**: Detailed performance analytics
4. **Easy Integration**: Seamless switch between paper and real trading
5. **Dashboard Ready**: Complete data structure for UI integration
6. **Firestore Logging**: Persistent storage for analysis and reporting

## Future Enhancements

1. **Advanced Order Types**: Stop-loss orders, trailing stops
2. **Slippage Simulation**: More realistic fill prices
3. **Commission Calculation**: Include brokerage and taxes
4. **Portfolio Optimization**: Dynamic allocation based on strategy performance
5. **Risk Metrics**: Sharpe ratio, maximum drawdown, etc.

## Error Handling

The system includes comprehensive error handling:
- **Insufficient Margin**: Trades rejected and logged
- **Invalid Symbols**: Graceful handling of unknown instruments
- **Database Errors**: Fallback to local logging
- **Configuration Issues**: Default to paper trading mode

## Conclusion

The Paper Trading Module provides a production-ready simulation environment that accurately mimics real trading conditions while providing comprehensive analytics and seamless integration with the main trading system. It serves as an essential tool for strategy development, testing, and risk management. 