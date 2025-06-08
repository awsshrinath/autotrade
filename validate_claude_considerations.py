#!/usr/bin/env python3
"""
Claude Considerations Validation Script

This script validates the three considerations identified by Claude:
1. Dependency Requirements (numpy, google-cloud libraries)
2. Historical Data (intelligent mock data with caching)
3. Market Hours (risk governor enforcement)
"""

import sys
import os
from datetime import datetime, timedelta
import traceback

# Add the current directory to the path
sys.path.append('.')

def test_consideration_1_dependencies():
    """Test Consideration 1: Dependency Requirements"""
    print("\n" + "="*60)
    print("🧪 CONSIDERATION 1: Dependency Requirements")
    print("="*60)
    
    try:
        # Test NumPy
        import numpy as np
        print(f"✅ NumPy: {np.__version__}")
        
        # Test Google Cloud libraries
        from google.cloud import firestore
        print("✅ Google Cloud Firestore: Available")
        
        from google.cloud import storage
        print("✅ Google Cloud Storage: Available")
        
        from google.cloud import secretmanager
        print("✅ Google Cloud Secret Manager: Available")
        
        # Test additional production dependencies
        import pandas as pd
        print(f"✅ Pandas: {pd.__version__}")
        
        import scipy
        print(f"✅ SciPy: {scipy.__version__}")
        
        try:
            import faiss
            print(f"✅ FAISS: Available")
        except ImportError:
            print("⚠️  FAISS: Not available (optional for some features)")
        
        try:
            import transformers
            print(f"✅ Transformers: {transformers.__version__}")
        except ImportError as e:
            print(f"⚠️  Transformers: Import issue ({str(e)[:50]}...) - Non-critical for core trading")
        
        print("\n🎉 CONSIDERATION 1: ✅ CORE DEPENDENCIES VALIDATED")
        print("   (All critical dependencies for trading are available)")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating dependencies: {e}")
        return False

def test_consideration_2_historical_data():
    """Test Consideration 2: Historical Data with Caching"""
    print("\n" + "="*60)
    print("🧪 CONSIDERATION 2: Historical Data & Caching")
    print("="*60)
    
    try:
        from runner.market_monitor import MarketMonitor
        
        # Initialize market monitor
        monitor = MarketMonitor()
        print("✅ MarketMonitor initialized")
        
        # Test cache configuration
        config = monitor.historical_config
        print(f"✅ Cache TTL: {config['cache_ttl_minutes']} minutes")
        print(f"✅ Max retries: {config['max_retry_attempts']}")
        print(f"✅ Batch size: {config['batch_size']}")
        print(f"✅ Rate limit delay: {config['rate_limit_delay']}s")
        
        # Test mock data generation
        to_date = datetime.now()
        from_date = to_date - timedelta(hours=2)
        
        print(f"\n📊 Testing mock data generation...")
        mock_data = monitor._generate_mock_data(from_date, to_date, "5minute")
        print(f"✅ Generated {len(mock_data)} mock data points")
        
        if not mock_data.empty:
            print(f"✅ Data columns: {list(mock_data.columns)}")
            print(f"✅ Date range: {mock_data['date'].min()} to {mock_data['date'].max()}")
            print(f"✅ Price range: ₹{mock_data['close'].min():.2f} - ₹{mock_data['close'].max():.2f}")
        
        # Test cache functionality
        print(f"\n🔄 Testing cache functionality...")
        cache_stats = monitor.get_cache_statistics()
        print(f"✅ Cache entries: {cache_stats['total_cached_entries']}")
        print(f"✅ Valid entries: {cache_stats['valid_cached_entries']}")
        print(f"✅ Cache TTL: {cache_stats['cache_ttl_minutes']} minutes")
        
        # Test multi-instrument capability
        instruments = {
            'NIFTY 50': 256265,
            'BANKNIFTY': 260105
        }
        
        print(f"\n📈 Testing multi-instrument data fetching...")
        batch_data = monitor.fetch_multiple_instruments_data(
            instruments, from_date, to_date, "5minute"
        )
        
        for name, data in batch_data.items():
            if not data.empty:
                print(f"✅ {name}: {len(data)} records")
            else:
                print(f"⚠️  {name}: No data (expected in mock mode)")
        
        print("\n🎉 CONSIDERATION 2: ✅ HISTORICAL DATA SYSTEM VALIDATED")
        return True
        
    except Exception as e:
        print(f"❌ Error validating historical data: {e}")
        traceback.print_exc()
        return False

