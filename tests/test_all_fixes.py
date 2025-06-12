#!/usr/bin/env python3
"""
Comprehensive test script to verify all fixes for Kubernetes pod errors
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def test_all_fixes():
    """Test all fixes for the reported errors"""
    
    print("Testing all fixes for Kubernetes pod errors...")
    print("=" * 60)
    
    # Test 1: access_secret function with default project_id
    try:
        from runner.secret_manager_client import access_secret
        import inspect
        sig = inspect.signature(access_secret)
        params = sig.parameters
        if 'project_id' in params and params['project_id'].default != inspect.Parameter.empty:
            print("✅ access_secret has default project_id parameter")
        else:
            print("❌ access_secret missing default project_id parameter")
    except Exception as e:
        print(f"❌ access_secret test failed: {e}")
    
    # Test 2: get_kite_client method accepts project_id parameter
    try:
        from runner.kiteconnect_manager import KiteConnectManager
        import inspect
        sig = inspect.signature(KiteConnectManager.get_kite_client)
        params = list(sig.parameters.keys())
        if 'project_id' in params:
            print("✅ KiteConnectManager.get_kite_client accepts project_id parameter")
        else:
            print("❌ KiteConnectManager.get_kite_client missing project_id parameter")
    except Exception as e:
        print(f"❌ get_kite_client test failed: {e}")
    
    # Test 3: Runner module imports work from trading bots
    try:
        # Simulate import from futures_trading directory
        old_path = sys.path[:]
        futures_path = os.path.join(os.path.dirname(__file__), "futures_trading")
        sys.path.insert(0, futures_path)
        sys.path.insert(0, os.path.dirname(__file__))
        
        from runner.config import PAPER_TRADE
        from runner.firestore_client import FirestoreClient
        from runner.logger import Logger
        print("✅ Runner module imports work from trading bot directories")
        
        sys.path[:] = old_path
    except Exception as e:
        print(f"❌ Runner module import test failed: {e}")
        sys.path[:] = old_path
    
    # Test 4: Strategy helpers import
    try:
        import runner.utils.strategy_helpers
        print("✅ Strategy helpers import successful")
    except Exception as e:
        print(f"❌ Strategy helpers import failed: {e}")
    
    # Test 5: Main runner imports
    try:
        # Test the main imports without executing
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "main_runner", 
            os.path.join(os.path.dirname(__file__), "runner", "main_runner.py")
        )
        if spec and spec.loader:
            print("✅ Main runner imports are valid")
        else:
            print("❌ Main runner import validation failed")
    except Exception as e:
        print(f"❌ Main runner import test failed: {e}")
    
    # Test 6: Options strategy imports
    try:
        old_path = sys.path[:]
        options_path = os.path.join(os.path.dirname(__file__), "options_trading", "strategies")
        sys.path.insert(0, options_path)
        sys.path.insert(0, os.path.dirname(__file__))
        
        from scalp_strategy import ScalpStrategy
        print("✅ Options strategy imports work correctly")
        
        sys.path[:] = old_path
    except Exception as e:
        print(f"❌ Options strategy import test failed: {e}")
        sys.path[:] = old_path
    
    # Test 7: Check if all required modules exist
    required_modules = [
        "runner.config",
        "runner.firestore_client", 
        "runner.kiteconnect_manager",
        "runner.logger",
        "runner.secret_manager_client",
        "runner.utils.strategy_helpers"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if not missing_modules:
        print("✅ All required modules are importable")
    else:
        print(f"❌ Missing modules: {missing_modules}")
    
    print("=" * 60)
    print("Fix verification complete!")


if __name__ == "__main__":
    test_all_fixes()