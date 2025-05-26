from datetime import datetime, timedelta

from runner.utils.technical_indicators import calculate_vwap
from strategies.base_strategy import BaseStrategy


class VWAPStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        super().__init__(kite, logger)

    def find_trade_opportunities(self, market_data):
        """
        Called repeatedly to check for trade opportunities.
        Should return a list of trade dicts or empty list.
        """
        symbols = ["RELIANCE", "TCS", "INFY", "HDFCBANK"]
        trades = []
        try:
            to_date = datetime.now()
            from_date = to_date - timedelta(minutes=30)
            for symbol in symbols:
                try:
                    token = self.kite.ltp([f"NSE:{symbol}"])[f"NSE:{symbol}"][
                        "instrument_token"
                    ]
                    candles = self.kite.historical_data(
                        token, from_date, to_date, "5minute"
                    )
                    if not candles or len(candles) < 5:
                        continue
                    vwap = calculate_vwap(candles)
                    last_close = candles[-1]["close"]
                    direction = "bullish" if last_close > vwap else "bearish"
                    trade = {
                        "symbol": symbol,
                        "entry_price": last_close,
                        "stop_loss": (
                            last_close - 0.5
                            if direction == "bullish"
                            else last_close + 0.5
                        ),
                        "target": (
                            last_close + 1.0
                            if direction == "bullish"
                            else last_close - 1.0
                        ),
                        "quantity": 10,
                        "direction": direction,
                        "strategy": "vwap",
                    }
                    self.logger.log_event(f"[VWAP] Signal: {trade}")
                    trades.append(trade)
                except Exception as e:
                    self.logger.log_event(f"[VWAP][{symbol}] ERROR: {e}")
            return trades
        except Exception as e:
            self.logger.log_event(f"[VWAP][ERROR] Overall failure: {e}")
            return []

    def should_exit_trade(self, trade):
        """
        Called to decide whether to exit a trade.
        Return True if trade should be closed.
        """
        try:
            # Fetch current price for the symbol
            symbol = trade.get("symbol")
            if not symbol:
                self.logger.log_event(f"[VWAP][ERROR] Trade missing symbol: {trade}")
                return False
            ltp_data = self.kite.ltp([f"NSE:{symbol}"])
            current_price = ltp_data.get(f"NSE:{symbol}", {}).get("last_price")
            if current_price is None:
                self.logger.log_event(
                    f"[VWAP][ERROR] Could not fetch current price for {symbol}"
                )
                return False
            if current_price <= trade["stop_loss"]:
                return True
            elif current_price >= trade["target"]:
                return True
            return False
        except Exception as e:
            self.logger.log_event(f"[VWAP][ERROR] Exit logic failed: {e}")
            return False
