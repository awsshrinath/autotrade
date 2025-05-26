class MarketMonitor:
    def __init__(self, logger=None):
        self.logger = logger

    def get_latest_market_context(self, kite_client=None):
        """
        Get the latest market context including sentiment, volatility, and trend
        """
        sentiment = self.get_market_sentiment(kite_client)

        # Add additional market context
        context = {
            "sentiment": sentiment,
            "volatility": "medium",  # Placeholder
            "trend": "neutral",  # Placeholder
            "timestamp": "2023-01-01T00:00:00Z",  # Placeholder
        }

        return context

    def get_market_sentiment(self, kite_client):
        try:
            indices = {
                "NIFTY 50": 256265,
                "BANKNIFTY": 260105,
                "INDIA VIX": 264969,
            }

            ltp = kite_client.ltp([f"NSE:{symbol}" for symbol in indices.keys()])

            # Get raw price data
            raw_data = {}
            for symbol, data in ltp.items():
                raw_data[symbol.split(":")[1]] = data["last_price"]

            # Convert to sentiment indicators
            sentiment = {
                "sgx_nifty": (
                    "bullish"
                    if raw_data.get("NIFTY 50", 0) > 17500
                    else "bearish" if raw_data.get("NIFTY 50", 0) < 17000 else "neutral"
                ),
                "dow": "neutral",  # Placeholder as we don't have Dow data
                "vix": (
                    "low"
                    if raw_data.get("INDIA VIX", 0) < 14
                    else "high" if raw_data.get("INDIA VIX", 0) > 18 else "moderate"
                ),
                "nifty_trend": (
                    "bullish"
                    if raw_data.get("NIFTY 50", 0) > raw_data.get("BANKNIFTY", 0) / 2.2
                    else (
                        "bearish"
                        if raw_data.get("NIFTY 50", 0)
                        < raw_data.get("BANKNIFTY", 0) / 2.3
                        else "neutral"
                    )
                ),
            }

            if self.logger:
                self.logger.log_event("Fetched market sentiment successfully")

            return sentiment

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] get_market_sentiment failed: {e}")
            return {}


# Standalone function for backward compatibility
def get_latest_market_context(kite_client=None, logger=None):
    """
    Standalone function to get the latest market context
    """
    monitor = MarketMonitor(logger)
    return monitor.get_latest_market_context(kite_client)
