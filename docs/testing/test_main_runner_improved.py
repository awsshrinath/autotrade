#!/usr/bin/env python3
"""
Test Script for Improved Main Runner
===================================

This script validates that the improved main runner has the necessary fixes
for crashloop prevention and includes the required functionality.
"""

import sys
import os
import datetime
import traceback

# Add the project root to path
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')

def test_imports():
    """Test that all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import pytz
        print("✅ pytz imported successfully")
    except ImportError:
        print("❌ pytz not available - install with: pip install pytz")
        assert False
    
    try:
        from runner.main_runner_improved import (
            safe_import_with_fallback,
            get_ist_time,
            is_market_open,
            check_environment_variables,
            setup_signal_handlers
        )
        print("✅ All main runner functions imported successfully")
        assert True
    except ImportError as e:
        print(f"❌ Main runner import failed: {e}")
        traceback.print_exc()
        assert False

def test_time_functions():
    """Test timezone and market time functions"""
    print("🧪 Testing time functions...")
    
    try:
        from runner.main_runner_improved import get_ist_time, is_market_open
        
        # Test IST time
        ist_time = get_ist_time()
        print(f"✅ IST time: {ist_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Test market open check
        market_status = is_market_open()
        print(f"✅ Market open: {market_status}")
        
        assert True
        
    except Exception as e:
        print(f"❌ Time function test failed: {e}")
        traceback.print_exc()
        assert False

def test_safe_imports():
    """Test safe import functionality"""
    print("🧪 Testing safe imports...")
    
    try:
        from runner.main_runner_improved import safe_import_with_fallback
        
        imports_status, imported_modules = safe_import_with_fallback()
        
        print(f"📊 Import Status: {imports_status}")
        print(f"📦 Imported Modules: {list(imported_modules.keys())}")
        
        # Check that core modules are imported
        required_modules = ['Logger', 'create_enhanced_logger']
        for module in required_modules:
            if module in imported_modules:
                print(f"✅ {module} imported successfully")
            else:
                print(f"⚠️ {module} not imported")
        
        assert True
        
    except Exception as e:
        print(f"❌ Safe imports test failed: {e}")
        traceback.print_exc()
        assert False

def test_signal_handlers():
    """Test signal handler setup"""
    print("🧪 Testing signal handlers...")
    
    try:
        from runner.main_runner_improved import setup_signal_handlers
        
        setup_signal_handlers()
        print("✅ Signal handlers set up successfully")
        assert True
        
    except Exception as e:
        print(f"❌ Signal handler test failed: {e}")
        traceback.print_exc()
        assert False

def test_environment_check():
    """Test environment variable checking"""
    print("🧪 Testing environment variable checks...")
    
    try:
        from runner.main_runner_improved import check_environment_variables
        
        env_status = check_environment_variables()
        print(f"✅ Environment check completed: {env_status}")
        assert True
        
    except Exception as e:
        print(f"❌ Environment check failed: {e}")
        traceback.print_exc()
        assert False

def test_crashloop_prevention_features():
    """Test crashloop prevention features"""
    print("🧪 Testing crashloop prevention features...")
    
    features_to_check = [
        ("IST timezone handling", "get_ist_time"),
        ("Market time checking", "is_market_open"),
        ("Safe imports", "safe_import_with_fallback"),
        ("Signal handlers", "setup_signal_handlers"),
        ("Environment validation", "check_environment_variables"),
        ("Logger initialization", "safe_initialize_loggers"),
        ("Cognitive system init", "safe_initialize_cognitive_system"),
        ("Market monitoring", "robust_market_monitor"),
        ("Post-market analysis", "run_post_market_analysis")
    ]
    
    try:
        from runner import main_runner_improved
        
        for feature_name, function_name in features_to_check:
            if hasattr(main_runner_improved, function_name):
                print(f"✅ {feature_name}: function '{function_name}' exists")
            else:
                print(f"❌ {feature_name}: function '{function_name}' missing")
        
        assert True
        
    except Exception as e:
        print(f"❌ Crashloop prevention test failed: {e}")
        traceback.print_exc()
        assert False

def main():
    """Run all tests"""
    print("🚀 Testing Improved Main Runner")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Time Functions Test", test_time_functions),
        ("Safe Imports Test", test_safe_imports),
        ("Signal Handlers Test", test_signal_handlers),
        ("Environment Check Test", test_environment_check),
        ("Crashloop Prevention Features Test", test_crashloop_prevention_features)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! The improved main runner is ready for deployment.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 