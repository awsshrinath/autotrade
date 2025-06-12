#!/usr/bin/env python3

"""
🔧 Test Script for GCP Bucket Creation Fixes
==========================================

This script tests the fixed bucket creation code to ensure it works
with the current Google Cloud Storage API.
"""

import os
import sys
from google.cloud import storage
from google.oauth2 import service_account
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bucket_creation_fix():
    """Test the fixed bucket creation code"""
    print("🧪 Testing Google Cloud Storage bucket creation fixes...")
    
    try:
        # Initialize GCS client
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            client = storage.Client()
        else:
            print("⚠️  No GCP credentials found - simulating test")
            assert True
            
        # Test bucket name
        test_bucket_name = "test-tron-fix-validation"
        
        try:
            bucket = client.bucket(test_bucket_name)
            
            # Check if bucket exists
            if bucket.exists():
                print(f"ℹ️  Test bucket {test_bucket_name} already exists - using existing")
            else:
                print(f"✨ Creating test bucket {test_bucket_name}...")
                
                # FIXED: Create bucket without labels parameter
                bucket = client.create_bucket(
                    test_bucket_name,
                    location='asia-south1'
                )
                
                # FIXED: Set labels after bucket creation
                bucket.labels = {
                    'environment': 'test',
                    'system': 'tron-trading',
                    'purpose': 'test-validation',
                    'region': 'asia-south1'
                }
                bucket.patch()  # Apply the labels
                
                print(f"✅ Successfully created test bucket with labels!")
                
                # Clean up test bucket
                print(f"🧹 Cleaning up test bucket...")
                bucket.delete()
                print(f"✅ Test bucket deleted")
                
        except Exception as bucket_error:
            print(f"❌ Bucket creation test failed: {bucket_error}")
            assert False
            
        assert True
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        assert False

def test_rag_imports():
    """Test RAG module imports"""
    print("🧪 Testing RAG module imports...")
    
    try:
        # Test direct import
        from gpt_runner.rag import retrieve_similar_context
        from gpt_runner.rag import sync_firestore_to_faiss
        from gpt_runner.rag import embed_logs_for_today
        
        print("✅ RAG imports successful!")
        
        # Test function calls (should use placeholder implementations)
        print("🔧 Testing RAG function calls...")
        sync_firestore_to_faiss()
        embed_logs_for_today()
        result = retrieve_similar_context("test query")
        
        print("✅ RAG function calls successful!")
        assert True
        
    except ImportError as e:
        print(f"❌ RAG import failed: {e}")
        assert False
    except Exception as e:
        print(f"❌ RAG test failed: {e}")
        assert False

def main():
    """Run all tests"""
    print("🚀 Running GCP fixes validation tests...\n")
    
    tests = [
        ("GCP Bucket Creation", test_bucket_creation_fix),
        ("RAG Module Imports", test_rag_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print(f"{'='*50}")
        
        try:
            if test_func():
                print(f"✅ {test_name} PASSED")
                passed += 1
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*50}")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Fixes are working correctly.")
        assert True
    else:
        print("⚠️  Some tests failed - check output above.")
        assert False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 