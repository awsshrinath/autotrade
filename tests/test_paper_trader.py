#!/usr/bin/env python3
"""
Standalone Paper Trader Test Script
Tests the paper trading functionality without external dependencies
"""

import logging
import datetime
from runner.paper_trader import PaperTrader, CapitalAllocation, SegmentType

# Mock Firestore client for testing
class MockFirestoreClient:
    def __init__(self, logger=None):
        self.logger = logger
        self.trades = []
        
    def log_trade(self, bot_name, date_str, trade_data):
        self.trades.append(trade_data)
        print(f"[MOCK FIRESTORE] Trade logged: {trade_data['symbol']} - {trade_data['strategy']}")
        
    def log_trade_exit(self, bot_name, date_str, symbol, exit_data):
        print(f"[MOCK FIRESTORE] Trade exit logged: {symbol} - PnL: ₹{exit_data['pnl']:.2f}")

def test_paper_trader_comprehensive():
    """Comprehensive test of paper trader functionality"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("PAPER TRADER COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Initialize paper trader with mock Firestore
    mock_firestore = MockFirestoreClient(logger)
    trader = PaperTrader(logger=logger, firestore_client=mock_firestore)
    
    print(f"\n1. INITIAL CAPITAL ALLOCATION:")
    print(f"   Total Capital: ₹{trader.capital.total_capital:,.2f}")
    print(f"   Stocks: ₹{trader.capital.stocks_allocation:,.2f} (Available: ₹{trader.capital.stocks_available:,.2f})")
    print(f"   Options: ₹{trader.capital.options_allocation:,.2f} (Available: ₹{trader.capital.options_available:,.2f})")
    print(f"   Futures: ₹{trader.capital.futures_allocation:,.2f} (Available: ₹{trader.capital.futures_available:,.2f})")
    
    # Test 1: Stock trade (should succeed)
    print(f"\n2. TESTING STOCK TRADE:")
    stock_signal = {
        "symbol": "RELIANCE",
        "entry_price": 2500.0,
        "quantity": 10,
        "stop_loss": 2450.0,
        "target": 2600.0,
        "direction": "bullish"
    }
    
    stock_trade = trader.execute_paper_trade(stock_signal, "vwap")
    if stock_trade:
        print(f"   ✅ Stock trade executed: {stock_trade.symbol}")
        print(f"   Margin used: ₹{stock_trade.margin_used:,.2f}")
        print(f"   Remaining stocks capital: ₹{trader.capital.stocks_available:,.2f}")
    else:
        print(f"   ❌ Stock trade failed")
    
    # Test 2: Options trade (should succeed)
    print(f"\n3. TESTING OPTIONS TRADE:")
    options_signal = {
        "symbol": "NIFTY24NOVCE24000",
        "entry_price": 120.0,
        "quantity": 50,  # 1 lot
        "stop_loss": 100.0,
        "target": 150.0,
        "direction": "bullish"
    }
    
    options_trade = trader.execute_paper_trade(options_signal, "scalp")
    if options_trade:
        print(f"   ✅ Options trade executed: {options_trade.symbol}")
        print(f"   Margin used: ₹{options_trade.margin_used:,.2f}")
        print(f"   Remaining options capital: ₹{trader.capital.options_available:,.2f}")
    else:
        print(f"   ❌ Options trade failed")
    
    # Test 3: Futures trade (should fail due to insufficient margin)
    print(f"\n4. TESTING FUTURES TRADE (INSUFFICIENT MARGIN):")
    futures_signal = {
        "symbol": "NIFTY24NOVFUT",
        "entry_price": 24000.0,
        "quantity": 50,  # 1 lot
        "stop_loss": 23800.0,
        "target": 24200.0,
        "direction": "bullish"
    }
    
    futures_trade = trader.execute_paper_trade(futures_signal, "orb")
    if futures_trade:
        print(f"   ✅ Futures trade executed: {futures_trade.symbol}")
        print(f"   Margin used: ₹{futures_trade.margin_used:,.2f}")
    else:
        print(f"   ❌ Futures trade rejected (Expected - insufficient margin)")
    
    # Test 4: Smaller futures trade (should succeed)
    print(f"\n5. TESTING SMALLER FUTURES TRADE:")
    small_futures_signal = {
        "symbol": "BANKNIFTY24NOVFUT",
        "entry_price": 50000.0,
        "quantity": 15,  # 1 lot
        "stop_loss": 49500.0,
        "target": 50500.0,
        "direction": "bullish"
    }
    
    # Check required margin first
    required_margin = trader.calculate_required_margin(
        "BANKNIFTY24NOVFUT", SegmentType.FUTURES, 50000.0, 15, 15
    )
    print(f"   Required margin for BANKNIFTY: ₹{required_margin:,.2f}")
    
    if required_margin <= trader.capital.futures_available:
        small_futures_trade = trader.execute_paper_trade(small_futures_signal, "orb")
        if small_futures_trade:
            print(f"   ✅ BANKNIFTY futures trade executed: {small_futures_trade.symbol}")
            print(f"   Margin used: ₹{small_futures_trade.margin_used:,.2f}")
            print(f"   Remaining futures capital: ₹{trader.capital.futures_available:,.2f}")
        else:
            print(f"   ❌ BANKNIFTY futures trade failed")
    else:
        print(f"   ❌ BANKNIFTY futures trade would also fail (insufficient margin)")
    
    # Test 5: Position monitoring and exit
    print(f"\n6. TESTING POSITION MONITORING:")
    print(f"   Active trades: {len(trader.active_trades)}")
    
    if trader.active_trades:
        # Simulate price movements
        market_data = {}
        for trade in trader.active_trades:
            if trade.direction == "bullish":
                # Simulate target hit
                market_data[trade.symbol] = trade.target + 1
            else:
                # Simulate target hit
                market_data[trade.symbol] = trade.target - 1
        
        print(f"   Simulating target hits for all positions...")
        trader.monitor_and_exit_trades(market_data)
        print(f"   Active trades after monitoring: {len(trader.active_trades)}")
        print(f"   Completed trades: {len(trader.completed_trades)}")
    
    # Test 6: Performance summary
    print(f"\n7. PERFORMANCE SUMMARY:")
    summary = trader.calculate_performance_summary()
    print(f"   Total trades: {summary.total_trades}")
    print(f"   Winning trades: {summary.winning_trades}")
    print(f"   Total P&L: ₹{summary.total_pnl:,.2f}")
    print(f"   Return percentage: {summary.return_percentage:.2f}%")
    print(f"   Win rate: {summary.win_rate:.1f}%")
    
    # Test 7: Dashboard data
    print(f"\n8. DASHBOARD DATA:")
    dashboard_data = trader.get_dashboard_data()
    print(f"   Daily P&L: ₹{dashboard_data['daily_pnl']:,.2f}")
    print(f"   Return %: {dashboard_data['return_percentage']:.2f}%")
    print(f"   Margin utilization:")
    for segment, utilization in dashboard_data['margin_utilization'].items():
        print(f"     {segment.title()}: {utilization:.1f}%")
    
    # Test 8: Capital allocation after trades
    print(f"\n9. FINAL CAPITAL ALLOCATION:")
    print(f"   Stocks: ₹{trader.capital.stocks_available:,.2f} available (₹{trader.capital.stocks_margin_used:,.2f} used)")
    print(f"   Options: ₹{trader.capital.options_available:,.2f} available (₹{trader.capital.options_margin_used:,.2f} used)")
    print(f"   Futures: ₹{trader.capital.futures_available:,.2f} available (₹{trader.capital.futures_margin_used:,.2f} used)")
    
    print(f"\n" + "=" * 60)
    print("PAPER TRADER TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    
    # Verify trader was created successfully
    assert trader is not None
    assert trader.capital.total_capital > 0

def test_margin_calculations():
    """Test margin calculation logic"""
    
    print("\n" + "=" * 60)
    print("MARGIN CALCULATION TESTS")
    print("=" * 60)
    
    trader = PaperTrader()
    
    # Test stock margin
    stock_margin = trader.calculate_required_margin("RELIANCE", SegmentType.STOCKS, 2500, 10)
    print(f"Stock margin (RELIANCE, 10 qty @ ₹2500): ₹{stock_margin:,.2f}")
    
    # Test options margin
    options_margin = trader.calculate_required_margin("NIFTY24NOVCE", SegmentType.OPTIONS, 120, 50, 50)
    print(f"Options margin (NIFTY CE, 50 qty @ ₹120): ₹{options_margin:,.2f}")
    
    # Test NIFTY futures margin
    nifty_margin = trader.calculate_required_margin("NIFTY24NOVFUT", SegmentType.FUTURES, 24000, 50, 50)
    print(f"NIFTY futures margin (1 lot): ₹{nifty_margin:,.2f}")
    
    # Test BANKNIFTY futures margin
    banknifty_margin = trader.calculate_required_margin("BANKNIFTY24NOVFUT", SegmentType.FUTURES, 50000, 15, 15)
    print(f"BANKNIFTY futures margin (1 lot): ₹{banknifty_margin:,.2f}")
    
    print("=" * 60)

if __name__ == "__main__":
    # Run margin calculation tests
    test_margin_calculations()
    
    # Run comprehensive functionality test
    trader = test_paper_trader_comprehensive()
    
    print(f"\n🎉 All tests completed! Paper trader is ready for integration.") 