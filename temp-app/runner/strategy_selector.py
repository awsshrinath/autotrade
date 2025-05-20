
# runner/strategy_selector.py

class StrategySelector:
    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def choose_strategy(bot_type, sentiment):
        # Mock logic for testing
        if bot_type == "stock":
            return ("vwap_strategy", "bearish")
        elif bot_type == "futures":
            return ("orb_strategy", "bullish")
        else:
            return ("range_reversal", "neutral")

# Test Mode
if __name__ == "__main__":
    print("StrategySelector class is ready!")
