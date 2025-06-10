import pytest
from runner.market_monitor import MarketMonitor
from runner.market_data import MarketDataFetcher
from datetime import datetime, timedelta

@pytest.fixture
def market_monitor():
    """Fixture for MarketMonitor"""
    return MarketMonitor()

@pytest.fixture
def market_data_fetcher():
    """Fixture for MarketDataFetcher"""
    return MarketDataFetcher()

def test_fetch_historical_data_benchmark(benchmark, market_data_fetcher):
    """Benchmark the fetch_historical_data method"""
    from_date = datetime.now() - timedelta(days=5)
    to_date = datetime.now()
    instrument_token = 256265  # NIFTY 50

    def f():
        market_data_fetcher.fetch_historical_data(instrument_token, from_date, to_date, "day")

    benchmark(f)

def test_classify_trend_vs_range_benchmark(benchmark, market_monitor):
    """Benchmark the classify_trend_vs_range method"""
    # Fetch some data to use for the benchmark
    from_date = datetime.now() - timedelta(days=60)
    to_date = datetime.now()
    hist_data = market_monitor.data_fetcher.fetch_historical_data(256265, from_date, to_date, 'day')
    
    price_data = {
        'open': [d['open'] for d in hist_data],
        'high': [d['high'] for d in hist_data],
        'low': [d['low'] for d in hist_data],
        'close': [d['close'] for d in hist_data],
        'volume': [d['volume'] for d in hist_data]
    }

    def f():
        market_monitor.regime_classifier.classify_trend_vs_range(price_data)

    benchmark(f)

def test_correlation_matrix_benchmark(benchmark, market_monitor):
    """Benchmark the calculate_correlation_matrix method"""
    def f():
        market_monitor.correlation_monitor.calculate_correlation_matrix()

    benchmark(f) 