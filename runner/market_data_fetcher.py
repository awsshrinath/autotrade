# runner/market_data_fetcher.py

import datetime


class MarketDataFetcher:
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    def fetch_latest_candle(self, instrument_token, interval="5minute"):
        try:
            now = datetime.datetime.now()
            from_time = now - datetime.timedelta(minutes=10)  # last 10 minutes
            to_time = now

            candles = self.kite.historical_data(
                instrument_token,
                from_time,
                to_time,
                interval,
                continuous=False,
                oi=True,
            )

            if candles:
                latest_candle = candles[-1]  # Latest candle
                return {
                    "timestamp": latest_candle["date"],
                    "open": latest_candle["open"],
                    "high": latest_candle["high"],
                    "low": latest_candle["low"],
                    "close": latest_candle["close"],
                    "volume": latest_candle["volume"],
                }
            else:
                self.logger.log_event(f"No candle data returned for {instrument_token}")
                return None

        except Exception as e:
            self.logger.log_event(f"Error fetching latest candle: {e}")
            return None
