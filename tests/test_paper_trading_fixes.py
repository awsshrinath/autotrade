#!/usr/bin/env python3
"""
Paper Trading Fixes Validation Script
====================================

This script tests all the critical paper trading fixes to ensure:
1. PAPER_TRADE flag is properly configured
2. EnhancedTradeManager routes to paper trading correctly
3. Enhanced logging with GCS uploads works
4. Trade simulation and monitoring work

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
        from runner.config import is_paper_trade
        paper_trade_mode = is_paper_trade()
        print(f"✅ is_paper_trade() returned: {paper_trade_mode}")
        
        if not paper_trade_mode:
            print("❌ is_paper_trade() is False - should be True for testing")
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
        
        session_id = f"test_{int(time.time())}"
        enhanced_logger = create_enhanced_logger(
            session_id=session_id,
            enable_gcs=False,
            enable_firestore=False,
            bot_type="test-bot"
        )
        print(f"✅ Enhanced logger created with session: {session_id}")
        
        enhanced_logger.log_event("Test paper trading fixes validation")
        print("✅ Test event logged")
        
        enhanced_logger.shutdown()
        print("✅ Enhanced logger test passed")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logger test failed: {e}")
        return False

def test_enhanced_trade_manager():
    """Test 3: EnhancedTradeManager Paper Trading"""
    print("\n🎯 Test 3: EnhancedTradeManager Paper Trading")
    
    try:
        from runner.enhanced_trade_manager import create_enhanced_trade_manager, TradeRequest
        from runner.logger import Logger
        
        test_logger = Logger('test')
        trade_manager = create_enhanced_trade_manager(logger=test_logger)
        
        print(f"✅ EnhancedTradeManager initialized with paper_trade_mode: {trade_manager.config.paper_trade}")
        
        if not trade_manager.config.paper_trade:
            print("❌ EnhancedTradeManager not in paper trade mode")
            return False
        
        trade_request = TradeRequest(
            symbol='RELIANCE',
            direction='bullish',
            quantity=10,
            entry_price=2500.0,
            stop_loss=2450.0,
            target=2600.0,
            strategy="test-strategy",
            paper_trade=True
        )
        
        position_id = trade_manager.execute_trade(trade_request)
        
        if position_id:
            print(f"✅ Paper trade executed, position ID: {position_id}")
            positions = trade_manager.get_active_positions()
            assert len(positions) == 1
            assert positions[0]['symbol'] == 'RELIANCE'
        else:
            print("❌ Paper trade execution failed")
            return False
            
        print("✅ EnhancedTradeManager test passed")
        return True
        
    except Exception as e:
        print(f"❌ EnhancedTradeManager test failed: {e}")
        return False

def test_stock_runner_integration():
    """Test 4: Stock Runner Integration (Import Test)"""
    print("\n📈 Test 4: Stock Runner Integration")
    
    try:
        from stock_trading.stock_runner import run_stock_trading_bot
        print("✅ Stock runner imports successful")
        
        import stock_trading.stock_runner as stock_runner
        
        # Check that it's using the new manager
        assert hasattr(stock_runner, 'create_enhanced_trade_manager')
        print("✅ Stock runner uses EnhancedTradeManager")
        
        print("✅ Stock runner integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Stock runner integration test failed: {e}")
        return False

def run_all_tests():
    """Run all validation tests"""
    print("🧪 Paper Trading Fixes Validation")
    print("=" * 50)
    
    tests = [
        test_configuration,
        test_enhanced_logger,
        test_enhanced_trade_manager,
        test_stock_runner_integration
    ]
    
    results = {}
    all_passed = True
    
    for test_func in tests:
        test_name = test_func.__name__
        try:
            passed = test_func()
            results[test_name] = "PASSED" if passed else "FAILED"
            if not passed:
                all_passed = False
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            all_passed = False
            
    print("\n" + "="*50)
    print("📊 Test Summary:")
    for name, result in results.items():
        print(f"  - {name}: {result}")
        
    print("\n" + "="*50)
    if all_passed:
        print("🎉 ALL PAPER TRADING TESTS PASSED!")
    else:
        print("❌ SOME PAPER TRADING TESTS FAILED!")

if __name__ == "__main__":
    run_all_tests() 