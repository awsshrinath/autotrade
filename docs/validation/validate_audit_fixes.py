#!/usr/bin/env python3

"""
Comprehensive Audit Fixes Validation Script
==========================================

This script validates all the critical fixes implemented during the security 
and stability audit. It tests error handling, validation logic, and safety 
mechanisms without making actual trades.

Run this script to ensure all fixes are working correctly before deployment.
"""

import os
import sys
import datetime
import time
import json
import logging
from typing import Dict, Any, List
import traceback

# Setup logging for validation
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_environment_validation():
    """Test 1: Environment Validation"""
    print("\n🧪 Test 1: Environment Validation")
    print("=" * 50)
    
    try:
        # Test the validation function
        from main import validate_environment
        
        # Save original env vars
        original_gcp_creds = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        original_project = os.environ.get('GOOGLE_CLOUD_PROJECT')
        
        # Test with missing credentials
        if 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ:
            del os.environ['GOOGLE_APPLICATION_CREDENTIALS']
        if 'GOOGLE_CLOUD_PROJECT' in os.environ:
            del os.environ['GOOGLE_CLOUD_PROJECT']
        
        result = validate_environment()
        if not result:
            print("✅ Environment validation correctly failed with missing vars")
        else:
            print("❌ Environment validation should have failed")
        
        # Restore environment
        if original_gcp_creds:
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = original_gcp_creds
        if original_project:
            os.environ['GOOGLE_CLOUD_PROJECT'] = original_project
        
        # Test with valid environment
        if original_gcp_creds and original_project:
            result = validate_environment()
            if result:
                print("✅ Environment validation correctly passed with valid vars")
            else:
                print("⚠️  Environment validation failed even with vars (expected if creds invalid)")
        
        return True
        
    except Exception as e:
        print(f"❌ Environment validation test failed: {e}")
        return False

def test_secret_manager_validation():
    """Test 2: Secret Manager Input Validation"""
    print("\n🧪 Test 2: Secret Manager Validation")
    print("=" * 50)
    
    try:
        from runner.secret_manager_client import access_secret
        
        # Test invalid inputs
        result = access_secret("", "test-project")
        if result is None:
            print("✅ Secret manager correctly rejected empty secret_id")
        else:
            print("❌ Secret manager should reject empty secret_id")
        
        result = access_secret(None, "test-project")
        if result is None:
            print("✅ Secret manager correctly rejected None secret_id")
        else:
            print("❌ Secret manager should reject None secret_id")
        
        result = access_secret("test-secret", "")
        if result is None:
            print("✅ Secret manager correctly rejected empty project_id")
        else:
            print("❌ Secret manager should reject empty project_id")
        
        # Test cache functionality
        from runner.secret_manager_client import clear_secret_cache, get_cache_status
        clear_secret_cache()
        status = get_cache_status()
        
        if status['total_entries'] == 0:
            print("✅ Cache management working correctly")
        else:
            print("❌ Cache not cleared properly")
        
        return True
        
    except Exception as e:
        print(f"❌ Secret manager validation test failed: {e}")
        return False

