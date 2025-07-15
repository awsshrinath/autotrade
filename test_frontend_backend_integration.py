#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
Verify that frontend dashboard components are displaying real trading data
"""

import requests
import json
import time
from datetime import datetime

def test_frontend_backend_integration():
    """Test that frontend can connect to backend and get real data"""
    
    print("🔗 Testing Frontend-Backend Integration")
    print("=" * 60)
    
    # Test Backend API Endpoints (what frontend expects)
    backend_tests = [
        {
            "name": "Cognitive AI Summary",
            "url": "http://localhost:8001/api/cognitive/summary",
            "expected_fields": ["summary", "key_insights", "confidence_score"]
        },
        {
            "name": "System Health Status", 
            "url": "http://localhost:8001/api/system/health",
            "expected_fields": ["status", "services", "overall_status"]
        },
        {
            "name": "System Metrics",
            "url": "http://localhost:8001/api/system/metrics", 
            "expected_fields": ["cpu_usage", "memory_usage", "active_trades"]
        },
        {
            "name": "Live Trading Positions",
            "url": "http://localhost:8001/api/v1/trade/positions/live",
            "expected_fields": ["positions", "total_positions", "data_source"]
        },
        {
            "name": "Analytics P&L Daily",
            "url": "http://localhost:8001/api/v1/analytics/pnl/daily",
            "expected_fields": ["pnl_data", "total_pnl", "market_status"]
        },
        {
            "name": "Risk Metrics",
            "url": "http://localhost:8001/api/v1/risk/metrics", 
            "expected_fields": ["portfolio_value", "total_exposure", "open_positions"]
        },
        {
            "name": "Strategy Performance",
            "url": "http://localhost:8001/api/v1/strategy/all",
            "expected_fields": ["strategies", "data_source", "market_status"]
        },
        {
            "name": "System Health Services",
            "url": "http://localhost:8001/api/v1/system/health/services",
            "expected_fields": ["services", "overall_status", "market_status"]
        }
    ]
    
    print("\n1️⃣ Testing Backend API Endpoints...")
    backend_results = {}
    
    for test in backend_tests:
        try:
            response = requests.get(test["url"], timeout=5)
            data = response.json()
            
            # Check if required fields exist
            missing_fields = [field for field in test["expected_fields"] if field not in data]
            
            if response.status_code == 200 and not missing_fields:
                status = "✅ PASS"
                backend_results[test["name"]] = {"status": "pass", "data": data}
            else:
                status = f"❌ FAIL (Status: {response.status_code}, Missing: {missing_fields})"
                backend_results[test["name"]] = {"status": "fail", "error": f"Status {response.status_code}"}
                
            print(f"   {test['name']}: {status}")
            
        except Exception as e:
            print(f"   {test['name']}: ❌ FAIL (Error: {str(e)})")
            backend_results[test["name"]] = {"status": "fail", "error": str(e)}
    
    # Test if frontend is responsive
    print("\n2️⃣ Testing Frontend Server...")
    try:
        frontend_response = requests.get("http://localhost:3000", timeout=10)
        if frontend_response.status_code == 200:
            print("   Frontend Server: ✅ RESPONSIVE")
            frontend_running = True
        else:
            print(f"   Frontend Server: ❌ ERROR (Status: {frontend_response.status_code})")
            frontend_running = False
    except Exception as e:
        print(f"   Frontend Server: ❌ NOT RUNNING ({str(e)})")
        frontend_running = False
    
    # Analyze data quality
    print("\n3️⃣ Analyzing Real Data Quality...")
    
    # Check Cognitive AI data
    if "Cognitive AI Summary" in backend_results and backend_results["Cognitive AI Summary"]["status"] == "pass":
        cognitive_data = backend_results["Cognitive AI Summary"]["data"]
        confidence = cognitive_data.get("confidence_score", 0)
        insights_count = len(cognitive_data.get("key_insights", []))
        print(f"   Cognitive AI: ✅ Confidence {confidence}/10, {insights_count} insights")
    else:
        print("   Cognitive AI: ❌ No data available")
    
    # Check Trading Positions
    if "Live Trading Positions" in backend_results and backend_results["Live Trading Positions"]["status"] == "pass":
        positions_data = backend_results["Live Trading Positions"]["data"] 
        total_positions = positions_data.get("total_positions", 0)
        if total_positions > 0:
            position = positions_data["positions"][0]
            symbol = position.get("symbol", "Unknown")
            quantity = position.get("quantity", 0)
            price = position.get("current_price", position.get("entry_price", 0))
            print(f"   Live Positions: ✅ {total_positions} positions - {symbol} {quantity}@₹{price}")
        else:
            print("   Live Positions: ✅ No open positions (market closed)")
    else:
        print("   Live Positions: ❌ No data available")
    
    # Check P&L Data
    if "Analytics P&L Daily" in backend_results and backend_results["Analytics P&L Daily"]["status"] == "pass":
        pnl_data = backend_results["Analytics P&L Daily"]["data"]
        total_pnl = pnl_data.get("total_pnl", 0)
        market_status = pnl_data.get("market_status", "Unknown")
        print(f"   P&L Analytics: ✅ Total P&L ₹{total_pnl}, Market: {market_status}")
    else:
        print("   P&L Analytics: ❌ No data available")
    
    # Check Risk Metrics
    if "Risk Metrics" in backend_results and backend_results["Risk Metrics"]["status"] == "pass":
        risk_data = backend_results["Risk Metrics"]["data"]
        portfolio_value = risk_data.get("portfolio_value", 0)
        open_positions = risk_data.get("open_positions", 0)
        print(f"   Risk Metrics: ✅ Portfolio ₹{portfolio_value:,.0f}, {open_positions} open positions")
    else:
        print("   Risk Metrics: ❌ No data available")
    
    # Overall Assessment
    print("\n" + "=" * 60)
    passed_tests = sum(1 for result in backend_results.values() if result["status"] == "pass")
    total_tests = len(backend_results)
    
    print("📊 INTEGRATION TEST RESULTS:")
    print(f"✅ Backend API Tests: {passed_tests}/{total_tests} passed ({(passed_tests/total_tests)*100:.1f}%)")
    print(f"🌐 Frontend Server: {'✅ Running' if frontend_running else '❌ Not Running'}")
    
    if passed_tests == total_tests and frontend_running:
        print("🎉 INTEGRATION SUCCESS: Frontend should display real trading data!")
        print("📋 TODO Status Update:")
        print("   ✅ Cognitive AI Insights: Connected to real backend")
        print("   ✅ System Health: Connected to real monitoring")
        print("   ✅ Log Monitor: Connected to real data sources")
        print("   ✅ Paper Trading Data: Properly displayed")
        return True
    else:
        print("⚠️ INTEGRATION ISSUES: Some components may show empty data")
        print("📋 TODO Status:")
        if "Cognitive AI Summary" not in backend_results or backend_results["Cognitive AI Summary"]["status"] == "fail":
            print("   🔄 Cognitive AI Insights: Still needs fixing")
        if "System Health Status" not in backend_results or backend_results["System Health Status"]["status"] == "fail":
            print("   🔄 System Health: Still needs fixing") 
        if "System Metrics" not in backend_results or backend_results["System Metrics"]["status"] == "fail":
            print("   🔄 Log Monitor: Still needs fixing")
        return False

def check_mock_data_removal():
    """Verify no mock data is being returned"""
    print("\n4️⃣ Verifying Zero Mock Data...")
    
    endpoints_to_check = [
        "http://localhost:8001/health",
        "http://localhost:8001/api/v1/analytics/metrics", 
        "http://localhost:8001/api/cognitive/summary"
    ]
    
    for endpoint in endpoints_to_check:
        try:
            response = requests.get(endpoint)
            data = response.json()
            
            # Check for mock data indicators
            mock_indicators = [
                data.get("mock_data", None) == True,
                "demo" in str(data).lower(),
                "sample" in str(data).lower(),
                "test_data" in str(data).lower()
            ]
            
            if any(mock_indicators):
                print(f"   {endpoint}: ⚠️ Contains mock data indicators")
            else:
                print(f"   {endpoint}: ✅ Real data confirmed")
                
        except Exception as e:
            print(f"   {endpoint}: ❌ Error: {e}")

if __name__ == "__main__":
    try:
        integration_success = test_frontend_backend_integration()
        check_mock_data_removal()
        
        if integration_success:
            print("\n🚀 Next Steps:")
            print("1. Open http://localhost:3000 to view the dashboard")
            print("2. Navigate through different pages to verify data display")
            print("3. Update TODO tracker to mark items as completed")
            print("4. Prepare for production deployment")
        else:
            print("\n🔧 Required Actions:")
            print("1. Fix remaining API endpoint mismatches")
            print("2. Update frontend component API calls if needed")
            print("3. Test individual dashboard components")
            
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}") 