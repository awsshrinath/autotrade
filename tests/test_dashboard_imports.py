#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add paths
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/runner')
sys.path.insert(0, '/app/gpt_runner')

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    # Test basic imports
    try:
        import datetime
        import time
        print("✓ Basic imports successful")
    except Exception as e:
        print(f"✗ Basic imports failed: {e}")
        return False
    
    # Test RAG imports
    try:
        from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss
        print("✓ faiss_firestore_adapter import successful")
    except Exception as e:
        print(f"✗ faiss_firestore_adapter import failed: {e}")
    
    try:
        from gpt_runner.rag.rag_worker import embed_logs_for_today
        print("✓ rag_worker import successful")
    except Exception as e:
        print(f"✗ rag_worker import failed: {e}")
    
    # Test GPT monitor imports
    try:
        from gpt_runner.rag.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
        print("✓ GPTSelfImprovementMonitor (rag) import successful")
    except Exception as e:
        print(f"✗ GPTSelfImprovementMonitor (rag) import failed: {e}")
        try:
            from runner.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
            print("✓ GPTSelfImprovementMonitor (runner) fallback successful")
        except Exception as e2:
            print(f"✗ GPTSelfImprovementMonitor fallback failed: {e2}")
    
    # Test runner imports
    try:
        from runner.firestore_client import FirestoreClient
        from runner.logger import Logger
        from runner.enhanced_logger import create_enhanced_logger
        print("✓ Runner imports successful")
    except Exception as e:
        print(f"✗ Runner imports failed: {e}")
        return False
    
    # Test dashboard imports if available
    try:
        from dashboard.components.overview import OverviewPage
        print("✓ Dashboard imports successful")
    except Exception as e:
        print(f"✗ Dashboard imports failed: {e}")
    
    print("Import testing completed!")
    return True

if __name__ == "__main__":
    print(f"Python path: {sys.path}")
    print(f"Current directory: {os.getcwd()}")
    
    # Show file structure
    if os.path.exists('/app'):
        print("Files in /app:")
        for item in os.listdir('/app'):
            print(f"  {item}")
    
    if os.path.exists('/app/gpt_runner'):
        print("Files in /app/gpt_runner:")
        for item in os.listdir('/app/gpt_runner'):
            print(f"  {item}")
    
    if os.path.exists('/app/gpt_runner/rag'):
        print("Files in /app/gpt_runner/rag:")
        for item in os.listdir('/app/gpt_runner/rag'):
            print(f"  {item}")
    
    test_imports() 