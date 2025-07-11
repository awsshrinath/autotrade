#!/usr/bin/env python3
"""
Comprehensive Automated Tests for Tron Dashboard API
Ensures all endpoints work correctly with real data connections
"""

import unittest
import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List

class TronDashboardAPITests(unittest.TestCase):
    """
    Automated test suite for Tron Trading Dashboard API
    Tests all endpoints for functionality, data integrity, and error handling
    """
    
    BASE_URL = "http://localhost:8001"
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        print(f"\n🧪 Starting Tron Dashboard API Test Suite")
        print(f"📡 Testing server at: {cls.BASE_URL}")
        print(f"⏰ Test started at: {datetime.now().isoformat()}")
        
        # Wait for server to be ready
        cls._wait_for_server()
    
    @classmethod
    def _wait_for_server(cls, max_attempts=10):
        """Wait for API server to be ready"""
        for attempt in range(max_attempts):
            try:
                response = requests.get(f"{cls.BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Server ready after {attempt + 1} attempts")
                    return
            except requests.exceptions.RequestException:
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    continue
                else:
                    raise Exception("❌ Server not responding after maximum attempts")
    
    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """Make API request with error handling"""
        url = f"{self.BASE_URL}{endpoint}"
        try:
            response = requests.get(url, timeout=10)
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "headers": dict(response.headers)
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "error": str(e),
                "data": {}
            }
    
    def _assert_successful_response(self, result: Dict[str, Any], endpoint: str):
        """Assert that API response is successful"""
        self.assertEqual(result["status_code"], 200, 
                        f"❌ {endpoint} failed with status {result.get('status_code', 'Unknown')}")
        self.assertIn("data", result, f"❌ {endpoint} missing response data")
        self.assertIsInstance(result["data"], dict, f"❌ {endpoint} data is not a dictionary")
    
    def _assert_real_data_source(self, data: Dict[str, Any], endpoint: str):
        """Assert that response contains real data source indicators"""
        # Check for real data source markers
        self.assertIn("data_source", data, f"❌ {endpoint} missing data_source field")
        self.assertIn("timestamp", data, f"❌ {endpoint} missing timestamp field")
        
        # Ensure it's not mock data
        data_source = data.get("data_source", "")
        self.assertNotIn("mock", data_source.lower(), f"❌ {endpoint} still using mock data")
        self.assertNotIn("demo", data_source.lower(), f"❌ {endpoint} still using demo data")

    def test_01_health_check(self):
        """Test API health endpoint"""
        print("\n🔍 Testing Health Check...")
        result = self._make_request("/health")
        
        self._assert_successful_response(result, "/health")
        
        data = result["data"]
        self.assertEqual(data["status"], "healthy", "❌ API not reporting healthy status")
        self.assertIn("data_sources", data, "❌ Health check missing data sources info")
        
        print("✅ Health check passed")

    def test_02_analytics_pnl_daily(self):
        """Test daily P&L analytics endpoint"""
        print("\n🔍 Testing Analytics P&L Daily...")
        result = self._make_request("/api/v1/analytics/pnl/daily")
        
        self._assert_successful_response(result, "/api/v1/analytics/pnl/daily")
        self._assert_real_data_source(result["data"], "/api/v1/analytics/pnl/daily")
        
        data = result["data"]
        self.assertIn("pnl_data", data, "❌ Missing pnl_data field")
        self.assertIn("total_pnl", data, "❌ Missing total_pnl field")
        self.assertIsInstance(data["pnl_data"], list, "❌ pnl_data is not a list")
        
        print("✅ Analytics P&L Daily passed")

    def test_03_analytics_metrics(self):
        """Test analytics metrics endpoint"""
        print("\n🔍 Testing Analytics Metrics...")
        result = self._make_request("/api/v1/analytics/metrics")
        
        self._assert_successful_response(result, "/api/v1/analytics/metrics")
        self._assert_real_data_source(result["data"], "/api/v1/analytics/metrics")
        
        data = result["data"]
        self.assertIn("metrics", data, "❌ Missing metrics field")
        
        metrics = data["metrics"]
        required_metrics = ["total_pnl", "total_trades", "win_rate", "avg_trade_pnl"]
        for metric in required_metrics:
            self.assertIn(metric, metrics, f"❌ Missing metric: {metric}")
        
        print("✅ Analytics Metrics passed")

    def test_04_risk_metrics(self):
        """Test risk metrics endpoint"""
        print("\n🔍 Testing Risk Metrics...")
        result = self._make_request("/api/v1/risk/metrics")
        
        self._assert_successful_response(result, "/api/v1/risk/metrics")
        self._assert_real_data_source(result["data"], "/api/v1/risk/metrics")
        
        data = result["data"]
        required_fields = ["portfolio_value", "total_exposure", "unrealized_pnl", "var_95"]
        for field in required_fields:
            self.assertIn(field, data, f"❌ Missing risk metric: {field}")
        
        print("✅ Risk Metrics passed")

    def test_05_risk_alerts(self):
        """Test risk alerts endpoint"""
        print("\n🔍 Testing Risk Alerts...")
        result = self._make_request("/api/v1/risk/alerts")
        
        self._assert_successful_response(result, "/api/v1/risk/alerts")
        self._assert_real_data_source(result["data"], "/api/v1/risk/alerts")
        
        data = result["data"]
        self.assertIn("alerts", data, "❌ Missing alerts field")
        self.assertIn("total_alerts", data, "❌ Missing total_alerts field")
        self.assertIsInstance(data["alerts"], list, "❌ alerts is not a list")
        
        print("✅ Risk Alerts passed")

    def test_06_strategy_all(self):
        """Test strategy performance endpoint"""
        print("\n🔍 Testing Strategy Performance...")
        result = self._make_request("/api/v1/strategy/all")
        
        self._assert_successful_response(result, "/api/v1/strategy/all")
        self._assert_real_data_source(result["data"], "/api/v1/strategy/all")
        
        data = result["data"]
        self.assertIn("strategies", data, "❌ Missing strategies field")
        self.assertIsInstance(data["strategies"], list, "❌ strategies is not a list")
        
        # Check strategy data structure
        if data["strategies"]:
            strategy = data["strategies"][0]
            required_fields = ["name", "status"]
            for field in required_fields:
                self.assertIn(field, strategy, f"❌ Strategy missing field: {field}")
        
        print("✅ Strategy Performance passed")

    def test_07_trade_positions_live(self):
        """Test live trading positions endpoint"""
        print("\n🔍 Testing Live Trading Positions...")
        result = self._make_request("/api/v1/trade/positions/live")
        
        self._assert_successful_response(result, "/api/v1/trade/positions/live")
        self._assert_real_data_source(result["data"], "/api/v1/trade/positions/live")
        
        data = result["data"]
        self.assertIn("positions", data, "❌ Missing positions field")
        self.assertIn("total_positions", data, "❌ Missing total_positions field")
        self.assertIsInstance(data["positions"], list, "❌ positions is not a list")
        
        print("✅ Live Trading Positions passed")

    def test_08_trade_recent(self):
        """Test recent trades endpoint"""
        print("\n🔍 Testing Recent Trades...")
        result = self._make_request("/api/v1/trade/recent")
        
        self._assert_successful_response(result, "/api/v1/trade/recent")
        self._assert_real_data_source(result["data"], "/api/v1/trade/recent")
        
        data = result["data"]
        self.assertIn("trades", data, "❌ Missing trades field")
        self.assertIn("total_trades", data, "❌ Missing total_trades field")
        self.assertIsInstance(data["trades"], list, "❌ trades is not a list")
        
        print("✅ Recent Trades passed")

    def test_09_system_health_services(self):
        """Test system health services endpoint"""
        print("\n🔍 Testing System Health Services...")
        result = self._make_request("/api/v1/system/health/services")
        
        self._assert_successful_response(result, "/api/v1/system/health/services")
        self._assert_real_data_source(result["data"], "/api/v1/system/health/services")
        
        data = result["data"]
        self.assertIn("services", data, "❌ Missing services field")
        self.assertIn("overall_status", data, "❌ Missing overall_status field")
        self.assertIsInstance(data["services"], list, "❌ services is not a list")
        
        # Check service data structure
        if data["services"]:
            service = data["services"][0]
            required_fields = ["name", "status", "uptime"]
            for field in required_fields:
                self.assertIn(field, service, f"❌ Service missing field: {field}")
        
        print("✅ System Health Services passed")

    def test_10_cognitive_summary(self):
        """Test cognitive AI insights endpoint"""
        print("\n🔍 Testing Cognitive AI Summary...")
        result = self._make_request("/api/v1/cognitive/summary")
        
        self._assert_successful_response(result, "/api/v1/cognitive/summary")
        self._assert_real_data_source(result["data"], "/api/v1/cognitive/summary")
        
        data = result["data"]
        self.assertIn("summary", data, "❌ Missing summary field")
        self.assertIn("key_insights", data, "❌ Missing key_insights field")
        self.assertIn("confidence_score", data, "❌ Missing confidence_score field")
        self.assertIsInstance(data["key_insights"], list, "❌ key_insights is not a list")
        
        print("✅ Cognitive AI Summary passed")

    def test_11_logs_sources(self):
        """Test log sources endpoint"""
        print("\n🔍 Testing Log Sources...")
        result = self._make_request("/api/v1/logs/sources")
        
        self._assert_successful_response(result, "/api/v1/logs/sources")
        self._assert_real_data_source(result["data"], "/api/v1/logs/sources")
        
        data = result["data"]
        self.assertIn("sources", data, "❌ Missing sources field")
        self.assertIsInstance(data["sources"], list, "❌ sources is not a list")
        
        # Check source data structure
        if data["sources"]:
            source = data["sources"][0]
            required_fields = ["name", "type", "status"]
            for field in required_fields:
                self.assertIn(field, source, f"❌ Source missing field: {field}")
        
        print("✅ Log Sources passed")

    def test_12_error_handling(self):
        """Test error handling for invalid endpoints"""
        print("\n🔍 Testing Error Handling...")
        
        # Test invalid endpoint
        result = self._make_request("/api/v1/invalid/endpoint")
        self.assertEqual(result["status_code"], 404, "❌ Invalid endpoint should return 404")
        
        print("✅ Error Handling passed")

    def test_13_response_times(self):
        """Test API response times"""
        print("\n🔍 Testing Response Times...")
        
        endpoints = [
            "/api/v1/analytics/pnl/daily",
            "/api/v1/analytics/metrics", 
            "/api/v1/risk/metrics",
            "/api/v1/strategy/all",
            "/api/v1/trade/positions/live"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            result = self._make_request(endpoint)
            response_time = time.time() - start_time
            
            self.assertEqual(result["status_code"], 200, f"❌ {endpoint} failed")
            self.assertLess(response_time, 5.0, f"❌ {endpoint} too slow: {response_time:.2f}s")
        
        print("✅ Response Times passed")

    def test_14_data_consistency(self):
        """Test data consistency across endpoints"""
        print("\n🔍 Testing Data Consistency...")
        
        # Get data from multiple endpoints
        analytics_result = self._make_request("/api/v1/analytics/metrics")
        strategy_result = self._make_request("/api/v1/strategy/all")
        
        self.assertEqual(analytics_result["status_code"], 200, "❌ Analytics endpoint failed")
        self.assertEqual(strategy_result["status_code"], 200, "❌ Strategy endpoint failed")
        
        # Verify data consistency
        analytics_data = analytics_result["data"]
        strategy_data = strategy_result["data"]
        
        # Both should have timestamp and data_source
        self.assertIn("timestamp", analytics_data, "❌ Analytics missing timestamp")
        self.assertIn("timestamp", strategy_data, "❌ Strategy missing timestamp")
        
        print("✅ Data Consistency passed")

    @classmethod
    def tearDownClass(cls):
        """Clean up after tests"""
        print(f"\n🏁 Test Suite Completed at: {datetime.now().isoformat()}")
        print("📊 All automated tests finished successfully!")

def run_tests():
    """Run the complete test suite"""
    print("🚀 Starting Tron Dashboard API Automated Test Suite")
    print("=" * 60)
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TronDashboardAPITests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        buffer=True,
        failfast=False
    )
    
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"✅ Tests run: {result.testsRun}")
    print(f"❌ Failures: {len(result.failures)}")
    print(f"⚠️ Errors: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("🎉 ALL TESTS PASSED! API is production ready!")
        return True
    else:
        print("❌ Some tests failed. Check output above.")
        return False

if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1) 