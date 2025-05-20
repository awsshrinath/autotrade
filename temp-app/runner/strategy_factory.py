# runner/strategy_factory.py

from strategies.range_reversal import RangeReversalStrategy

# In future: from runner.strategies.opening_range_breakout import OpeningRangeBreakoutStrategy
# In future: from runner.strategies.vwap_reversal import VWAPReversalStrategy

def load_strategy(strategy_name, kite, logger):
    if strategy_name == "Range_Reversal":
        return RangeReversalStrategy(kite, logger)
    # elif strategy_name == "Opening_Range_Breakout":
    #     return OpeningRangeBreakoutStrategy(kite, logger)
    # elif strategy_name == "VWAP_Reversal":
    #     return VWAPReversalStrategy(kite, logger)
    else:
        logger.log_event(f"Strategy '{strategy_name}' not found. Using fallback dummy strategy.")
        return None
