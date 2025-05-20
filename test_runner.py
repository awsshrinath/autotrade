
import sys
import os
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

from options_trading.utils.strike_picker import pick_strike
pick_strike(symbol="NIFTY", direction="bullish")

from runner.risk_governor import RiskGovernor
rg = RiskGovernor(max_daily_loss=600, max_trades=3)
print("✅ risk_governor.can_trade() →", rg.can_trade())

from runner.gpt_self_improvement_monitor import run_gpt_reflection
run_gpt_reflection(bot_name="options-trader")

def test_config():
    from runner import config
    print(f"\u2705 config.py loaded: PAPER_TRADE={config.PAPER_TRADE}")

def test_vwap_strategy():
    try:
        from strategies.vwap_strategy import vwap_strategy
        result = vwap_strategy(kite=None, instrument_token="FAKE", symbol="NIFTY", capital=10000)
        if result and isinstance(result, dict):
            print(f"\u2705 vwap_strategy.py returned a trade dict with keys: {list(result.keys())}")
        else:
            print("\u274C vwap_strategy returned None or invalid format")
    except Exception as e:
        print(f"\u274C vwap_strategy failed: {e}")

def test_strike_picker():
    try:
        from options_trading.utils.strike_picker import pick_strike
        result = pick_strike("NIFTY", "bullish")
        if result:
            print(f"\u2705 strike_picker returned: {result.get('symbol', 'UNKNOWN')}")
        else:
            print("\u274C strike_picker returned None")
    except Exception as e:
        print(f"\u274C strike_picker failed: {e}")

def test_risk_governor():
    try:
        from runner import risk_governor
        allowed = risk_governor.can_trade()
        print(f"\u2705 risk_governor.can_trade() → {allowed}")
    except Exception as e:
        print(f"\u274C risk_governor failed: {e}")

def test_gpt_reflection():
    try:
        from runner import gpt_self_improvement_monitor
        gpt_self_improvement_monitor.run_gpt_reflection()
        print("\u2705 GPT reflection ran successfully")
    except Exception as e:
        print(f"\u274C GPT reflection failed: {e}")

if __name__ == "__main__":
    print("\U0001F680 Running GPT Runner Health Checks...\n")
    test_config()
    test_vwap_strategy()
    test_strike_picker()
    test_risk_governor()
    test_gpt_reflection()
    print("\n\u2705 All checks completed.")
