# Enhanced TRON Trading System

## Overview

The Enhanced TRON Trading System is a comprehensive algorithmic trading platform with advanced position monitoring, exit strategies, and risk management. It provides real-time position tracking, multiple exit strategies, system crash recovery, and comprehensive logging to Firestore.

## Key Features

### 🎯 Advanced Position Management
- **Real-time Position Monitoring**: Continuous tracking of all open positions
- **Multiple Exit Strategies**: Stop loss, target, trailing stop, time-based, and risk-based exits
- **Partial Position Management**: Support for partial exits and position scaling
- **Breakeven Management**: Automatic and manual breakeven adjustments

### 🛡️ Risk Management
- **Risk Governor**: Daily loss limits and trade count restrictions
- **Portfolio Manager**: Position sizing based on Kelly Criterion and risk metrics
- **Emergency Exit System**: Immediate exit of all positions during emergencies
- **System Crash Recovery**: Automatic position recovery after system restarts

### 📊 Exit Strategies

#### 1. Stop Loss
- **Fixed Stop Loss**: Predefined stop loss levels
- **Dynamic Stop Loss**: Adjustable based on market conditions
- **Breakeven Stops**: Move stop loss to entry price when profitable

#### 2. Trailing Stop Loss
- **Distance-based Trailing**: Trail by fixed amount
- **Percentage-based Trailing**: Trail by percentage of price
- **Trigger-based Trailing**: Activate trailing after reaching trigger price

#### 3. Target-based Exits
- **Fixed Targets**: Predefined profit targets
- **Multiple Target Levels**: Partial exits at different price levels
- **Risk-Reward Based**: Targets based on risk-reward ratios

#### 4. Time-based Exits
- **Maximum Hold Time**: Exit after maximum duration
- **Market Close Exits**: Automatic exit before market close
- **Session-based Exits**: Exit at specific times

#### 5. Risk Management Exits
- **Maximum Loss Percentage**: Exit when loss exceeds threshold
- **Portfolio Risk Limits**: Exit when portfolio risk is too high
- **Volatility-based Exits**: Exit during high volatility periods

### 🔄 System Recovery
- **Crash Recovery**: Automatic position recovery from saved state
- **Position Persistence**: All positions saved to recovery file
- **Graceful Shutdown**: Proper cleanup and position management on exit

## Architecture

### Core Components

```
Enhanced Trading System
├── EnhancedTradeManager
│   ├── Trade Execution
│   ├── Risk Management
│   └── Strategy Integration
├── PositionMonitor
│   ├── Real-time Monitoring
│   ├── Exit Strategy Engine
│   └── Recovery System
├── Portfolio Manager
│   ├── Position Sizing
│   ├── Capital Management
│   └── Risk Assessment
└── Cognitive System
    ├── Decision Analysis
    ├── Performance Tracking
    └── Learning System
```

### Data Flow

```
Strategy Signal → Risk Checks → Trade Execution → Position Monitor → Exit Management → Firestore Logging
```

## Installation and Setup

### Prerequisites
- Python 3.8+
- Kite Connect API credentials (for live trading)
- Google Cloud Firestore setup
- Required Python packages (see requirements.txt)

### Configuration
1. Set up environment variables:
   ```bash
   export KITE_API_KEY="your_api_key"
   export KITE_API_SECRET="your_api_secret"
   export FIRESTORE_PROJECT_ID="your_project_id"
   ```

2. Configure trading parameters in `config/config_manager.py`

## Usage

### Basic Usage

#### Start Trading System
```bash
python main_enhanced.py
```

#### Manual Mode (Interactive)
```bash
python main_enhanced.py manual
```

#### Show Statistics Only
```bash
python main_enhanced.py stats
```

### Manual Commands

In manual mode, you can use these commands:

- `positions` - Show all active positions
- `stats` - Display trading statistics
- `exit <position_id> [percentage]` - Exit position (full or partial)
- `breakeven <position_id>` - Move stop loss to breakeven
- `trailing <position_id> <distance>` - Enable trailing stop
- `emergency` - Emergency exit all positions
- `quit` - Exit manual mode

### Example Trade Execution

```python
from runner.enhanced_trade_manager import TradeRequest, create_enhanced_trade_manager

# Create trade manager
trade_manager = create_enhanced_trade_manager(logger, kite_manager, firestore)

# Create trade request
trade_request = TradeRequest(
    symbol="RELIANCE",
    strategy="vwap",
    direction="bullish",
    quantity=10,
    entry_price=2500.0,
    stop_loss=2450.0,
    target=2600.0,
    trailing_stop_enabled=True,
    trailing_stop_distance=25.0,
    time_based_exit_minutes=240,  # 4 hours
    max_loss_pct=2.0
)

# Execute trade
position_id = trade_manager.execute_trade(trade_request)
```

## Exit Strategy Configuration