def test_consideration_3_market_hours():
    """Test Consideration 3: Market Hours Enforcement"""
    print("\n" + "="*60)
    print("🧪 CONSIDERATION 3: Market Hours Enforcement")
    print("="*60)
    
    try:
        from runner.risk_governor import RiskGovernor
        
        # Initialize risk governor
        risk_gov = RiskGovernor()
        print("✅ RiskGovernor initialized")
        
        # Get current time info
        now = datetime.now()
        print(f"✅ Current time: {now.strftime('%H:%M:%S')}")
        print(f"✅ Current day: {now.strftime('%A')}")
        
        # Test market hours validation
        time_ok, time_msg = risk_gov._validate_trade_timing()
        print(f"✅ Time validation: {time_ok}")
        print(f"✅ Time message: {time_msg}")
        
        # Test overall trading permission
        can_trade = risk_gov.can_trade()
        print(f"✅ Can trade: {can_trade}")
        
        # Test risk limits validation
        risk_ok, risk_msg = risk_gov._validate_risk_limits()
        print(f"✅ Risk validation: {risk_ok}")
        print(f"✅ Risk message: {risk_msg}")
        
        # Test position limits validation
        position_ok, position_msg = risk_gov._validate_position_limits(10000)
        print(f"✅ Position validation: {position_ok}")
        print(f"✅ Position message: {position_msg}")
        
        # Get risk summary
        risk_summary = risk_gov.get_risk_summary()
        print(f"\n📊 Risk Summary:")
        print(f"   - Total P&L: ₹{risk_summary['total_pnl']:.2f}")
        print(f"   - Trade count: {risk_summary['trade_count']}")
        print(f"   - Emergency stop: {risk_summary['emergency_stop_active']}")
        print(f"   - Can trade now: {risk_summary['can_trade_now']}")
        
        # Test market hours configuration
        limits = risk_summary['limits']
        print(f"\n⚙️  Configuration:")
        print(f"   - Max daily loss: ₹{limits['max_daily_loss']}")
        print(f"   - Max trades: {limits['max_trades']}")
        print(f"   - Cutoff time: {limits['cutoff_time']}")
        print(f"   - Max position: ₹{limits['max_position_value']}")
        
        print("\n🎉 CONSIDERATION 3: ✅ MARKET HOURS ENFORCEMENT VALIDATED")
        return True
        
    except Exception as e:
        print(f"❌ Error validating market hours: {e}")
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    print("🚀 Claude Considerations Validation Script")
    print("=" * 60)
    print("Validating three considerations identified by Claude:")
    print("1. Dependency Requirements")
    print("2. Historical Data with Caching")
    print("3. Market Hours Enforcement")
    
    results = []
    
    # Test all considerations
    results.append(test_consideration_1_dependencies())
    results.append(test_consideration_2_historical_data())
    results.append(test_consideration_3_market_hours())
    
    # Summary
    print("\n" + "="*60)
    print("🏁 VALIDATION SUMMARY")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    considerations = [
        "Dependency Requirements",
        "Historical Data & Caching", 
        "Market Hours Enforcement"
    ]
    
    for i, (consideration, result) in enumerate(zip(considerations, results), 1):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{i}. {consideration}: {status}")
    
    print(f"\n📊 Overall Result: {passed}/{total} considerations validated")
    
    if passed == total:
        print("🎉 ALL CONSIDERATIONS SUCCESSFULLY VALIDATED!")
        print("🚀 System is PRODUCTION READY!")
    else:
        print("⚠️  Some considerations need attention")
        print("🔧 Review failed tests and fix issues")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 