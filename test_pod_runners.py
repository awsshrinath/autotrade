#!/usr/bin/env python3
"""
Test script to verify that pod runners can start without crashing
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

def test_runner_imports():
    """Test that all runner scripts can be imported"""
    print("🔍 Testing runner script imports...")
    
    test_results = {}
    
    # Test main runner
    try:
        from runner import main_runner_lightweight
        print("✅ main_runner_lightweight: Import OK")
        test_results['main_runner_lightweight'] = True
    except Exception as e:
        print(f"❌ main_runner_lightweight: {e}")
        test_results['main_runner_lightweight'] = False
    
    # Test trading runners
    runners = [
        ('stock_trading.stock_runner', 'stock_runner'),
        ('futures_trading.futures_runner', 'futures_runner'), 
        ('options_trading.options_runner', 'options_runner')
    ]
    
    for module_path, name in runners:
        try:
            __import__(module_path)
            print(f"✅ {name}: Import OK")
            test_results[name] = True
        except Exception as e:
            print(f"❌ {name}: {e}")
            test_results[name] = False
    
    # Test cognitive services
    cognitive_services = [
        ('runner.cognitive_system', 'cognitive_system'),
        ('runner.thought_journal', 'thought_journal'),
        ('runner.cognitive_memory', 'cognitive_memory')
    ]
    
    for module_path, name in cognitive_services:
        try:
            __import__(module_path)
            print(f"✅ {name}: Import OK")
            test_results[name] = True
        except Exception as e:
            print(f"❌ {name}: {e}")
            test_results[name] = False
    
    return test_results

def test_main_functions():
    """Test that main functions can be called"""
    print("\n🔍 Testing main function availability...")
    
    test_results = {}
    
    # Test scripts with main functions
    scripts = [
        ('runner.main_runner_lightweight', 'main_runner_lightweight'),
        ('runner.cognitive_system', 'cognitive_system'),
        ('runner.thought_journal', 'thought_journal'),
        ('runner.cognitive_memory', 'cognitive_memory')
    ]
    
    for module_path, name in scripts:
        try:
            module = __import__(module_path, fromlist=['main'])
            if hasattr(module, 'main'):
                print(f"✅ {name}: main() function available")
                test_results[name] = True
            else:
                print(f"⚠️  {name}: No main() function")
                test_results[name] = False
        except Exception as e:
            print(f"❌ {name}: {e}")
            test_results[name] = False
    
    return test_results

def main():
    """Run all tests"""
    print("🚀 Testing pod runner scripts...\n")
    
    import_results = test_runner_imports()
    main_func_results = test_main_functions()
    
    print("\n📊 Test Summary:")
    print("================")
    
    total_tests = len(import_results) + len(main_func_results)
    passed_tests = sum(import_results.values()) + sum(main_func_results.values())
    
    print(f"Import Tests: {sum(import_results.values())}/{len(import_results)} passed")
    print(f"Main Function Tests: {sum(main_func_results.values())}/{len(main_func_results)} passed")
    print(f"Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Pod runners should start successfully.")
        return True
    else:
        print("⚠️  Some tests failed. Manual review needed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)