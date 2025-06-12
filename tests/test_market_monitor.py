from runner.market_data import MarketDataFetcher, TechnicalIndicators
from runner.market_monitor import MarketMonitor, CorrelationMonitor, MarketRegimeClassifier


class MockLogger:
    def log_event(self, msg):
        print(f"[MOCK LOG] {msg}")


class MockKiteClient:
    def ltp(self, symbols):
        return {
            "NSE:NIFTY 50": {"last_price": 18000},
            "NSE:BANKNIFTY": {"last_price": 40000},
            "NSE:INDIA VIX": {"last_price": 15},
        }


def test_get_market_sentiment_structure():
    monitor = MarketMonitor(logger=MockLogger())
    sentiment = monitor.get_market_sentiment(kite_client=MockKiteClient())
    assert isinstance(sentiment, dict)
    assert "sgx_nifty" in sentiment
    assert "dow" in sentiment
    assert "vix" in sentiment
    assert "nifty_trend" in sentiment

    for key in ["sgx_nifty", "dow", "nifty_trend"]:
        assert sentiment[key] in ["bullish", "bearish", "neutral"]

    assert sentiment["vix"] in ["low", "moderate", "high"]
