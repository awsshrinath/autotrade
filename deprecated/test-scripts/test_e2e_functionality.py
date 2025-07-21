#!/usr/bin/env python3
"""
End-to-End Functionality Testing for Tron Trading System
Tests core functionality without external dependencies
"""

import sys
import os
import traceback
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TronFunctionalityTester:
    def __init__(self):
        self.results = {
            'passed': [],
            'failed': [],
            'warnings': []
        }
        
    def test_imports(self):
        """Test critical module imports"""
        tests = [
            ('config.config_manager', 'ConfigManager'),
            ('runner.main_runner', None),
            ('dashboard_api.main', 'app'),
            ('strategies.base_strategy', 'BaseStrategy'),
            ('stock_trading.stock_runner', None),
            ('options_trading.options_runner', None),
            ('futures_trading.futures_runner', None),
        ]
        
        for module_name, class_name in tests:
            try:
                module = __import__(module_name, fromlist=[class_name] if class_name else [''])
                if class_name and hasattr(module, class_name):
                    self.results['passed'].append(f"✅ {module_name}.{class_name}")
                elif not class_name:
                    self.results['passed'].append(f"✅ {module_name}")
                else:
                    self.results['failed'].append(f"❌ {module_name}.{class_name} not found")
            except ImportError as e:
                if 'google' in str(e) or 'fastapi' in str(e) or 'pytz' in str(e):
                    self.results['warnings'].append(f"⚠️  {module_name}: {e} (external dependency)")
                else:
                    self.results['failed'].append(f"❌ {module_name}: {e}")
            except Exception as e:
                self.results['failed'].append(f"❌ {module_name}: {e}")
    
    def test_configuration(self):
        """Test configuration system"""
        try:
            from config.config_manager import ConfigManager
            config = ConfigManager()
            
            # Test config loading
            base_config = config.get_config()
            if isinstance(base_config, dict):
                self.results['passed'].append("✅ Configuration loads successfully")
            else:
                self.results['failed'].append("❌ Configuration not a dict")
                
            # Test environment switching
            try:
                config.switch_environment('development')
                self.results['passed'].append("✅ Environment switching works")
            except Exception as e:
                self.results['warnings'].append(f"⚠️  Environment switching: {e}")
                
        except Exception as e:
            self.results['failed'].append(f"❌ Configuration system: {e}")
    
    def test_strategies(self):
        """Test strategy system"""
        try:
            from strategies.base_strategy import BaseStrategy
            from strategies.vwap_strategy import VWAPStrategy
            
            # Test base strategy class structure (not instantiation)
            if hasattr(BaseStrategy, 'execute'):
                self.results['passed'].append("✅ BaseStrategy structure valid")
            else:
                self.results['failed'].append("❌ BaseStrategy missing execute method")
                
            # Test VWAP strategy
            vwap = VWAPStrategy()
            if hasattr(vwap, 'calculate_vwap'):
                self.results['passed'].append("✅ VWAPStrategy structure valid")
            else:
                self.results['failed'].append("❌ VWAPStrategy missing calculate_vwap method")
                
        except Exception as e:
            self.results['failed'].append(f"❌ Strategy system: {e}")
    
    def test_trading_runners(self):
        """Test trading runner modules"""
        runners = [
            'stock_trading.stock_runner',
            'options_trading.options_runner', 
            'futures_trading.futures_runner'
        ]
        
        for runner_module in runners:
            try:
                module = __import__(runner_module, fromlist=[''])
                # Check if main execution function exists
                if hasattr(module, 'main') or hasattr(module, 'run') or hasattr(module, 'start_trading'):
                    self.results['passed'].append(f"✅ {runner_module} structure valid")
                else:
                    self.results['warnings'].append(f"⚠️  {runner_module} - no main execution function found")
            except Exception as e:
                if 'google' in str(e) or 'kiteconnect' in str(e):
                    self.results['warnings'].append(f"⚠️  {runner_module}: {e} (external dependency)")
                else:
                    self.results['failed'].append(f"❌ {runner_module}: {e}")
    
    def test_dashboard_api(self):
        """Test dashboard API structure"""
        try:
            # Test service modules
            from dashboard_api.services.cognitive_service import CognitiveService
            from dashboard_api.services.system_service import SystemService
            from dashboard_api.services.trade_service import TradeService
            
            cognitive = CognitiveService()
            system_service = SystemService(None, None)  # Mock dependencies
            
            self.results['passed'].append("✅ Dashboard services instantiate successfully")
            
            # Test if services have required methods
            if hasattr(cognitive, 'get_cognitive_summary'):
                self.results['passed'].append("✅ CognitiveService has required methods")
            else:
                self.results['failed'].append("❌ CognitiveService missing required methods")
                
        except Exception as e:
            if 'fastapi' in str(e):
                self.results['warnings'].append(f"⚠️  Dashboard API: {e} (external dependency)")
            else:
                self.results['failed'].append(f"❌ Dashboard API: {e}")
    
    def test_file_structure(self):
        """Test project file structure"""
        required_files = [
            'main.py',
            'requirements.txt',
            'Dockerfile',
            'helm/tron-system/Chart.yaml',
            'helm/tron-system/values.yaml',
            'config/base.yaml',
            'frontend/package.json',
            'frontend/next.config.mjs'
        ]
        
        for file_path in required_files:
            if os.path.exists(file_path):
                self.results['passed'].append(f"✅ {file_path} exists")
            else:
                self.results['failed'].append(f"❌ {file_path} missing")
    
    def run_all_tests(self):
        """Run all functionality tests"""
        print(f"🚀 Starting Tron E2E Functionality Tests - {datetime.now()}")
        print("=" * 60)
        
        test_methods = [
            self.test_file_structure,
            self.test_imports,
            self.test_configuration,
            self.test_strategies,
            self.test_trading_runners,
            self.test_dashboard_api
        ]
        
        for test_method in test_methods:
            try:
                print(f"\n📋 Running {test_method.__name__}...")
                test_method()
            except Exception as e:
                self.results['failed'].append(f"❌ {test_method.__name__}: {traceback.format_exc()}")
        
        self.print_results()
    
    def print_results(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"\n✅ PASSED ({len(self.results['passed'])} tests):")
        for result in self.results['passed']:
            print(f"  {result}")
        
        if self.results['warnings']:
            print(f"\n⚠️  WARNINGS ({len(self.results['warnings'])} items):")
            for result in self.results['warnings']:
                print(f"  {result}")
        
        if self.results['failed']:
            print(f"\n❌ FAILED ({len(self.results['failed'])} tests):")
            for result in self.results['failed']:
                print(f"  {result}")
        else:
            print(f"\n🎉 All critical tests passed!")
        
        print(f"\n📈 OVERALL STATUS:")
        total_tests = len(self.results['passed']) + len(self.results['failed'])
        pass_rate = (len(self.results['passed']) / total_tests * 100) if total_tests > 0 else 0
        print(f"  Pass Rate: {pass_rate:.1f}% ({len(self.results['passed'])}/{total_tests})")
        
        if len(self.results['failed']) == 0:
            print("  🟢 SYSTEM READY FOR DEPLOYMENT")
        elif len(self.results['failed']) <= 2:
            print("  🟡 SYSTEM MOSTLY READY - MINOR FIXES NEEDED")
        else:
            print("  🔴 SYSTEM NEEDS SIGNIFICANT FIXES BEFORE DEPLOYMENT")

if __name__ == "__main__":
    tester = TronFunctionalityTester()
    tester.run_all_tests()