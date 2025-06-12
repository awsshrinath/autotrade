from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    def __init__(self, kite=None, logger=None):
        self.kite = kite
        self.logger = logger
        self.name = "BaseStrategy"

    def find_trade_opportunities(self, market_data):
        """
        Called repeatedly to check for trade opportunities.
        Should return a list of trade dicts or empty list.
        Default implementation returns empty list.
        """
        return []

    def should_exit_trade(self, trade):
        """
        Called to decide whether to exit a trade.
        Return True if trade should be closed.
        Default implementation returns False.
        """
        return False

    @abstractmethod
    def execute(self, symbol, candles, capital):
        """
        Execute the strategy for given symbol and data.
        This method must be implemented by subclasses.
        """
        pass
