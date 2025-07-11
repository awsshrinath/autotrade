import requests

try:
    response = requests.get("http://localhost:8001/api/v1/analytics/pnl/daily", timeout=3)
    print(f"✅ SUCCESS! Status: {response.status_code}")
    print(f"Response: {response.text[:200]}...")
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server")
except requests.exceptions.Timeout:
    print("❌ Request timed out")
except Exception as e:
    print(f"❌ Error: {e}") 