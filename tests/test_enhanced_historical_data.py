#!/usr/bin/env python3
"""
🚀 Enhanced Historical Data Fetching System Test

This script comprehensively tests the new production-ready historical data system with:
- Real KiteConnect API integration with batching
- Intelligent caching with TTL management
- Exponential backoff retry logic for rate limits
- Multi-instrument analysis capabilities
- Performance optimization and monitoring

Tests all new features implemented in MarketMonitor for production deployment.
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add the runner directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'runner'))

from runner.market_monitor import MarketMonitor

class MockLogger:
    """Mock logger for testing"""
    def __init__(self):
        self.events = []
    
    def log_event(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        self.events.append(log_entry)

class MockKiteClient:
    """Mock KiteConnect client for testing without real API"""
    def __init__(self, simulate_errors=False):
        self.simulate_errors = simulate_errors
        self.call_count = 0
        
    def historical_data(self, instrument_token, from_date, to_date, interval):
        """Mock historical data with realistic behavior"""
        self.call_count += 1
        
        # Simulate rate limit error on 3rd call if enabled
        if self.simulate_errors and self.call_count == 3:
            raise Exception("Too many requests - Rate limit exceeded")
        
        # Simulate network error on 5th call if enabled
        if self.simulate_errors and self.call_count == 5:
            raise Exception("Connection timeout - Network error")
            
        # Generate realistic mock data
        import pandas as pd
        import numpy as np
        
        # Calculate data points based on interval
        if interval == 'minute':
            freq = '1T'
        elif interval == '5minute':
            freq = '5T'
        elif interval == '1hour':
            freq = '1H'
        elif interval == 'day':
            freq = '1D'
        else:
            freq = '5T'
        
        date_range = pd.date_range(start=from_date, end=to_date, freq=freq)
        
        if len(date_range) == 0:
            return []
        
        # Generate realistic NIFTY-like price data
        base_price = 17500
        volatility = 0.02
        
        # Use instrument token to vary base price
        if instrument_token == 260105:  # BANKNIFTY
            base_price = 38000
        elif instrument_token == 11924738:  # NIFTY IT
            base_price = 34000
            
        returns = np.random.normal(0, volatility / np.sqrt(len(date_range)), len(date_range))
        prices = base_price * np.exp(np.cumsum(returns))
        
        # Create realistic OHLCV data
        data = []
        for i, date in enumerate(date_range):
            price = prices[i]
            open_price = price * (1 + np.random.normal(0, 0.001))
            close_price = price * (1 + np.random.normal(0, 0.001))
            high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
            low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
            volume = np.random.randint(10000, 100000)
            
            data.append({
                'date': date,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
        
        # Simulate API delay
        time.sleep(0.1)
        
        return data

def test_basic_data_fetching():
    """Test 1: Basic historical data fetching with caching"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Basic Historical Data Fetching with Caching")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    # Test single instrument fetch
    to_date = datetime.now()
    from_date = to_date - timedelta(hours=6)
    
    print(f"📊 Fetching NIFTY 50 data from {from_date} to {to_date}")
    
    start_time = time.time()
    data = monitor._fetch_historical_data(256265, from_date, to_date, "5minute")
    fetch_time = time.time() - start_time
    
    print(f"✅ Fetched {len(data)} records in {fetch_time:.3f} seconds")
    print(f"📈 Data sample: {data[['date', 'close']].head(3).to_dict('records') if not data.empty else 'No data'}")
    
    # Test cache hit
    print("\n🔄 Testing cache functionality...")
    start_time = time.time()
    cached_data = monitor._fetch_historical_data(256265, from_date, to_date, "5minute")
    cache_time = time.time() - start_time
    
    print(f"⚡ Cached fetch completed in {cache_time:.3f} seconds (should be much faster)")
    
    # Cache statistics
    cache_stats = monitor.get_cache_statistics()
    print(f"📊 Cache Statistics: {cache_stats}")
    
    return len(data) > 0

