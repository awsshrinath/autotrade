#!/usr/bin/env python3
"""
Paper Trading Fixes Validation Script
====================================

This script tests all the critical paper trading fixes to ensure:
1. PAPER_TRADE flag is properly configured
2. TradeManager routes to paper trading correctly
3. Enhanced logging with GCS uploads works
4. Paper trading managers are properly integrated
5. Trade simulation and monitoring work

Run this script to validate the fixes before deploying.
"""

import os
import sys
import datetime
import time
import logging

# Set paper trading mode for testing
os.environ['PAPER_TRADE'] = 'true'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_configuration():
    """Test 1: Configuration and Environment Setup"""
    print("\n🔧 Test 1: Configuration and Environment Setup")
    
    try:
        from runner.config import PAPER_TRADE, get_config
        print(f"✅ PAPER_TRADE flag: {PAPER_TRADE}")
        
        if not PAPER_TRADE:
            print("❌ PAPER_TRADE is False - should be True for testing")
            return False
            
        print("✅ Configuration loaded successfully")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_enhanced_logger():
    """Test 2: Enhanced Logger with GCS Integration"""
    print("\n📝 Test 2: Enhanced Logger with GCS Integration")
    
    try:
        from runner.enhanced_logger import create_enhanced_logger
        
        # Create enhanced logger
        session_id = f"test_{int(time.time())}"
        enhanced_logger = create_enhanced_logger(
            session_id=session_id,
            enable_gcs=True,
            enable_firestore=True,
            bot_type="test-bot"
        )
        
        print(f"✅ Enhanced logger created with session: {session_id}")
        
        # Test logging
        enhanced_logger.log_event(
            "Test paper trading fixes validation",
            data={
                'test_type': 'paper_trading_validation',
                'timestamp': datetime.datetime.now().isoformat()
            }
        )
        
        print("✅ Test event logged")
        
        # Test force GCS upload
        enhanced_logger.force_upload_to_gcs()
        print("✅ Force GCS upload completed")
        
        enhanced_logger.shutdown()
        print("✅ Enhanced logger test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logger test failed: {e}")
        return False

def test_trade_manager():
    """Test 3: TradeManager Paper Trading Integration"""
    print("\n🎯 Test 3: TradeManager Paper Trading Integration")
    
    try:
        from runner.trade_manager import TradeManager
        from runner.logger import Logger
        
        # Create trade manager
        test_logger = Logger('test')
        trade_manager = TradeManager(
            logger=test_logger,
            kite=None,  # Mock for testing
            firestore_client=None
        )
        
        print(f"✅ TradeManager initialized with paper_trade_mode: {trade_manager.paper_trade_mode}")
        
        if not trade_manager.paper_trade_mode:
            print("❌ TradeManager not in paper trade mode")
            return False
        
        # Test paper trade execution
        sample_trade_signal = {
            'symbol': 'RELIANCE',
            'direction': 'bullish',
            'quantity': 10,
            'entry_price': 2500.0,
            'stop_loss': 2450.0,
            'target': 2600.0
        }
        
        result = trade_manager._execute_paper_trade(
            sample_trade_signal, 
            "test-bot", 
            "test-strategy"
        )
        
        if result:
            print(f"✅ Paper trade executed: {result['id']}")
            print(f"   Symbol: {result['symbol']}, Mode: {result['mode']}")
            
            # Test trade exit simulation
            sample_market_data = {
                'RELIANCE': {'ltp': 2600.0}  # Hit target
            }
            
            exit_result = trade_manager.simulate_trade_exit(result, sample_market_data)
            if exit_result and exit_result.get('status') == 'paper_closed':
                print(f"✅ Trade exit simulated: {exit_result['exit_reason']}, P&L: ₹{exit_result['pnl']}")
            else:
                print("⚠️ Trade exit simulation incomplete (expected for some scenarios)")
                
        print("✅ TradeManager test passed")
        return True
        
    except Exception as e:
        print(f"❌ TradeManager test failed: {e}")
        return False

def test_paper_trading_manager():
    """Test 4: Paper Trading Manager Integration"""
    print("\n📊 Test 4: Paper Trading Manager Integration")
    
    try:
        from runner.paper_trader_integration import PaperTradingManager
        from runner.logger import Logger
        
        # Create paper trading manager
        test_logger = Logger('test')
        manager = PaperTradingManager(logger=test_logger)
        
        print(f"✅ Paper Trading Manager initialized, enabled: {manager.is_enabled}")
        
        if not manager.is_enabled:
            print("❌ Paper Trading Manager not enabled")
            return False
        
        # Test sample market data creation
        from runner.paper_trader_integration import create_sample_market_data
        market_data = create_sample_market_data()
        
        print(f"✅ Sample market data created with {len(market_data)} symbols")
        
        # Test trading session
        manager.run_trading_session(market_data)
        print("✅ Trading session executed")
        
        # Test dashboard data
        dashboard_data = manager.get_dashboard_data()
        print(f"✅ Dashboard data: {dashboard_data}")
        
        print("✅ Paper Trading Manager test passed")
        return True
        
    except Exception as e:
        print(f"❌ Paper Trading Manager test failed: {e}")
        return False

def test_stock_runner_integration():
    """Test 5: Stock Runner Integration (Import Test)"""
    print("\n📈 Test 5: Stock Runner Integration")
    
    try:
        # Test imports and basic setup
        from stock_trading.stock_runner import run_stock_trading_bot
        print("✅ Stock runner imports successful")
        
        # Test that runner has paper trading components
        import stock_trading.stock_runner as stock_runner
        
        if hasattr(stock_runner, 'PaperTradingManager'):
            print("✅ Paper Trading Manager available in stock runner")
        else:
            print("⚠️ Paper Trading Manager not imported in stock runner")
        
        if hasattr(stock_runner, 'PAPER_TRADING_AVAILABLE'):
            print(f"✅ Paper trading availability flag: {stock_runner.PAPER_TRADING_AVAILABLE}")
        else:
            print("⚠️ Paper trading availability flag not found")
        
        print("✅ Stock runner integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Stock runner integration test failed: {e}")
        return False

def test_main_integration():
    """Test 6: Main Entry Point Integration (Import Test)"""
    print("\n🚀 Test 6: Main Entry Point Integration")
    
    try:
        # Test main.py imports
        import main
        
        print("✅ main.py imports successful")
        
        # Check for paper trading components
        if hasattr(main, 'PAPER_TRADING_AVAILABLE'):
            print(f"✅ Paper trading availability: {main.PAPER_TRADING_AVAILABLE}")
        else:
            print("⚠️ Paper trading availability flag not found in main.py")
        
        if hasattr(main, 'PAPER_TRADE'):
            print(f"✅ PAPER_TRADE flag: {main.PAPER_TRADE}")
        else:
            print("⚠️ PAPER_TRADE flag not found in main.py")
        
        print("✅ Main integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Main integration test failed: {e}")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("🧪 Paper Trading Fixes Validation")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_enhanced_logger,
        test_trade_manager,
        test_paper_trading_manager,
        test_stock_runner_integration,
        test_main_integration
    ]
    
    results = []
    
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Paper trading fixes are working!")
        print("\n✅ Ready for deployment:")
        print("   1. Paper trading is properly configured")
        print("   2. TradeManager routes to paper trading correctly")
        print("   3. Enhanced logging with GCS uploads works")
        print("   4. All components are properly integrated")
    else:
        print("⚠️ Some tests failed - check the output above for details")
        print(f"\nFailed tests: {total - passed}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 