import sys

sys.path.insert(0, ".")


def test_config():
    from runner import config

    print(f"\u2705 config.py loaded: PAPER_TRADE={config.PAPER_TRADE}")


def test_vwap_strategy():
    try:
        from strategies.vwap_strategy import vwap_strategy

        result = vwap_strategy(
            symbol="NIFTY", instrument_token="FAKE", capital=10000
        )
        print("✅ vwap_strategy loaded and callable.")
    except Exception as e:
        print(f"\u274c vwap_strategy failed: {e}")


def test_strike_picker():
    try:
        from options_trading.utils.strike_picker import pick_strike

        result = pick_strike(symbol="NIFTY", direction="bullish")
        print(
            f"✅ strike_picker returned: {result.get('symbol', 'UNKNOWN') if result else 'None'}"
        )
    except Exception as e:
        print(f"\u274c strike_picker failed: {e}")


def test_risk_governor():
    try:
        from runner.risk_governor import RiskGovernor

        rg = RiskGovernor(max_daily_loss=600, max_trades=3)
        allowed = rg.can_trade()
        print(f"✅ risk_governor.can_trade() → {allowed}")
    except Exception as e:
        print(f"\u274c risk_governor failed: {e}")


def test_gpt_reflection():
    try:
        from runner.gpt_self_improvement_monitor import run_gpt_reflection

        run_gpt_reflection(bot_name="options-trader")
        print("✅ GPT reflection ran successfully")
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
