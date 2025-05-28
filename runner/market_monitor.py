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

    def get_sentiment(self, kite_client=None):
        """Alias for get_market_sentiment for backward compatibility"""
        return self.get_market_sentiment(kite_client)

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

    def fetch_premarket_data(self):
        """Fetch pre-market data for strategy selection"""
        try:
            # Placeholder implementation - in real scenario would fetch actual pre-market data
            premarket_data = {
                "sgx_nifty": {"change": 0.5, "trend": "bullish"},
                "dow_futures": {"change": -0.2, "trend": "bearish"},
                "crude_oil": {"change": 1.2, "trend": "bullish"},
                "dollar_index": {"change": -0.1, "trend": "neutral"},
                "vix": {"value": 15.5, "trend": "low"},
                "market_sentiment": "neutral"
            }
            
            if self.logger:
                self.logger.log_event("Fetched pre-market data successfully")
            
            return premarket_data
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] fetch_premarket_data failed: {e}")
            return {}


# Standalone functions for backward compatibility
def get_latest_market_context(kite_client=None, logger=None):
    """
    Standalone function to get the latest market context
    """
    monitor = MarketMonitor(logger)
    return monitor.get_latest_market_context(kite_client)


def get_nifty_trend(kite_client=None, logger=None):
    """
    Get NIFTY trend analysis - standalone function for strategy compatibility
    """
    try:
        if kite_client:
            monitor = MarketMonitor(logger)
            sentiment = monitor.get_market_sentiment(kite_client)
            return sentiment.get("nifty_trend", "neutral")
        else:
            # Fallback when no kite client available (paper trading)
            import random
            trends = ["bullish", "bearish", "neutral"]
            return random.choice(trends)
    except Exception as e:
        if logger:
            logger.log_event(f"[ERROR] get_nifty_trend failed: {e}")
        return "neutral"


def get_market_sentiment(kite_client=None, logger=None):
    """
    Standalone function to get market sentiment
    """
    monitor = MarketMonitor(logger)
    return monitor.get_market_sentiment(kite_client)
