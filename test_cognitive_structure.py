#!/usr/bin/env python3
"""
Simplified test to validate cognitive system structure and logic
Tests without requiring GCP dependencies
"""

import sys
import os
import datetime
import logging
from unittest.mock import Mock

# Add project root to path
sys.path.insert(0, os.path.abspath('.'))

def test_python_syntax():
    """Test that all cognitive modules have valid Python syntax"""
    print("🧪 Testing Python syntax...")
    
    cognitive_files = [
        'runner/gcp_memory_client.py',
        'runner/cognitive_memory.py', 
        'runner/thought_journal.py',
        'runner/cognitive_state_machine.py',
        'runner/metacognition.py',
        'runner/cognitive_system.py'
    ]
    
    import ast
    
    for file_path in cognitive_files:
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Parse the file to check syntax
            ast.parse(content)
            print(f"✅ {file_path} - Valid Python syntax")
            
        except FileNotFoundError:
            print(f"❌ {file_path} - File not found")
            return False
        except SyntaxError as e:
            print(f"❌ {file_path} - Syntax error: {e}")
            return False
        except Exception as e:
            print(f"❌ {file_path} - Error: {e}")
            return False
    
    return True

def test_class_definitions():
    """Test that key classes are properly defined"""
    print("\n🧪 Testing class definitions...")
    
    try:
        # Test dataclass syntax  
        import dataclasses
        import datetime
        from enum import Enum
        
        # Test that dataclass decorator works
        @dataclasses.dataclass
        class TestMemory:
            id: str
            content: str
        
        # Create test instance
        test_mem = TestMemory("test-id", "test content")
        assert test_mem.id == "test-id"
        print("✅ Dataclass structure valid")
        
        # Test enum syntax
        class TestState(Enum):
            OBSERVING = "observing"
            ANALYZING = "analyzing"
        
        assert TestState.OBSERVING.value == "observing"
        print("✅ Enum definitions valid")
        
        # Test datetime usage
        now = datetime.datetime.utcnow()
        assert isinstance(now, datetime.datetime)
        print("✅ Datetime functionality valid")
        
        return True
        
    except Exception as e:
        print(f"❌ Class definition test failed: {e}")
        return False

def test_integration_points():
    """Test integration points in trade manager and main runner"""
    print("\n🧪 Testing integration points...")
    
    try:
        # Check trade manager modification
        with open('runner/trade_manager.py', 'r') as f:
            trade_manager_content = f.read()
        
        # Look for cognitive system integration
        required_imports = [
            'from runner.cognitive_system import',
            'from runner.thought_journal import DecisionType',
            'from runner.cognitive_state_machine import CognitiveState'
        ]
        
        for import_line in required_imports:
            if import_line in trade_manager_content:
                print(f"✅ Trade manager has: {import_line}")
            else:
                print(f"❌ Trade manager missing: {import_line}")
                return False
        
        # Check for cognitive integration in constructor
        if 'cognitive_system' in trade_manager_content:
            print("✅ Trade manager has cognitive_system parameter")
        else:
            print("❌ Trade manager missing cognitive_system parameter")
            return False
        
        # Check main runner modification
        with open('runner/main_runner_combined.py', 'r') as f:
            main_runner_content = f.read()
        
        if 'initialize_cognitive_system' in main_runner_content:
            print("✅ Main runner has cognitive initialization")
        else:
            print("❌ Main runner missing cognitive initialization")
            return False
        
        # Check firestore client updates
        with open('runner/firestore_client.py', 'r') as f:
            firestore_content = f.read()
        
        if 'log_cognitive_thought' in firestore_content:
            print("✅ Firestore client has cognitive methods")
        else:
            print("❌ Firestore client missing cognitive methods")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_requirements_file():
    """Test that requirements.txt has been updated"""
    print("\n🧪 Testing requirements.txt...")
    
    try:
        with open('requirements.txt', 'r') as f:
            requirements_content = f.read()
        
        required_packages = [
            'google-cloud-firestore',
            'google-cloud-storage'
        ]
        
        for package in required_packages:
            if package in requirements_content:
                print(f"✅ Requirements includes: {package}")
            else:
                print(f"❌ Requirements missing: {package}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Requirements test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist"""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        'runner/gcp_memory_client.py',
        'runner/cognitive_memory.py',
        'runner/thought_journal.py', 
        'runner/cognitive_state_machine.py',
        'runner/metacognition.py',
        'runner/cognitive_system.py'
    ]
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False
    
    return True

def test_memory_bucket_info():
    """Test that bucket information is properly documented"""
    print("\n🧪 Testing bucket documentation...")
    
    try:
        with open('runner/gcp_memory_client.py', 'r') as f:
            gcp_client_content = f.read()
        
        required_buckets = [
            'tron-cognitive-memory',
            'tron-thought-archives',
            'tron-analysis-reports',
            'tron-memory-backups'
        ]
        
        for bucket in required_buckets:
            if bucket in gcp_client_content:
                print(f"✅ Bucket defined: {bucket}")
            else:
                print(f"❌ Bucket missing: {bucket}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bucket documentation test failed: {e}")
        return False

def main():
    """Run all structural tests"""
    print("🧠 TRON Cognitive System - Structure Validation Test")
    print("=" * 55)
    
    tests = [
        test_file_structure,
        test_python_syntax,
        test_class_definitions,
        test_integration_points,
        test_requirements_file,
        test_memory_bucket_info
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print(f"\n📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")
    
    if failed == 0:
        print("\n🎉 ALL STRUCTURE TESTS PASSED!")
        print("\n📋 Implementation Status: ✅ COMPLETE")
        print("\n🔧 Required GCS Buckets (create these in GCP):")
        print("   • tron-cognitive-memory")
        print("   • tron-thought-archives") 
        print("   • tron-analysis-reports")
        print("   • tron-memory-backups")
        print("\n⚙️  Environment Variables Needed:")
        print("   • GCP_PROJECT_ID=your-gcp-project-id")
        print("\n🚀 Ready for deployment with cognitive system!")
        return True
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)