from strategies.base_strategy import BaseStrategy
from runner.utils.technical_indicators import calculate_vwap
from datetime import datetime, timedelta

class VWAPStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    def analyze(self):
        symbols = ['RELIANCE', 'TCS', 'INFY', 'HDFCBANK']
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(minutes=30)
            for symbol in symbols:
                try:
                    token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"]["instrument_token"]
                    candles = self.kite.historical_data(token, from_date, to_date, "5minute")
                    if not candles or len(candles) < 5:
                        continue
                    vwap = calculate_vwap(candles)
                    last_close = candles[-1]['close']
                    direction = "bullish" if last_close > vwap else "bearish"
                    trade = {
                        "symbol": symbol,
                        "entry_price": last_close,
                        "stop_loss": last_close - 0.5 if direction == "bullish" else last_close + 0.5,
                        "target": last_close + 1.0 if direction == "bullish" else last_close - 1.0,
                        "quantity": 10,
                        "direction": direction,
                        "strategy": "vwap"
                    }
                    self.logger.log_event(f"[VWAP] Signal: {trade}")
                    return trade
                except Exception as e:
                    self.logger.log_event(f"[VWAP][{symbol}] ERROR: {e}")
            return None
        except Exception as e:
            self.logger.log_event(f"[VWAP][ERROR] Overall failure: {e}")
            return None

    def should_exit(self, trade, current_price):
        try:
            if current_price <= trade["stop_loss"]:
                return "sl_hit"
            elif current_price >= trade["target"]:
                return "target_hit"
            return None
        except Exception as e:
            self.logger.log_event(f"[VWAP][ERROR] Exit logic failed: {e}")
            return None
