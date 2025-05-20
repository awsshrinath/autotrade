
# runner/market_monitor.py

class MarketMonitor:
    def __init__(self, logger=None):
        self.logger = logger

    def get_market_sentiment(self):
        # Mock sentiment logic for testing
        if self.logger:
            self.logger.log_event("Returning mock market sentiment")
        return {
            "sgx_nifty": "bullish",
            "dow": "neutral",
            "vix": "low",
            "nifty_trend": "bullish"
        }

# Test Mode
if __name__ == "__main__":
    print("MarketMonitor class is ready!")
