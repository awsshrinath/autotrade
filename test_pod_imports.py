#!/usr/bin/env python3
"""
Test script to verify all critical imports work correctly
This simulates the pod environment import patterns
"""

import sys
import os
import traceback

# Add paths like the entrypoint does
sys.path.insert(0, '/app' if os.path.exists('/app') else '.')

def test_import(module_name, import_statement, critical=True):
    """Test a specific import and return result"""
    try:
        exec(import_statement)
        print(f"✓ {module_name}: SUCCESS")
        return True
    except Exception as e:
        status = "CRITICAL FAILURE" if critical else "WARNING"
        print(f"✗ {module_name}: {status} - {e}")
        if critical:
            print(f"  Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all import tests"""
    print("🧪 Testing Pod Import Compatibility")
    print("=" * 50)
    
    all_critical_passed = True
    
    # Test 1: Basic Python modules
    print("\n📦 Basic Python Modules:")
    basic_tests = [
        ("datetime", "import datetime"),
        ("time", "import time"),
        ("logging", "import logging"),
        ("os", "import os"),
        ("sys", "import sys")
    ]
    
    for module, statement in basic_tests:
        if not test_import(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 2: Enhanced logging system  
    print("\n📊 Enhanced Logging System:")
    enhanced_logging_tests = [
        ("enhanced_logging types", "from runner.enhanced_logging.log_types import LogLevel, LogCategory, LogType"),
        ("enhanced_logger", "from runner.enhanced_logger import create_enhanced_logger, LogLevel, LogCategory"),
        ("logger creation", "from runner.enhanced_logger import create_enhanced_logger; logger = create_enhanced_logger('test')"),
    ]
    
    for module, statement in enhanced_logging_tests:
        if not test_import(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 3: Core runner modules
    print("\n🏃 Core Runner Modules:")
    runner_tests = [
        ("firestore_client", "from runner.firestore_client import FirestoreClient"),
        ("logger", "from runner.logger import Logger"),
        ("openai_manager", "from runner.openai_manager import OpenAIManager"),
        ("kiteconnect_manager", "from runner.kiteconnect_manager import KiteConnectManager"),
        ("trade_manager", "from runner.trade_manager import TradeManager"),
        ("cognitive_system", "from runner.cognitive_system import CognitiveSystem"),
        ("cognitive_state_machine", "from runner.cognitive_state_machine import CognitiveState, StateTransitionTrigger"),
        ("thought_journal", "from runner.thought_journal import DecisionType, ConfidenceLevel"),
    ]
    
    for module, statement in runner_tests:
        if not test_import(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 4: RAG imports (non-critical, should fallback gracefully)
    print("\n🧠 RAG System (Fallback Expected):")
    rag_tests = [
        ("gpt_runner package", "import gpt_runner"),
        ("rag retriever", "from gpt_runner.rag.retriever import retrieve_similar_context"),
        ("rag faiss adapter", "from gpt_runner.rag.faiss_firestore_adapter import sync_firestore_to_faiss"),
        ("rag worker", "from gpt_runner.rag.rag_worker import embed_logs_for_today")
    ]
    
    for module, statement in rag_tests:
        test_import(module, statement, critical=False)
    
    # Test 5: Dashboard specific imports  
    print("\n🎛️ Dashboard Specific:")
    dashboard_tests = [
        ("stock_runner", "from stock_trading.stock_runner import main as stock_main"),
    ]
    
    for module, statement in dashboard_tests:
        test_import(module, statement, critical=False)
    
    # Test 6: Main runner imports
    print("\n🎯 Main Runner:")
    main_tests = [
        ("main_runner_combined", "from runner.main_runner_combined import main"),
        ("gpt_self_improvement", "from runner.gpt_self_improvement_monitor import run_gpt_reflection"),
    ]
    
    for module, statement in main_tests:
        if not test_import(module, statement, critical=True):
            all_critical_passed = False
    
    # Summary
    print("\n" + "=" * 50)
    if all_critical_passed:
        print("🎉 ALL CRITICAL IMPORTS PASSED!")
        print("✅ Pod should start successfully")
        return 0
    else:
        print("❌ CRITICAL IMPORT FAILURES DETECTED!")  
        print("🚨 Pod may fail to start")
        return 1

if __name__ == "__main__":
    exit(main()) 