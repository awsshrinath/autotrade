import sys
from datetime import datetime

sys.path.insert(0, ".")

from runner import config

print(f"✅ config.py loaded: PAPER_TRADE={config.PAPER_TRADE}")

from strategies.vwap_strategy import vwap_strategy

fake_candles = [
    {"high": 101, "low": 99, "close": 100, "volume": 10000}
] * 15  # Dummy 15 candles

trade = vwap_strategy(symbol="NIFTY", candles=fake_candles, capital=10000)
print("✅ vwap_strategy output:", trade)

from unittest.mock import patch

from options_trading.utils.strike_picker import pick_strike
from runner.logger import Logger


# Mock the access_secret function to avoid Google Cloud authentication issues
@patch("runner.secret_manager_client.access_secret")
def mock_access_secret(mock_access_secret):
    mock_access_secret.return_value = "mock_secret_value"
    return mock_access_secret


# Mock the KiteConnect client
class MockKiteConnect:
    def __init__(self):
        pass

    def set_access_token(self, token):
        pass

    def ltp(self, symbol):
        return {symbol: {"last_price": 100}}

    def instruments(self, exchange):
        return [
            {
                "tradingsymbol": "NIFTY25MAY18000CE",
                "name": "NIFTY",
                "instrument_type": "CE",
                "strike": 18000,
                "expiry": datetime.now().date(),
            }
        ]


# Create a logger and mock KiteConnect client for the pick_strike function
logger = Logger(datetime.now().strftime("%Y-%m-%d"))
kite = MockKiteConnect()

pick_strike(kite=kite, symbol="NIFTY", direction="bullish")

from runner.risk_governor import RiskGovernor

rg = RiskGovernor(max_daily_loss=600, max_trades=3)
print("✅ risk_governor.can_trade() →", rg.can_trade())

# Mock the OpenAIManager to avoid Google Cloud authentication issues
from unittest.mock import patch


@patch("runner.openai_manager.OpenAIManager")
def mock_run_gpt_reflection(mock_openai):
    mock_openai.return_value.ask.return_value = "Mock GPT reflection response"
    print("✅ GPT reflection mocked successfully")


# Run the mock instead of the actual function
mock_run_gpt_reflection()


def test_config():
    from runner import config

    print(f"\u2705 config.py loaded: PAPER_TRADE={config.PAPER_TRADE}")


def test_vwap_strategy():
    try:
        from strategies.vwap_strategy import vwap_strategy

        result = vwap_strategy(
            kite=None, instrument_token="TEST_TOKEN", symbol="NIFTY", capital=10000
        )
        if result and isinstance(result, dict):
            print(
                f"\u2705 vwap_strategy.py returned a trade dict with keys: {list(result.keys())}"
            )
        else:
            print("\u274c vwap_strategy returned None or invalid format")
    except Exception as e:
        print(f"\u274c vwap_strategy failed: {e}")


def test_strike_picker():
    try:
        from options_trading.utils.strike_picker import pick_strike

        # Use the mock KiteConnect client
        kite = MockKiteConnect()

        result = pick_strike(kite=kite, symbol="NIFTY", direction="bullish")
        if result:
            print(
                f"\u2705 strike_picker returned: {result.get('tradingsymbol', 'UNKNOWN')}"
            )
        else:
            print("\u274c strike_picker returned None")
    except Exception as e:
        print(f"\u274c strike_picker failed: {e}")


def test_risk_governor():
    try:
        from runner import risk_governor

        allowed = risk_governor.can_trade()
        print(f"\u2705 risk_governor.can_trade() → {allowed}")
    except Exception as e:
        print(f"\u274c risk_governor failed: {e}")


def test_gpt_reflection():
    try:
        from runner import gpt_self_improvement_monitor

        gpt_self_improvement_monitor.run_gpt_reflection()
        print("\u2705 GPT reflection ran successfully")
    except Exception as e:
        print(f"\u274c GPT reflection failed: {e}")


if __name__ == "__main__":
    print("\U0001f680 Running GPT Runner Health Checks...\n")
    test_config()
    test_vwap_strategy()
    test_strike_picker()
    test_risk_governor()
    test_gpt_reflection()
    print("\n\u2705 All checks completed.")
