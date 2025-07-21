#!/usr/bin/env python3
"""
Test script to verify pod crash fixes
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def test_critical_imports():
    """Test that all critical imports work"""
    print("🔍 Testing critical imports...")
    
    try:
        from runner.config import initialize_config, get_config, PAPER_TRADE
        print("✅ Config imports: OK")
    except Exception as e:
        print(f"❌ Config imports: {e}")
        return False

    try:
        from runner.trade_manager import create_enhanced_trade_manager
        print("✅ Trade manager imports: OK")
    except Exception as e:
        print(f"❌ Trade manager imports: {e}")
        return False

    try:
        from runner.utils.paper_trade_utils import simulate_exit
        print("✅ Paper trade utils: OK")
    except Exception as e:
        print(f"❌ Paper trade utils: {e}")
        return False

    try:
        from runner.firestore_client import FirestoreClient
        print("✅ Firestore client: OK")
    except Exception as e:
        print(f"❌ Firestore client: {e}")
        return False
        
    return True

def test_config_initialization():
    """Test config initialization"""
    print("\n🔍 Testing configuration initialization...")
    
    try:
        from runner.config import initialize_config
        result = initialize_config()
        if result:
            print("✅ Configuration initialization: OK")
        else:
            print("⚠️  Configuration initialization returned False")
        return result
    except Exception as e:
        print(f"❌ Configuration initialization: {e}")
        return False

def test_gcp_clients():
    """Test GCP client initialization with graceful fallbacks"""
    print("\n🔍 Testing GCP client initialization...")
    
    try:
        from runner.firestore_client import FirestoreClient
        client = FirestoreClient()
        if client.available:
            print("✅ Firestore client: Available")
        else:
            print("⚠️  Firestore client: Not available (expected in local environment)")
        return True
    except Exception as e:
        print(f"❌ Firestore client: {e}")
        return False

def test_trading_runners():
    """Test that trading runners can be imported"""
    print("\n🔍 Testing trading runner imports...")
    
    try:
        # Test that we can import the modules without crashing
        import futures_trading.futures_runner
        print("✅ Futures runner: OK")
        
        import stock_trading.stock_runner  
        print("✅ Stock runner: OK")
        
        import options_trading.options_runner
        print("✅ Options runner: OK")
        
        return True
    except Exception as e:
        print(f"❌ Trading runners: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing pod crash fixes...\n")
    
    tests = [
        test_critical_imports,
        test_config_initialization,
        test_gcp_clients,
        test_trading_runners
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Pod crash fixes appear to be working.")
        return True
    else:
        print("⚠️  Some tests failed. Manual review may be needed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)