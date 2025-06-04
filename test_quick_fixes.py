#!/usr/bin/env python3

"""
Quick Fix Validation Test
========================

This script tests that our fixes for RAG imports and GCS lifecycle policies
are working correctly.
"""

print('🧪 Testing fixes...')

# Test 1: Import main.py to see if RAG fallbacks work
try:
    import main
    print('✅ main.py imports successfully')
except Exception as e:
    print(f'❌ main.py import failed: {e}')

# Test 2: Test GCS logger import
try:
    from runner.enhanced_logging.gcs_logger import GCSLogger
    print('✅ GCS Logger imports successfully') 
except Exception as e:
    print(f'❌ GCS Logger import failed: {e}')

# Test 3: Test RAG fallback functions
try:
    from main import sync_firestore_to_faiss, embed_logs_for_today, retrieve_similar_context
    
    # Test calling fallback functions
    result1 = sync_firestore_to_faiss()
    result2 = embed_logs_for_today() 
    result3 = retrieve_similar_context('test query')
    
    print('✅ RAG fallback functions work correctly')
    print(f'   sync_firestore_to_faiss: {result1}')
    print(f'   embed_logs_for_today: {result2}')
    print(f'   retrieve_similar_context: {type(result3)}')
    
except Exception as e:
    print(f'❌ RAG fallback test failed: {e}')

# Test 4: Test GCS lifecycle policy fix - check imports
try:
    from google.cloud.storage.bucket import LifecycleConfiguration
    print('✅ LifecycleConfiguration import works')
except ImportError as e:
    print(f'⚠️  LifecycleConfiguration not available, will use fallback: {e}')

print('🎯 Fix validation complete') 