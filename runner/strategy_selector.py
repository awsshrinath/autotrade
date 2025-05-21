class StrategySelector:
    def __init__(self, logger=None):
        self.logger = logger

    @staticmethod
    def choose_strategy(
        bot_type="stock", sentiment=None, market_sentiment=None
    ):
        # Determine direction from sentiment
        direction = "neutral"
        if sentiment:
            sgx_trend = sentiment.get("sgx_nifty", "neutral")
            dow_trend = sentiment.get("dow", "neutral")
            # Simple logic to determine overall direction
            if sgx_trend == "bullish" and dow_trend != "bearish":
                direction = "bullish"
            elif sgx_trend == "bearish" and dow_trend != "bullish":
                direction = "bearish"
            else:
                direction = "neutral"
        # Optional override using live market sentiment
        if market_sentiment:
            vix = market_sentiment.get("INDIA VIX", 0)
            market_sentiment.get("NIFTY 50", 0)

            if vix > 18:
                return "range_reversal", direction
            elif vix < 13:
                return "vwap", direction
            else:
                return "orb", direction

        # Fallback to static bot-type mapping
        if bot_type == "stock":
            return "vwap", direction
        elif bot_type == "futures":
            return "orb", direction
        elif bot_type == "options":
            return "scalp", direction
        else:
            return "range_reversal", direction


# ✅ Externally used function


def select_best_strategy(bot_name="stock-trader", market_sentiment=None, sentiment=None):
    bot_type = (
        "stock"
        if "stock" in bot_name
        else ("futures" if "futures" in bot_name else "options")
    )
    strategy, direction = StrategySelector.choose_strategy(
        bot_type, sentiment=sentiment, market_sentiment=market_sentiment
    )
    return strategy
