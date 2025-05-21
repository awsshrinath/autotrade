from datetime import datetime, timedelta

from strategies.base_strategy import BaseStrategy


class RangeReversalStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    def analyze(self):
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
        try:
            to_time = datetime.now()
            from_time = to_time - timedelta(minutes=30)

            for symbol in symbols:
                try:
                    token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"][
                        "instrument_token"
                    ]
                    candles = self.kite.historical_data(
                        token, from_time, to_time, "5minute"
                    )
                    if not candles or len(candles) < 5:
                        continue

                    open_price = candles[0]["open"]
                    close_price = candles[-1]["close"]

                    if abs(close_price - open_price) < 1.0:
                        continue

                    direction = (
                        "bullish" if close_price > open_price else "bearish"
                    )
                    entry = close_price
                    sl = entry - 1.0 if direction == "bullish" else entry + 1.0
                    target = (
                        entry + 2.0 if direction == "bullish" else entry - 2.0
                    )

                    trade = {
                        "symbol": symbol,
                        "entry_price": entry,
                        "stop_loss": sl,
                        "target": target,
                        "quantity": 10,
                        "direction": direction,
                        "strategy": "range_reversal",
                    }
                    self.logger.log_event(f"[RANGE] Signal: {trade}")
                    return trade
                except Exception as e:
                    self.logger.log_event(f"[RANGE][{symbol}] ERROR: {e}")

            return None
        except Exception as e:
            self.logger.log_event(f"[RANGE][ERROR] Overall failure: {e}")
            return None

    def should_exit(self, trade, current_price):
        try:
            if current_price <= trade["stop_loss"]:
                return "sl_hit"
            elif current_price >= trade["target"]:
                return "target_hit"
            return None
        except Exception as e:
            self.logger.log_event(f"[RANGE][ERROR] Exit logic failed: {e}")
            return None
