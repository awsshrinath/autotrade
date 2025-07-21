#!/usr/bin/env python3
"""
Test script to verify dashboard connections are working
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_connections():
    """Test all dashboard connections"""
    print("🔍 Testing Dashboard Connections...")
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from dashboard.data.cognitive_data_provider import CognitiveDataProvider
        from dashboard.data.system_data_provider import SystemDataProvider
        from dashboard.components.cognitive_insights import CognitiveInsightsPage
        from dashboard.components.system_health import SystemHealthPage
        from dashboard.components.live_trades import LiveTradesPage
        print("✅ All imports successful!")
        
        # Test data providers
        print("🔧 Testing data providers...")
        system_data = SystemDataProvider()
        cognitive_data = CognitiveDataProvider()
        print("✅ Data providers initialized!")
        
        # Test basic functionality
        print("⚙️ Testing basic functionality...")
        health = system_data.get_system_health()
        summary = cognitive_data.get_cognitive_summary()
        print("✅ Basic functionality working!")
        
        # Display status
        print(f"\n📊 Status Report:")
        print(f"  System status: {health.get('status', 'unknown')}")
        print(f"  Cognitive available: {bool(cognitive_data.cognitive_system)}")
        
        if cognitive_data.cognitive_system:
            print(f"  Cognitive initialized: {summary.get('system_status', {}).get('initialized', False)}")
        else:
            print("  Cognitive system: Using fallback mode")
        
        # Test component initialization
        print("\n🧩 Testing component initialization...")
        cognitive_page = CognitiveInsightsPage(cognitive_data)
        health_page = SystemHealthPage(system_data)
        trades_page = LiveTradesPage(system_data)
        print("✅ All components initialized successfully!")
        
        print("\n🎉 All tests passed! Dashboard is ready to run.")
        assert True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        assert False

if __name__ == "__main__":
    success = test_connections()
    sys.exit(0 if success else 1) 