
import pytest
from runner.market_monitor import MarketMonitor

class MockLogger:
    def log_event(self, msg):
        print(f"[MOCK LOG] {msg}")

def test_get_market_sentiment_structure():
    monitor = MarketMonitor(logger=MockLogger())
    sentiment = monitor.get_market_sentiment()
    assert isinstance(sentiment, dict)
    assert "sgx_nifty" in sentiment
    assert "dow" in sentiment
    assert "vix" in sentiment
    assert "nifty_trend" in sentiment

    for key in ["sgx_nifty", "dow", "nifty_trend"]:
        assert sentiment[key] in ["bullish", "bearish", "neutral"]

    assert sentiment["vix"] in ["low", "moderate", "high"]
