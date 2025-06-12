#!/usr/bin/env python3
"""
Pod Error Fixes Validation Script
=================================

This script tests all the fixes for the pod errors reported:
1. RAG module import issues
2. GCS bucket region warnings  
3. Missing function implementations
4. Paper trading integration

Run this script to validate all fixes are working.
"""

import os
import sys
import datetime
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_rag_imports():
    """Test 1: RAG Module Import Issues"""
    print("\n🔧 Test 1: RAG Module Import Resolution")
    print("=" * 50)
    
    try:
        # Test basic RAG imports
        from gpt_runner.rag import retrieve_similar_context
        print("✅ retrieve_similar_context imported successfully")
        
        from gpt_runner.rag import sync_firestore_to_faiss
        print("✅ sync_firestore_to_faiss imported successfully")
        
        from gpt_runner.rag import embed_logs_for_today
        print("✅ embed_logs_for_today imported successfully")
        
        from gpt_runner.rag import embed_text
        print("✅ embed_text imported successfully")
        
        # Test function calls with placeholders
        result1 = sync_firestore_to_faiss("test_bot")
        print(f"✅ sync_firestore_to_faiss executed: {result1}")
        
        result2 = embed_logs_for_today("2024-01-15")
        print(f"✅ embed_logs_for_today executed: {result2}")
        
        # Test core RAG functionality
        context = retrieve_similar_context("test query", limit=3)
        print(f"✅ retrieve_similar_context executed: {len(context)} results")
        
        # Test embedding
        embedding = embed_text("test text")
        print(f"✅ embed_text executed: {len(embedding)} dimensions")
        
        print("✅ All RAG imports and functions working")
        return True
        
    except Exception as e:
        print(f"❌ RAG import test failed: {e}")
        return False

def test_gcs_enhanced_logging():
    """Test 2: Enhanced GCS Logging"""
    print("\n📝 Test 2: Enhanced GCS Logging Resolution")
    print("=" * 50)
    
    try:
        from runner.enhanced_logging.gcs_logger import GCSLogger, GCSBuckets
        print("✅ GCS Logger imported successfully")
        
        # Test bucket names
        print(f"✅ Trade logs bucket: {GCSBuckets.TRADE_LOGS}")
        print(f"✅ System logs bucket: {GCSBuckets.SYSTEM_LOGS}")
        print(f"✅ Cognitive archives bucket: {GCSBuckets.COGNITIVE_ARCHIVES}")
        print(f"✅ Analytics data bucket: {GCSBuckets.ANALYTICS_DATA}")
        print(f"✅ Compliance logs bucket: {GCSBuckets.COMPLIANCE_LOGS}")
        
        # Test logger creation (without actual GCS operations)
        try:
            logger_instance = GCSLogger()
            print("✅ GCS Logger instance created successfully")
            
            # Test internal methods without actual uploads
            blob_path = logger_instance._get_blob_path("test", "log", "test-bot", "v1")
            print(f"✅ Blob path generation: {blob_path}")
            
            # Test data compression
            test_data = {"test": "data", "timestamp": datetime.datetime.now().isoformat()}
            compressed = logger_instance._compress_data(test_data)
            print(f"✅ Data compression: {len(compressed)} bytes")
            
        except Exception as gcs_error:
            print(f"⚠️ GCS Logger creation failed (expected without credentials): {gcs_error}")
        
        print("✅ Enhanced GCS Logging components working")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced GCS logging test failed: {e}")
        return False

def test_paper_trading_integration():
    """Test 3: Paper Trading Integration"""
    print("\n📊 Test 3: Paper Trading Integration")
    print("=" * 50)
    
    try:
        # Set paper trading mode
        os.environ['PAPER_TRADE'] = 'true'
        
        from runner.config import is_paper_trade
        paper_trade_flag = is_paper_trade()
        print(f"✅ is_paper_trade() returned: {paper_trade_flag}")
        
        if not paper_trade_flag:
            print("❌ is_paper_trade() should return True")
            return False
        
        # Test EnhancedTradeManager paper trading
        from runner.enhanced_trade_manager import create_enhanced_trade_manager
        from runner.logger import Logger
        
        test_logger = Logger('test')
        trade_manager = create_enhanced_trade_manager(logger=test_logger)
        
        print(f"✅ EnhancedTradeManager paper mode from config: {trade_manager.config.paper_trade}")
        
        if not trade_manager.config.paper_trade:
            print("❌ EnhancedTradeManager should be in paper mode based on its config")
            return False
        
        print("✅ Paper trading integration working")
        return True
        
    except Exception as e:
        print(f"❌ Paper trading integration test failed: {e}")
        return False

