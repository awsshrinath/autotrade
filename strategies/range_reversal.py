from strategies.base_strategy import BaseStrategy


class RangeReversalStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        super().__init__(kite, logger)
        self.traded_symbols = set()

    def find_trade_opportunities(self, market_data):
        """
        Dummy logic for now — will be replaced with real candle analysis.
        Simulates detection of 1 trade per category.
        """
        trades = []

        if "NIFTY" not in self.traded_symbols:
            trade = {
                "symbol": "NIFTY24MAY17700CE",
                "entry_price": 82.5,
                "quantity": 150,
                "stop_loss": 68.5,
                "target": 112.5,
                "strategy": "Range_Reversal",
                "type": "OPTIONS",
            }
            trades.append(trade)
            self.traded_symbols.add("NIFTY")
            self.logger.log_event(f"Trade opportunity detected: {trade}")

        return trades

    def should_exit_trade(self, trade):
        """
        Placeholder — always hold trades for now.
        """
        return False
