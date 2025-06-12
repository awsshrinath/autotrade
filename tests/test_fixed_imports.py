#!/usr/bin/env python3
"""
Test script to verify that import fixes work correctly
"""

import sys
import os

def test_basic_imports():
    """Test basic Python imports"""
    try:
        import datetime
        import time
        import logging  # This should work now
        print("✓ Basic imports successful")
        return True
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False

def test_enhanced_logging():
    """Test our custom enhanced logging imports"""
    try:
        from runner.enhanced_logging import LogLevel, LogCategory
        print("✓ Enhanced logging imports successful")
        return True
    except Exception as e:
        print(f"✗ Enhanced logging imports failed: {e}")
        return False

def test_config_imports():
    """Test config imports"""
    try:
        from config.config_manager import get_config
        print("✓ Config imports successful")
        return True
    except Exception as e:
        print(f"✗ Config imports failed: {e}")
        return False

def test_gpt_runner_package():
    """Test gpt_runner package structure"""
    try:
        import gpt_runner
        print("✓ gpt_runner package importable")
        
        # Test if rag subpackage exists
        import gpt_runner.rag
        print("✓ gpt_runner.rag subpackage importable")
        return True
    except Exception as e:
        print(f"✗ gpt_runner package test failed: {e}")
        return False

def main():
    """Run all import tests"""
    print("=== Testing Fixed Imports ===")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}")
    print()
    
    tests = [
        test_basic_imports,
        test_enhanced_logging,
        test_config_imports,
        test_gpt_runner_package,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"=== Results: {passed}/{total} tests passed ===")
    
    if passed == total:
        print("🎉 All import fixes working correctly!")
        return True
    else:
        print("❌ Some imports still have issues")
        return False

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 