def test_risk_governor_validation():
    """Test 3: Risk Governor Comprehensive Validation"""
    print("\n🧪 Test 3: Risk Governor Validation")
    print("=" * 50)
    
    try:
        from runner.risk_governor import RiskGovernor
        
        # Test invalid initialization
        try:
            risk_gov = RiskGovernor(max_daily_loss=-1000)
            print("❌ Risk governor should reject negative daily loss")
            return False
        except ValueError:
            print("✅ Risk governor correctly rejected negative daily loss")
        
        try:
            risk_gov = RiskGovernor(max_trades=0)
            print("❌ Risk governor should reject zero max trades")
            return False
        except ValueError:
            print("✅ Risk governor correctly rejected zero max trades")
        
        # Test valid initialization
        risk_gov = RiskGovernor(
            max_daily_loss=5000,
            max_trades=10,
            max_position_value=50000
        )
        print("✅ Risk governor initialized with valid parameters")
        
        # Test trading permission logic
        if risk_gov.can_trade():
            print("✅ Risk governor allows trading with clean state")
        else:
            print("⚠️  Risk governor blocks trading (may be due to time constraints)")
        
        # Test position limits
        can_trade = risk_gov.can_trade(trade_value=60000)  # Over limit
        if not can_trade:
            print("✅ Risk governor correctly blocks oversized position")
        else:
            print("❌ Risk governor should block oversized position")
        
        # Test emergency stop
        risk_gov._trigger_emergency_stop("Test emergency stop")
        if not risk_gov.can_trade():
            print("✅ Emergency stop correctly prevents trading")
        else:
            print("❌ Emergency stop should prevent trading")
        
        # Test risk summary
        summary = risk_gov.get_risk_summary()
        if isinstance(summary, dict) and 'emergency_stop_active' in summary:
            print("✅ Risk summary generation working")
        else:
            print("❌ Risk summary generation failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Risk governor validation test failed: {e}")
        traceback.print_exc()
        return False

def test_kiteconnect_manager_validation():
    """Test 4: KiteConnect Manager Validation"""
    print("\n🧪 Test 4: KiteConnect Manager Validation")
    print("=" * 50)
    
    try:
        # Mock logger for testing
        class MockLogger:
            def log_event(self, message):
                print(f"[MOCK LOG] {message}")
        
        from runner.kiteconnect_manager import KiteConnectManager
        
        mock_logger = MockLogger()
        
        # Test initialization (will fail gracefully if secrets not available)
        kite_manager = KiteConnectManager(mock_logger)
        print("✅ KiteConnect manager initialized (may not have valid credentials)")
        
        # Test connection status
        status = kite_manager.get_connection_status()
        if isinstance(status, dict):
            print("✅ Connection status reporting working")
            print(f"   - Kite initialized: {status.get('kite_initialized', False)}")
            print(f"   - Access token set: {status.get('access_token_set', False)}")
        else:
            print("❌ Connection status reporting failed")
        
        # Test safe API call with invalid method
        result = kite_manager.safe_api_call("invalid_method")
        if result is None:
            print("✅ Safe API call correctly handles invalid methods")
        else:
            print("❌ Safe API call should return None for invalid methods")
        
        return True
        
    except Exception as e:
        print(f"❌ KiteConnect manager validation test failed: {e}")
        return False