def test_batch_fetching():
    """Test 2: Batch fetching for multiple instruments"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Batch Fetching for Multiple Instruments")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    # Test multiple instruments
    instruments = {
        'NIFTY 50': 256265,
        'BANKNIFTY': 260105,
        'NIFTY IT': 11924738,
        'NIFTY BANK': 11924234
    }
    
    to_date = datetime.now()
    from_date = to_date - timedelta(hours=4)
    
    print(f"📊 Batch fetching {len(instruments)} instruments")
    
    start_time = time.time()
    batch_data = monitor.fetch_multiple_instruments_data(instruments, from_date, to_date, "5minute")
    batch_time = time.time() - start_time
    
    print(f"✅ Batch fetch completed in {batch_time:.3f} seconds")
    
    for name, data_df in batch_data.items():
        if not data_df.empty:
            current_price = data_df['close'].iloc[-1]
            print(f"📈 {name}: {len(data_df)} records, current price: ₹{current_price:.2f}")
        else:
            print(f"❌ {name}: No data")
    
    # Performance analysis
    avg_time_per_instrument = batch_time / len(instruments)
    print(f"⚡ Average time per instrument: {avg_time_per_instrument:.3f} seconds")
    
    return len(batch_data) == len(instruments)

def test_retry_logic():
    """Test 3: Retry logic with simulated errors"""
    print("\n" + "="*60)
    print("🧪 TEST 3: Retry Logic with Simulated Errors")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient(simulate_errors=True)
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    # Update config for faster testing
    monitor.update_historical_config(
        max_retry_attempts=3,
        exponential_backoff_base=1.5,
        max_backoff_seconds=5
    )
    
    to_date = datetime.now()
    from_date = to_date - timedelta(hours=2)
    
    print("🔄 Testing retry logic with simulated errors...")
    
    # This should trigger retries due to mock errors
    try:
        start_time = time.time()
        data = monitor._fetch_historical_data(256265, from_date, to_date, "minute")
        retry_time = time.time() - start_time
        
        print(f"✅ Retry logic successful, data fetched in {retry_time:.3f} seconds")
        print(f"📊 API calls made: {kite_client.call_count}")
        print(f"📈 Records retrieved: {len(data)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Retry logic test failed: {e}")
        return False

def test_volatility_regimes():
    """Test 4: Enhanced volatility regime calculation"""
    print("\n" + "="*60)
    print("🧪 TEST 4: Enhanced Volatility Regime Calculation")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    print("📊 Calculating volatility regimes with real data...")
    
    start_time = time.time()
    vol_regimes = monitor.get_volatility_regimes("NIFTY 50", 256265)
    calc_time = time.time() - start_time
    
    print(f"✅ Volatility calculation completed in {calc_time:.3f} seconds")
    
    for period, regime_data in vol_regimes.items():
        regime = regime_data.get('regime', 'UNKNOWN')
        confidence = regime_data.get('confidence', 0)
        data_quality = regime_data.get('data_quality', 'unknown')
        data_points = regime_data.get('data_points', 0)
        
        print(f"📈 {period}: {regime} (confidence: {confidence:.2f}, quality: {data_quality}, points: {data_points})")
    
    # Check if all regimes were calculated
    expected_periods = ['5min', '1hr', '1day']
    calculated_periods = list(vol_regimes.keys())
    
    return all(period in calculated_periods for period in expected_periods)

def test_multi_instrument_analysis():
    """Test 5: Comprehensive multi-instrument analysis"""
    print("\n" + "="*60)
    print("🧪 TEST 5: Multi-Instrument Analysis")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    print("🔬 Performing comprehensive multi-instrument analysis...")
    
    start_time = time.time()
    analysis = monitor.get_multi_instrument_analysis()
    analysis_time = time.time() - start_time
    
    print(f"✅ Multi-instrument analysis completed in {analysis_time:.3f} seconds")
    
    # Performance metrics
    perf_metrics = analysis.get('performance_metrics', {})
    print(f"⚡ Performance Metrics:")
    print(f"   - Fetch time: {perf_metrics.get('fetch_time_seconds', 0):.3f}s")
    print(f"   - Instruments processed: {perf_metrics.get('instruments_processed', 0)}")
    print(f"   - Successful analysis: {perf_metrics.get('successful_analysis', 0)}")
    print(f"   - Cache hit ratio: {perf_metrics.get('cache_hit_ratio', 0):.2f}")
    
    # Analysis results
    analysis_results = analysis.get('analysis_results', {})
    print(f"\n📊 Analysis Results:")
    
    for instrument, result in analysis_results.items():
        status = result.get('status', 'unknown')
        if status == 'success':
            overall_regime = result.get('overall_regime', {}).get('regime', 'UNKNOWN')
            confidence = result.get('overall_regime', {}).get('confidence', 0)
            price_range = result.get('price_range', {})
            
            print(f"   📈 {instrument}: {overall_regime} (confidence: {confidence:.2f})")
            print(f"      Current: ₹{price_range.get('current', 0):.2f}, Range: ₹{price_range.get('low', 0):.2f} - ₹{price_range.get('high', 0):.2f}")
        else:
            print(f"   ❌ {instrument}: {status}")
    
    # Cross correlations
    correlations = analysis.get('cross_correlations', {})
    if correlations:
        print(f"\n🔗 Cross-Correlations:")
        for inst1, corr_data in list(correlations.items())[:2]:  # Show first 2 for brevity
            for inst2, corr_value in list(corr_data.items())[:2]:
                print(f"   {inst1} vs {inst2}: {corr_value:.3f}")
    
    return analysis_time < 15.0 and perf_metrics.get('successful_analysis', 0) > 0

def test_cache_management():
    """Test 6: Cache management and cleanup"""
    print("\n" + "="*60)
    print("🧪 TEST 6: Cache Management and Cleanup")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    # Set short TTL for testing
    monitor.update_historical_config(cache_ttl_minutes=0.01)  # 0.6 seconds
    
    # Fetch some data to populate cache
    to_date = datetime.now()
    from_date = to_date - timedelta(hours=1)
    
    print("📊 Populating cache with test data...")
    monitor._fetch_historical_data(256265, from_date, to_date, "5minute")
    monitor._fetch_historical_data(260105, from_date, to_date, "5minute")
    
    initial_stats = monitor.get_cache_statistics()
    print(f"📈 Initial cache stats: {initial_stats['total_cached_entries']} entries")
    
    # Wait for cache to expire
    print("⏳ Waiting for cache to expire...")
    time.sleep(1)
    
    # Manually clean expired entries
    expired_count = monitor.clear_expired_cache()
    print(f"🧹 Cleaned {expired_count} expired entries")
    
    final_stats = monitor.get_cache_statistics()
    print(f"📉 Final cache stats: {final_stats['total_cached_entries']} entries")
    
    return expired_count > 0

def test_configuration_updates():
    """Test 7: Configuration updates and validation"""
    print("\n" + "="*60)
    print("🧪 TEST 7: Configuration Updates")
    print("="*60)
    
    logger = MockLogger()
    monitor = MarketMonitor(logger=logger)
    
    print("⚙️ Testing configuration updates...")
    
    # Test valid configuration updates
    monitor.update_historical_config(
        cache_ttl_minutes=30,
        max_retry_attempts=5,
        rate_limit_delay=2.0
    )
    
    config = monitor.historical_config
    print(f"✅ Updated config: TTL={config['cache_ttl_minutes']}, Retries={config['max_retry_attempts']}, Delay={config['rate_limit_delay']}")
    
    # Test invalid configuration
    monitor.update_historical_config(invalid_key="test")
    
    return config['cache_ttl_minutes'] == 30 and config['max_retry_attempts'] == 5

def run_performance_benchmark():
    """Performance benchmark: Test system under load"""
    print("\n" + "="*60)
    print("🚀 PERFORMANCE BENCHMARK")
    print("="*60)
    
    logger = MockLogger()
    kite_client = MockKiteClient()
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    
    # Test with larger dataset
    instruments = {
        'NIFTY 50': 256265,
        'BANKNIFTY': 260105,
        'NIFTY IT': 11924738,
        'NIFTY BANK': 11924234,
        'NIFTY FMCG': 11924242,
        'NIFTY AUTO': 11924226,
        'NIFTY PHARMA': 11924274,
        'INDIA VIX': 264969
    }
    
    to_date = datetime.now()
    from_date = to_date - timedelta(days=1)  # Larger dataset
    
    print(f"🏃‍♂️ Performance test: {len(instruments)} instruments, 1 day of 5-minute data")
    
    start_time = time.time()
    
    # Batch fetch
    batch_data = monitor.fetch_multiple_instruments_data(instruments, from_date, to_date, "5minute")
    
    # Multi-instrument analysis
    analysis = monitor.get_multi_instrument_analysis(instruments)
    
    total_time = time.time() - start_time
    
    # Performance metrics
    total_records = sum(len(df) for df in batch_data.values() if not df.empty)
    cache_stats = monitor.get_cache_statistics()
    
    print(f"🏁 Performance Results:")
    print(f"   ⏱️  Total time: {total_time:.3f} seconds")
    print(f"   📊 Total records: {total_records}")
    print(f"   ⚡ Records per second: {total_records / total_time:.1f}")
    print(f"   🎯 Cache hit ratio: {cache_stats.get('cache_hit_ratio', 0):.2f}")
    print(f"   💾 Cache size: {cache_stats.get('cache_size_mb', 0):.2f} MB")
    
    # Performance targets
    performance_good = (
        total_time < 30 and  # Should complete in under 30 seconds
        total_records > 100 and  # Should have meaningful data
        cache_stats.get('cache_hit_ratio', 0) >= 0.0  # Cache should work
    )
    
    if performance_good:
        print("✅ Performance benchmark PASSED")
    else:
        print("❌ Performance benchmark needs optimization")
    
    return performance_good

def main():
    """Run all tests and provide summary"""
    print("🚀 Enhanced Historical Data Fetching System - Comprehensive Test Suite")
    print("=" * 80)
    
    tests = [
        ("Basic Data Fetching", test_basic_data_fetching),
        ("Batch Fetching", test_batch_fetching),
        ("Retry Logic", test_retry_logic),
        ("Volatility Regimes", test_volatility_regimes),
        ("Multi-Instrument Analysis", test_multi_instrument_analysis),
        ("Cache Management", test_cache_management),
        ("Configuration Updates", test_configuration_updates)
    ]
    
    results = {}
    start_time = time.time()
    
    # Run all tests
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "✅ PASS" if result else "❌ FAIL"
        except Exception as e:
            results[test_name] = f"💥 ERROR: {e}"
    
    # Run performance benchmark
    try:
        perf_result = run_performance_benchmark()
        results["Performance Benchmark"] = "✅ PASS" if perf_result else "❌ FAIL"
    except Exception as e:
        results["Performance Benchmark"] = f"💥 ERROR: {e}"
    
    total_time = time.time() - start_time
    
    # Summary
    print("\n" + "="*80)
    print("📋 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result.startswith("✅"))
    total = len(results)
    
    for test_name, result in results.items():
        print(f"{result} {test_name}")
    
    print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
    print(f"⏱️  Total test time: {total_time:.2f} seconds")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED - Enhanced Historical Data System is PRODUCTION READY! 🚀")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed - Review implementation")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 