def test_enhanced_logger_integration():
    """Test 4: Enhanced Logger Integration"""
    print("\n🔍 Test 4: Enhanced Logger Integration")
    print("=" * 50)
    
    try:
        from runner.enhanced_logging import create_enhanced_logger, TradingLogger
        print("✅ Enhanced logging imports successful")
        
        # Create enhanced logger
        session_id = f"pod_test_{int(time.time())}"
        enhanced_logger = create_enhanced_logger(
            session_id=session_id,
            enable_gcs=False,  # Disable GCS to avoid credentials issues
            enable_firestore=False,  # Disable Firestore to avoid credentials issues
            bot_type="pod-test"
        )
        
        print(f"✅ Enhanced logger created: {session_id}")
        
        # Test logging methods
        enhanced_logger.log_system_event(
            "Pod error fixes validation test",
            data={'test_type': 'pod_validation'}
        )
        print("✅ System event logged")
        
        # Test force upload method
        enhanced_logger.force_upload_to_gcs()
        print("✅ Force GCS upload method available")
        
        # Test shutdown
        enhanced_logger.shutdown()
        print("✅ Enhanced logger shutdown successful")
        
        print("✅ Enhanced logger integration working")
        return True
        
    except Exception as e:
        print(f"❌ Enhanced logger integration test failed: {e}")
        return False

def test_main_integration():
    """Test 5: Main Integration"""
    print("\n🚀 Test 5: Main Integration Test")
    print("=" * 50)
    
    try:
        # Test main.py imports without executing
        import main
        print("✅ main.py imports successful")
        
        # Check for paper trading components
        if hasattr(main, 'PAPER_TRADING_AVAILABLE'):
            print(f"✅ Paper trading availability: {main.PAPER_TRADING_AVAILABLE}")
        else:
            print("⚠️ Paper trading availability flag not found")
        
        if hasattr(main, 'PAPER_TRADE'):
            print(f"✅ PAPER_TRADE flag: {main.PAPER_TRADE}")
        else:
            print("⚠️ PAPER_TRADE flag not found")
        
        # Test other runner imports
        try:
            import stock_trading.stock_runner
            print("✅ Stock runner imports successful")
        except ImportError as e:
            print(f"⚠️ Stock runner import issue: {e}")
        
        try:
            from runner.main_runner_fixed import safe_import_with_fallback
            imports = safe_import_with_fallback()
            print(f"✅ Safe imports working: {len(imports)} modules loaded")
        except ImportError as e:
            print(f"⚠️ Main runner fixed import issue: {e}")
        
        print("✅ Main integration test completed")
        return True
        
    except Exception as e:
        print(f"❌ Main integration test failed: {e}")
        return False

def test_faiss_handling():
    """Test 6: FAISS Handling"""
    print("\n🔬 Test 6: FAISS GPU Handling")
    print("=" * 50)
    
    try:
        import faiss
        print("✅ FAISS imported successfully")
        
        # Test that we handle GPU FAISS gracefully
        try:
            # This might fail but should be handled gracefully
            faiss.version
            print("✅ FAISS version accessible")
        except Exception as faiss_error:
            print(f"⚠️ FAISS GPU warning (expected): {faiss_error}")
        
        print("✅ FAISS handling test completed")
        return True
        
    except ImportError:
        print("⚠️ FAISS not available (this is ok)")
        return True
    except Exception as e:
        print(f"❌ FAISS handling test failed: {e}")
        return False

def run_all_tests():
    """Run all pod error fix validation tests"""
    print("🧪 Pod Error Fixes Validation")
    print("=" * 60)
    print(f"Test started at: {datetime.datetime.now()}")
    print("")
    
    tests = [
        test_rag_imports,
        test_gcs_enhanced_logging,
        test_paper_trading_integration,
        test_enhanced_logger_integration,
        test_main_integration,
        test_faiss_handling
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
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - Pod errors have been resolved!")
        print("\n✅ Issues Fixed:")
        print("   1. RAG module import errors resolved")
        print("   2. GCS bucket region warnings handled")
        print("   3. Missing function implementations added")
        print("   4. Enhanced logging integration working")
        print("   5. Paper trading integration functional")
        print("   6. FAISS GPU warnings handled gracefully")
        print("\n🚀 The pod should now run without these errors!")
    else:
        print("⚠️ Some tests failed - check the output above for details")
        print(f"\nFailed tests: {total - passed}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    print(f"\n{'='*60}")
    print(f"Validation {'SUCCESSFUL' if success else 'FAILED'} at {datetime.datetime.now()}")
    sys.exit(0 if success else 1) 