### Basic Exit Strategy
```python
exit_strategy = ExitStrategy(
    stop_loss=2450.0,
    target=2600.0,
    max_loss_pct=2.0,
    max_hold_time_minutes=240
)
```

### Advanced Exit Strategy with Trailing Stop
```python
exit_strategy = ExitStrategy(
    stop_loss=2450.0,
    target=2600.0,
    trailing_stop_enabled=True,
    trailing_stop_distance=25.0,
    trailing_stop_trigger=2550.0,  # Start trailing when price reaches this
    partial_exit_levels=[(2575.0, 50.0)],  # Exit 50% at 2575
    time_based_exit_minutes=240,
    max_loss_pct=2.0
)
```

## Monitoring and Logging

### Real-time Monitoring
- Position prices updated every 5 seconds
- Exit conditions checked continuously
- All events logged to Firestore

### Log Structure
```json
{
  "id": "position_id",
  "symbol": "RELIANCE",
  "strategy": "vwap",
  "direction": "bullish",
  "entry_price": 2500.0,
  "exit_price": 2575.0,
  "quantity": 10,
  "entry_time": "2024-01-15T09:30:00",
  "exit_time": "2024-01-15T11:45:00",
  "exit_reason": "target_hit",
  "pnl": 750.0,
  "status": "closed",
  "partial_exits": [],
  "paper_trade": true
}
```

### Statistics Tracking
- Total trades executed
- Success/failure rates
- Exit reason breakdown
- P&L tracking
- Risk metrics

## Risk Management

### Risk Governor
- **Daily Loss Limit**: Maximum daily loss allowed
- **Trade Count Limit**: Maximum number of trades per day
- **Time-based Restrictions**: No trading after cutoff time

### Portfolio Manager
- **Position Sizing**: Kelly Criterion-based sizing
- **Capital Allocation**: Dynamic capital allocation
- **Risk Assessment**: Pre-trade risk evaluation

### Emergency Procedures
- **System Crash**: Automatic position recovery
- **Market Volatility**: Risk-based position exits
- **Manual Override**: Emergency exit all positions

## Paper Trading vs Live Trading

### Paper Trading (Default)
- Simulated trade execution
- Real-time price monitoring
- Full exit strategy testing
- No actual money at risk

### Live Trading
- Real order placement via Kite Connect
- Actual position management
- Real money at risk
- Production-ready execution

## Performance Optimization

### Monitoring Efficiency
- Batch price updates for multiple positions
- Asynchronous exit execution
- Optimized database queries

### Memory Management
- Position cleanup after closure
- Limited trade history retention
- Efficient data structures

## Error Handling

### Trade Execution Errors
- Automatic retry mechanisms
- Fallback to paper trading
- Comprehensive error logging

### System Errors
- Graceful degradation
- Position preservation
- Recovery procedures

## API Integration

### Kite Connect Integration
- Real-time price feeds
- Order placement and management
- Portfolio and margin data

### Firestore Integration
- Trade logging
- Position persistence
- Historical data storage

## Cognitive System Integration

### Decision Analysis
- Trade outcome analysis
- Strategy performance tracking
- Learning from results

### Performance Metrics
- Win/loss ratios
- Average holding times
- Risk-adjusted returns

## Configuration Options

### Trading Configuration
```python
config = {
    'paper_trade': True,
    'max_daily_loss': 5000,
    'default_capital': 100000,
    'update_interval': 5,  # seconds
    'max_positions': 10,
    'default_strategy': 'vwap'
}
```

### Exit Strategy Defaults
```python
default_exit_strategy = {
    'max_loss_pct': 2.0,
    'max_hold_time_minutes': 240,
    'trailing_stop_distance': 1.0,  # percentage
    'breakeven_trigger_pct': 1.0
}
```

## Troubleshooting

### Common Issues

1. **Position Not Exiting**
   - Check exit conditions
   - Verify price data availability
   - Review exit strategy configuration

2. **System Crash Recovery**
   - Check recovery file: `data/position_recovery.json`
   - Verify Firestore connectivity
   - Review system logs

3. **Kite Connect Issues**
   - Verify API credentials
   - Check market hours
   - Review rate limits

### Debug Mode
```bash
export DEBUG=True
python main_enhanced.py
```

## Future Enhancements

### Planned Features
- Machine learning-based exit optimization
- Multi-timeframe analysis
- Advanced risk metrics
- Real-time alerts and notifications
- Web-based dashboard integration

### Scalability Improvements
- Distributed position monitoring
- Cloud-based execution
- High-frequency trading support

## Support and Documentation

### Additional Resources
- API Documentation: `/docs/api.md`
- Strategy Development Guide: `/docs/strategies.md`
- Risk Management Guide: `/docs/risk_management.md`

### Contact
For support and questions, please refer to the project documentation or create an issue in the repository.

---

**Note**: This system is designed for educational and research purposes. Always test thoroughly in paper trading mode before using with real money. Trading involves risk, and past performance does not guarantee future results. 