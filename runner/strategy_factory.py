from stock_trading.strategies.vwap_strategy import VWAPStrategy
from futures_trading.strategies.orb_strategy import ORBStrategy
from options_trading.strategies.scalp_strategy import ScalpStrategy
from stock_trading.strategies.range_reversal import RangeReversalStrategy

def load_strategy(strategy_name, kite, logger):
    STRATEGY_MAP = {
        "vwap": VWAPStrategy,
        "orb": ORBStrategy,
        "scalp": ScalpStrategy,
        "range_reversal": RangeReversalStrategy
    }

    strategy_cls = STRATEGY_MAP.get(strategy_name.lower())
    if strategy_cls:
        logger.log_event(f"[FACTORY] Loaded strategy: {strategy_name}")
        return strategy_cls(kite, logger)
    else:
        logger.log_event(f"[FACTORY][ERROR] Strategy not found: {strategy_name}")
        return None