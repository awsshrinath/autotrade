#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

def test_imports():
    """Test all problematic imports"""
    
    print("Testing imports...")
    
    try:
        # Test 1: gpt_runner.rag import
        from gpt_runner.rag.gpt_self_improvement_monitor import GPTSelfImprovementMonitor
        print("✅ gpt_runner.rag.gpt_self_improvement_monitor import successful")
    except ImportError as e:
        print(f"❌ gpt_runner.rag.gpt_self_improvement_monitor import failed: {e}")
    
    try:
        # Test 2: embedder import (should not use sentence_transformers)
        from gpt_runner.rag.embedder import get_embedding
        print("✅ gpt_runner.rag.embedder import successful")
    except ImportError as e:
        print(f"❌ gpt_runner.rag.embedder import failed: {e}")
    
    try:
        # Test 3: MarketMonitor with get_sentiment method
        from runner.market_data import MarketDataFetcher, TechnicalIndicators
        from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier
        monitor = MarketMonitor()
        # Check if get_sentiment method exists
        if hasattr(monitor, 'get_sentiment'):
            print("✅ MarketMonitor.get_sentiment method exists")
        else:
            print("❌ MarketMonitor.get_sentiment method missing")
    except ImportError as e:
        print(f"❌ MarketMonitor import failed: {e}")
    
    try:
        # Test 4: FirestoreClient with updated fetch_trades method
        from runner.firestore_client import FirestoreClient
        client = FirestoreClient()
        # Check method signature
        import inspect
        sig = inspect.signature(client.fetch_trades)
        params = list(sig.parameters.keys())
        if 'date' in params:
            print("✅ FirestoreClient.fetch_trades supports 'date' parameter")
        else:
            print("❌ FirestoreClient.fetch_trades missing 'date' parameter support")
    except ImportError as e:
        print(f"❌ FirestoreClient import failed: {e}")
    
    print("Import testing complete!")


if __name__ == "__main__":
    test_imports()