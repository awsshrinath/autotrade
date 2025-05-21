from runner.strategy_selector import StrategySelector

mock_sentiment = {
    "sgx_nifty": "bullish",
    "dow": "neutral",
    "vix": "low",
    "nifty_trend": "bullish",
}


def test_choose_strategy_stock():
    strategy, direction = StrategySelector.choose_strategy("stock", mock_sentiment)
    assert isinstance(strategy, str)
    assert direction in ["bullish", "bearish", "neutral"]


def test_choose_strategy_futures():
    strategy, direction = StrategySelector.choose_strategy("futures", mock_sentiment)
    assert isinstance(strategy, str)
    assert direction in ["bullish", "bearish", "neutral"]


def test_choose_strategy_options():
    strategy, direction = StrategySelector.choose_strategy("options", mock_sentiment)
    assert isinstance(strategy, str)
    assert direction in ["bullish", "bearish", "neutral"]
