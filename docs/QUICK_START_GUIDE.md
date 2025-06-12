# Quick Start Guide - Enhanced TRON Trading System

## 🚀 Getting Started

### 1. Test the System (Recommended First Step)

Run the comprehensive test suite to see all features in action:

```bash
python test_enhanced_system.py
```

This will demonstrate:
- ✅ Basic trade execution
- ✅ Trailing stop loss
- ✅ Partial exits
- ✅ Time-based exits
- ✅ Manual position management
- ✅ Risk management
- ✅ System crash recovery
- ✅ Emergency exit procedures

### 2. Run in Manual Mode (Interactive)

Start the system in manual mode to control positions interactively:

```bash
python main_enhanced.py manual
```

**Available Commands:**
- `positions` - Show all active positions
- `stats` - Display trading statistics
- `exit <position_id> [percentage]` - Exit position (full or partial)
- `breakeven <position_id>` - Move stop loss to breakeven
- `trailing <position_id> <distance>` - Enable trailing stop
- `emergency` - Emergency exit all positions
- `quit` - Exit manual mode

### 3. View Current Statistics

Check current system status and statistics:

```bash
python main_enhanced.py stats
```

### 4. Run Automated Trading

Start the full automated trading system:

```bash
python main_enhanced.py
```

## 🎯 Key Features Overview

### Real-time Position Monitoring
- Continuous price updates every 5 seconds
- Automatic exit condition checking
- Real-time P&L calculation

### Advanced Exit Strategies

#### Stop Loss Types:
- **Fixed Stop Loss**: Set at trade entry
- **Trailing Stop Loss**: Follows price movement
- **Breakeven Stop**: Move to entry price when profitable

#### Target Management:
- **Fixed Targets**: Predefined profit levels
- **Partial Exits**: Scale out at multiple levels
- **Risk-Reward Based**: Calculated target levels

#### Time-based Exits:
- **Maximum Hold Time**: Auto-exit after duration
- **Market Close**: Exit before market close (3:20 PM)
- **Session-based**: Exit at specific times

### Risk Management
- **Daily Loss Limits**: Maximum daily loss protection
- **Position Sizing**: Kelly Criterion-based sizing
- **Portfolio Risk**: Overall portfolio risk management
- **Emergency Exits**: Immediate exit all positions

### System Recovery
- **Crash Recovery**: Automatic position recovery after restart
- **Position Persistence**: All positions saved continuously
- **Graceful Shutdown**: Proper cleanup on exit

## 📊 Example Usage

### Create a Basic Trade

```python
from runner.enhanced_trade_manager import TradeRequest, create_enhanced_trade_manager

# Create trade request
trade_request = TradeRequest(
    symbol="RELIANCE",
    strategy="vwap",
    direction="bullish",
    quantity=10,
    entry_price=2500.0,
    stop_loss=2450.0,
    target=2600.0,
    paper_trade=True  # Safe testing
)

# Execute trade
position_id = trade_manager.execute_trade(trade_request)
```

### Advanced Trade with Trailing Stop

```python
trade_request = TradeRequest(
    symbol="TCS",
    strategy="momentum",
    direction="bullish",
    quantity=5,
    entry_price=3500.0,
    stop_loss=3450.0,
    target=3650.0,
    trailing_stop_enabled=True,
    trailing_stop_distance=25.0,  # ₹25 trailing distance
    time_based_exit_minutes=240,  # Exit after 4 hours
    partial_exit_levels=[(3575.0, 50.0)],  # Exit 50% at ₹3575
    paper_trade=True
)
```

## 🛡️ Safety Features

### Paper Trading (Default)
- All trades are simulated by default
- Real-time price monitoring
- Full exit strategy testing
- Zero financial risk

### Risk Limits
- Maximum daily loss: ₹5,000 (configurable)
- Maximum trades per day: 10 (configurable)
- Position size limits based on capital
- Stop trading after 3:20 PM

### Emergency Procedures
- **Ctrl+C**: Graceful shutdown with position cleanup
- **Emergency Exit**: Manual command to exit all positions
- **System Crash**: Automatic recovery on restart

## 📈 Monitoring

### Real-time Statistics
```
=== TRADING STATISTICS ===
Trades: 5 total, 4 successful, 1 failed
Paper: 5, Real: 0
Positions: 2 open, 3 closed
P&L: Unrealized ₹150.00, Realized ₹750.00
Exits: 3 total, SL: 1, Target: 2, Trailing: 0
Risk: Can trade: True, Daily loss: ₹0.00
========================
```

### Position Details
```
=== Active Positions (2) ===
ID: RELIANCE_vwap_1705123456
  Symbol: RELIANCE (bullish)
  Qty: 10 | Entry: ₹2500.00
  Current: ₹2525.00 | P&L: ₹250.00
  SL: ₹2450.00 | Target: ₹2600.00
  Strategy: vwap | Duration: 15 min
```

## 🔧 Configuration

### Environment Variables
```bash
export KITE_API_KEY="your_api_key"
export KITE_API_SECRET="your_api_secret"
export FIRESTORE_PROJECT_ID="your_project_id"
export PAPER_TRADE="true"  # For safety
```

### Trading Configuration
Edit `config/config_manager.py`:
```python
config = {
    'paper_trade': True,
    'max_daily_loss': 5000,
    'default_capital': 100000,
    'max_positions': 10,
    'default_strategy': 'vwap'
}
```

## 🚨 Important Notes

### Before Live Trading
1. **Test thoroughly** in paper mode
2. **Verify** all exit strategies work as expected
3. **Check** risk limits are appropriate
4. **Ensure** Kite Connect credentials are correct
5. **Start small** with real money

### Risk Warnings
- **Trading involves risk** - you can lose money
- **Test everything** in paper mode first
- **Never risk more** than you can afford to lose
- **Monitor positions** actively during market hours
- **Have exit plans** for all scenarios

## 📞 Support

### Troubleshooting
1. **Check logs** in `logs/` directory
2. **Verify** Firestore connectivity
3. **Review** position recovery file: `data/position_recovery.json`
4. **Test** with paper trading first

### Common Issues
- **Position not exiting**: Check exit conditions and price data
- **System crash recovery**: Check recovery file and logs
- **Kite Connect issues**: Verify credentials and market hours

### Debug Mode
```bash
export DEBUG=True
python main_enhanced.py
```

---

**Remember**: This system is designed for educational purposes. Always test thoroughly before using real money. Past performance does not guarantee future results. 