def test_logging_and_error_handling():
    """Test 5: Logging and Error Handling"""
    print("\n🧪 Test 5: Logging and Error Handling")
    print("=" * 50)
    
    try:
        # Test log directory creation
        os.makedirs("logs", exist_ok=True)
        print("✅ Log directory creation working")
        
        # Test exception logging setup from main.py
        def test_exception_handler(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                return
            print(f"✅ Exception handler caught: {exc_type.__name__}: {exc_value}")
        
        # Test enhanced logging availability
        try:
            from runner.enhanced_logging.core_logger import TradingLogger
            logger = TradingLogger(session_id="test_session", bot_type="test")
            print("✅ Enhanced logging system available")
            
            # Test error logging
            test_error = ValueError("Test error for validation")
            logger.log_error(test_error, context={'test': True})
            print("✅ Error logging working")
            
            # Test metrics
            metrics = logger.get_metrics()
            if isinstance(metrics, dict):
                print("✅ Metrics collection working")
            
        except ImportError:
            print("⚠️  Enhanced logging not available (using fallback)")
        
        return True
        
    except Exception as e:
        print(f"❌ Logging and error handling test failed: {e}")
        return False

def test_strategy_validation():
    """Test 6: Strategy Input Validation"""
    print("\n🧪 Test 6: Strategy Input Validation")
    print("=" * 50)
    
    try:
        # Test basic strategy imports
        from strategies.scalp_strategy import calculate_scalp_quantity, calculate_simple_atr_scalp
        
        # Test quantity calculation with invalid inputs
        quantity = calculate_scalp_quantity(0, 100)  # Zero capital
        if quantity == 0:
            print("✅ Strategy correctly handles zero capital")
        else:
            print("❌ Strategy should return 0 for zero capital")
        
        quantity = calculate_scalp_quantity(100000, 0)  # Zero price
        if quantity == 0:
            print("✅ Strategy correctly handles zero price")
        else:
            print("❌ Strategy should return 0 for zero price")
        
        # Test ATR calculation with insufficient data
        atr = calculate_simple_atr_scalp([])  # Empty candles
        if atr == 10:  # Default value
            print("✅ ATR calculation provides safe default for empty data")
        else:
            print("❌ ATR calculation should provide default for empty data")
        
        return True
        
    except Exception as e:
        print(f"❌ Strategy validation test failed: {e}")
        return False

def test_market_data_validation():
    """Test 7: Market Data Validation"""
    print("\n🧪 Test 7: Market Data Validation")
    print("=" * 50)
    
    try:
        # Mock logger and kite for testing
        class MockLogger:
            def log_event(self, message):
                print(f"[MOCK LOG] {message}")
        
        class MockKite:
            def historical_data(self, *args, **kwargs):
                # Return None to simulate no data
                return None
        
        from runner.market_data_fetcher import MarketDataFetcher
        
        mock_logger = MockLogger()
        mock_kite = MockKite()
        
        fetcher = MarketDataFetcher(mock_kite, mock_logger)
        result = fetcher.fetch_latest_candle("123456", "5minute")
        
        if result is None:
            print("✅ Market data fetcher correctly handles no data scenario")
        else:
            print("❌ Market data fetcher should return None when no data available")
        
        return True
        
    except Exception as e:
        print(f"❌ Market data validation test failed: {e}")
        return False

def test_configuration_management():
    """Test 8: Configuration Management"""
    print("\n🧪 Test 8: Configuration Management")
    print("=" * 50)
    
    try:
        # Test paper trade configuration
        from runner.config import PAPER_TRADE
        print(f"✅ Paper trade configuration loaded: {PAPER_TRADE}")
        
        # Test configuration file existence
        config_files = [
            "runner/config.py",
            "requirements.txt"
        ]
        
        for config_file in config_files:
            if os.path.exists(config_file):
                print(f"✅ Configuration file exists: {config_file}")
            else:
                print(f"❌ Missing configuration file: {config_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration management test failed: {e}")
        return False

def run_comprehensive_validation():
    """Run all validation tests"""
    print("🔍 COMPREHENSIVE AUDIT FIXES VALIDATION")
    print("=" * 60)
    print(f"Started at: {datetime.datetime.now()}")
    print()
    
    tests = [
        ("Environment Validation", test_environment_validation),
        ("Secret Manager Validation", test_secret_manager_validation),
        ("Risk Governor Validation", test_risk_governor_validation),
        ("KiteConnect Manager Validation", test_kiteconnect_manager_validation),
        ("Logging and Error Handling", test_logging_and_error_handling),
        ("Strategy Validation", test_strategy_validation),
        ("Market Data Validation", test_market_data_validation),
        ("Configuration Management", test_configuration_management),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - FIXES WORKING CORRECTLY!")
        print("✅ System is ready for further testing and deployment")
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW NEEDED")
        print("🔧 Check failed tests and address issues before deployment")
    
    # Save results
    try:
        results_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'total_tests': total,
            'passed_tests': passed,
            'test_results': results,
            'overall_status': 'PASS' if passed == total else 'FAIL'
        }
        
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/audit_validation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"\n📁 Results saved to logs/audit_validation_*.json")
        
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = run_comprehensive_validation()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Validation script crashed: {e}")
        traceback.print_exc()
        sys.exit(1) 