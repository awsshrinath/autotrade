#!/usr/bin/env python3
"""
Simple API tester to check if our dashboard endpoints are working
"""
import requests
import json
import sys
from datetime import datetime

# Test endpoints
endpoints = [
    "/api/v1/analytics/pnl/daily",
    "/api/v1/analytics/metrics",
    "/api/v1/risk/metrics", 
    "/api/v1/strategy/all",
    "/api/v1/system/health/services",
    "/api/v1/trade/positions/live",
    "/api/v1/cognitive/summary",
    "/api/v1/logs/sources"
]

base_url = "http://localhost:8001"

def test_endpoint(endpoint):
    """Test a single endpoint"""
    try:
        print(f"Testing {endpoint}...")
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Response: {json.dumps(data, indent=2)[:200]}...")
            return True
        else:
            print(f"  Error: {response.text[:100]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ERROR: Cannot connect to server at {base_url}")
        return False
    except requests.exceptions.Timeout:
        print(f"  ERROR: Request timed out")
        return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def main():
    """Test all endpoints"""
    print(f"Testing Dashboard API at {base_url}")
    print(f"Time: {datetime.now()}")
    print("=" * 50)
    
    total_tests = len(endpoints)
    passed_tests = 0
    
    for endpoint in endpoints:
        if test_endpoint(endpoint):
            passed_tests += 1
        print()
    
    print("=" * 50)
    print(f"Results: {passed_tests}/{total_tests} endpoints working")
    
    if passed_tests == 0:
        print("\n❌ Server appears to be down or not responding")
        return 1
    elif passed_tests == total_tests:
        print("\n✅ All endpoints working!")
        return 0
    else:
        print(f"\n⚠️  {total_tests - passed_tests} endpoints have issues")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 