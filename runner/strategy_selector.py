class StrategySelector:
    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def choose_strategy(
        bot_type="stock", sentiment="neutral", market_sentiment=None
    ):
        # Optional override using live market sentiment
        if market_sentiment:
            vix = market_sentiment.get("INDIA VIX", 0)
            market_sentiment.get("NIFTY 50", 0)

            if vix > 18:
                return "range_reversal"
            elif vix < 13:
                return "vwap"
            else:
                return "orb"

        # Fallback to static bot-type mapping
        if bot_type == "stock":
            return "vwap"
        elif bot_type == "futures":
            return "orb"
        elif bot_type == "options":
            return "scalp"
        else:
            return "range_reversal"


# ✅ Externally used function


def select_best_strategy(bot_name="stock-trader", market_sentiment=None):
    bot_type = (
        "stock"
        if "stock" in bot_name
        else ("futures" if "futures" in bot_name else "options")
    )
    return StrategySelector.choose_strategy(
        bot_type, market_sentiment=market_sentiment
    )
