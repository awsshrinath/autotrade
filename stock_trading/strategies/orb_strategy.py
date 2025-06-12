from datetime import datetime

from strategies.base_strategy import BaseStrategy


class ORBStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    def analyze(self):
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
        try:
            now = datetime.now()
            market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
            orb_end = now.replace(hour=9, minute=30, second=0, microsecond=0)

            if now < orb_end:
                self.logger.log_event(
                    "[ORB] Waiting for 9:30 AM to evaluate opening range."
                )
                return None

            for symbol in symbols:
                try:
                    token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"][
                        "instrument_token"
                    ]
                    candles = self.kite.historical_data(
                        token, market_open, orb_end, "5minute"
                    )
                    if not candles or len(candles) < 3:
                        continue

                    highs = [c["high"] for c in candles]
                    lows = [c["low"] for c in candles]
                    high = max(highs)
                    low = min(lows)
                    close = candles[-1]["close"]

                    if close > high:
                        direction = "bullish"
                        sl = low - 2
                        target = close + 10
                    elif close < low:
                        direction = "bearish"
                        sl = high + 2
                        target = close - 10
                    else:
                        continue

                    trade = {
                        "symbol": symbol,
                        "entry_price": close,
                        "stop_loss": sl,
                        "target": target,
                        "quantity": 10,
                        "direction": direction,
                        "strategy": "orb",
                    }
                    self.logger.log_event(f"[ORB] Signal: {trade}")
                    return trade
                except Exception as e:
                    self.logger.log_event(f"[ORB][{symbol}] ERROR: {e}")
            return None
        except Exception as e:
            self.logger.log_event(f"[ORB][ERROR] Overall failure: {e}")
            return None

    def should_exit(self, trade, current_price):
        try:
            if current_price <= trade["stop_loss"]:
                return "sl_hit"
            elif current_price >= trade["target"]:
                return "target_hit"
            return None
        except Exception as e:
            self.logger.log_event(f"[ORB][ERROR] Exit logic failed: {e}")
            return None
