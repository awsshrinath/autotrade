class MarketMonitor:
    def __init__(self, logger=None):
        self.logger = logger

    def get_market_sentiment(self, kite_client):
        try:
            indices = {
                "NIFTY 50": 256265,
                "BANKNIFTY": 260105,
                "INDIA VIX": 264969
            }

            ltp = kite_client.ltp([f"NSE:{symbol}" for symbol in indices.keys()])

            sentiment = {}
            for symbol, data in ltp.items():
                sentiment[symbol.split(":")[1]] = data["last_price"]

            if self.logger:
                self.logger.log_event("Fetched market sentiment successfully")

            return sentiment

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] get_market_sentiment failed: {e}")
            return {}
