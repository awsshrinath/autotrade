
class StrategySelector:
    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def choose_strategy(bot_type="stock", sentiment="neutral"):
        # Simple rule-based fallback
        if bot_type == "stock":
            return "vwap"
        elif bot_type == "futures":
            return "orb"
        elif bot_type == "options":
            return "scalp"
        else:
            return "range_reversal"

# ✅ Externally used function
def select_best_strategy(bot_name="stock-trader"):
    bot_type = "stock" if "stock" in bot_name else (
               "futures" if "futures" in bot_name else "options")
    return StrategySelector.choose_strategy(bot_type)
