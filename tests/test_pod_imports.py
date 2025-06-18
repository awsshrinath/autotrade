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

def test_import_function(module_name, import_statement, critical=True):
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
        if not test_import_function(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 2: Enhanced logging system  
    print("\n📊 Enhanced Logging System:")
    enhanced_logging_tests = [
        ("enhanced_logging types", "from runner.enhanced_logging.log_types import LogLevel, LogCategory, LogType"),
        ("enhanced_logger", "from runner.logger import create_enhanced_logger, LogLevel, LogCategory"),
        ("logger creation", "from runner.logger import create_enhanced_logger; logger = create_enhanced_logger('test')"),
    ]
    
    for module, statement in enhanced_logging_tests:
        if not test_import_function(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 3: Core runner modules
    print("\n🏃 Core Runner Modules:")
    runner_tests = [
        ("firestore_client", "from runner.firestore_client import FirestoreClient"),
        ("logger", "from runner.logger import Logger"),
        ("logger creation", "from runner.logger import create_enhanced_logger; logger = create_enhanced_logger('test')"),
        ("kiteconnect_manager", "from runner.kiteconnect_manager import KiteConnectManager"),
        ("market_data_fetcher", "from runner.market_data_fetcher import MarketDataFetcher"),
        ("market_monitor", "from runner.market_monitor import MarketMonitor"),
        ("openai_manager", "from runner.openai_manager import OpenAIManager"),
        ("paper_trader", "from runner.paper_trader import PaperTrader"),
        ("position_monitor", "from runner.position_monitor import PositionMonitor"),
        ("risk_governor", "from runner.risk_governor import RiskGovernor"),
        ("secret_manager", "from runner.secret_manager import EnhancedSecretManager"),
        ("strategy_factory", "from runner.strategy_factory import StrategyFactory"),
        ("strategy_selector", "from runner.strategy_selector import StrategySelector"),
        ("trade_manager", "from runner.trade_manager import EnhancedTradeManager"),
        ("common_utils", "from runner.common_utils import create_daily_folders"),
        ("daily_report_generator", "from runner.daily_report_generator import DailyReportGenerator"),
        ("gpt_codefix_suggestor", "from runner.gpt_codefix_suggestor import suggest_code_fix"),
        ("gpt_runner", "from runner.gpt_runner import gpt_runner"),
        ("gpt_self_improvement_monitor", "from runner.gpt_self_improvement_monitor import run_gpt_reflection"),
    ]
    
    for module, statement in runner_tests:
        if not test_import_function(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 4: RAG imports (non-critical, should fallback gracefully)
    print("\n🧠 RAG System (Fallback Expected):")
    rag_tests = [
        ("rag_worker", "from gpt_runner.rag.rag_worker import embed_logs_for_today"),
    ]
    
    for module, statement in rag_tests:
        test_import_function(module, statement, critical=False)
    
    # Test 5: Dashboard specific imports  
    print("\n🎛️ Dashboard Specific:")
    dashboard_tests = [
        ("stock_runner", "from stock_trading.stock_runner import main as stock_main"),
        ("options_runner", "from options_trading.options_runner import main as options_main"),
        ("futures_runner", "from futures_trading.futures_runner import main as futures_main"),
    ]
    
    for module, statement in dashboard_tests:
        test_import_function(module, statement, critical=False)
    
    # Test 6: Configuration system
    print("\n⚙️ Configuration System:")
    config_tests = [
        ("config package", "import config"),
        ("config_manager", "from config.config_manager import get_trading_config"),
        ("runner config", "from runner.config import PAPER_TRADE"),
        ("portfolio manager", "from runner.capital.portfolio_manager import PortfolioManager"),
    ]
    
    for module, statement in config_tests:
        if not test_import_function(module, statement, critical=True):
            all_critical_passed = False
    
    # Test 7: Main runner imports
    print("\n🎯 Main Runner:")
    main_tests = [
        ("main_runner", "from runner.main_runner import main"),
        ("stock_runner", "from stock_trading.stock_runner import main as stock_main"),
        ("options_runner", "from options_trading.options_runner import main as options_main"),
        ("futures_runner", "from futures_trading.futures_runner import main as futures_main"),
    ]
    
    for module, statement in main_tests:
        if not test_import_function(module, statement, critical=True):
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

def test_import():
    """Pytest test function for imports"""
    result = main()
    assert result == 0, "Critical import failures detected"

if __name__ == "__main__":
    exit(main()) 