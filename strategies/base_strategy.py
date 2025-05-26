from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    def __init__(self, kite, logger):
        self.kite = kite
        self.logger = logger

    @abstractmethod
    def find_trade_opportunities(self, market_data):
        """
        Called repeatedly to check for trade opportunities.
        Should return a list of trade dicts or empty list.
        """

    @abstractmethod
    def should_exit_trade(self, trade):
        """
        Called to decide whether to exit a trade.
        Return True if trade should be closed.
        """
