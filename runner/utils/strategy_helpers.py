"""
Strategy helper functions for trading strategies.
Now uses the enterprise engines with paper trade support.
"""

from runner.indicators.technical_engine import create_technical_engine
from runner.options.pricing_engine import create_options_engine
from runner.capital.portfolio_manager import create_portfolio_manager
import os


def calculate_vwap(candles):
    """
    Calculate VWAP using enterprise technical engine
    """
    engine = create_technical_engine()
    result = engine.calculate_vwap_advanced(candles)
    return result.value


def calculate_atr(candles, period=14):
    """
    Calculate ATR using enterprise technical engine
    """
    engine = create_technical_engine()
    result = engine.calculate_smart_atr(candles, period)
    return result.value


def calculate_quantity(price, capital, risk_pct=0.02):
    """
    Calculate position quantity with risk management
    """
    if price <= 0:
        return 0

    # Risk-based position sizing
    risk_amount = capital * risk_pct
    max_quantity_by_risk = int(risk_amount / price)

    # Traditional position sizing (10% of capital)
    traditional_quantity = int(capital * 0.1 / price)

    # Use the smaller of the two for conservative sizing
    return min(max_quantity_by_risk, traditional_quantity)


def get_strategy_signal(candles, strategy_type="comprehensive"):
    """
    Get trading signal based on multiple technical indicators
    """
    engine = create_technical_engine()

    try:
        # Get individual signals
        vwap_signal = engine.calculate_vwap_advanced(candles)
        rsi_signal = engine.calculate_adaptive_rsi(candles)
        atr_signal = engine.calculate_smart_atr(candles)
        macd_signal = engine.calculate_macd(candles)

        # Aggregate signals
        signals = [vwap_signal, rsi_signal, macd_signal]
        buy_count = sum(1 for s in signals if s.signal == "BUY")
        sell_count = sum(1 for s in signals if s.signal == "SELL")

        # Determine overall signal
        if buy_count > sell_count:
            overall_signal = "BUY"
            confidence = buy_count / len(signals)
        elif sell_count > buy_count:
            overall_signal = "SELL"
            confidence = sell_count / len(signals)
        else:
            overall_signal = "HOLD"
            confidence = 0.5

        # Adjust confidence based on volatility
        volatility = atr_signal.metadata.get("ratio", 1.0)
        if volatility > 1.5:  # High volatility reduces confidence
            confidence *= 0.8
        elif volatility < 0.7:  # Low volatility increases confidence
            confidence *= 1.2

        confidence = min(1.0, max(0.1, confidence))  # Clamp between 0.1 and 1.0

        return {
            "signal": overall_signal,
            "confidence": confidence,
            "individual_signals": {
                "vwap": {"signal": vwap_signal.signal, "value": vwap_signal.value},
                "rsi": {"signal": rsi_signal.signal, "value": rsi_signal.value},
                "atr": {"signal": atr_signal.signal, "value": atr_signal.value},
                "macd": {"signal": macd_signal.signal, "value": macd_signal.value},
            },
            "volatility_regime": atr_signal.metadata.get("regime", "NORMAL"),
            "paper_trade": engine.paper_trade,
        }

    except Exception as e:
        # Fallback to neutral signal on error
        return {
            "signal": "HOLD",
            "confidence": 0.5,
            "error": str(e),
            "paper_trade": True,
        }


def calculate_stop_loss_target(
    entry_price, direction, atr_value, risk_reward_ratio=2.0
):
    """
    Calculate stop loss and target prices based on ATR
    """
    if direction.lower() == "bullish":
        stop_loss = entry_price - (1.5 * atr_value)
        target = entry_price + (risk_reward_ratio * 1.5 * atr_value)
    else:
        stop_loss = entry_price + (1.5 * atr_value)
        target = entry_price - (risk_reward_ratio * 1.5 * atr_value)

    return {
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "risk_amount": 1.5 * atr_value,
        "reward_amount": risk_reward_ratio * 1.5 * atr_value,
        "risk_reward_ratio": risk_reward_ratio,
    }


def validate_trade_signal(signal_data, market_conditions=None):
    """
    Validate trade signal based on market conditions and confidence
    """
    if not signal_data or signal_data.get("signal") == "HOLD":
        return False, "No clear signal"

    confidence = signal_data.get("confidence", 0)
    if confidence < 0.6:
        return False, f"Low confidence: {confidence:.1%}"

    # Check volatility regime
    volatility_regime = signal_data.get("volatility_regime", "NORMAL")
    if volatility_regime == "HIGH_VOLATILITY":
        if confidence < 0.8:
            return False, "High volatility requires higher confidence"

    # Market conditions check
    if market_conditions:
        market_hours = market_conditions.get("market_hours", True)
        if not market_hours:
            return False, "Outside market hours"

        market_trend = market_conditions.get("trend", "neutral")
        signal_direction = signal_data.get("signal")

        # Avoid counter-trend trades in strong trending markets
        if market_trend == "strong_bullish" and signal_direction == "SELL":
            if confidence < 0.9:
                return False, "Counter-trend trade in strong bull market"
        elif market_trend == "strong_bearish" and signal_direction == "BUY":
            if confidence < 0.9:
                return False, "Counter-trend trade in strong bear market"

    return True, "Signal validated"


def optimize_position_size(symbol, strategy, price, capital, volatility=0.02):
    """
    Optimize position size using portfolio manager
    """
    try:
        portfolio_manager = create_portfolio_manager(
            initial_capital=capital,
            paper_trade=os.getenv("PAPER_TRADE", "true").lower() == "true",
        )

        # Get recommended position size
        position_info = portfolio_manager.calculate_position_size(
            symbol=symbol,
            strategy=strategy,
            price=price,
            volatility=volatility,
            confidence=0.7,  # Default confidence
        )

        return {
            "recommended_quantity": position_info.get("recommended_quantity", 0),
            "position_value": position_info.get("position_value", 0),
            "allocation_pct": position_info.get("final_allocation_pct", 0),
            "risk_amount": position_info.get("risk_amount", 0),
            "kelly_fraction": position_info.get("kelly_fraction", 0),
            "asset_type": position_info.get("asset_type", "stock"),
        }

    except Exception as e:
        # Fallback to simple calculation
        safe_quantity = int(capital * 0.05 / price) if price > 0 else 0
        return {
            "recommended_quantity": safe_quantity,
            "position_value": safe_quantity * price,
            "allocation_pct": 5.0,
            "error": str(e),
        }


def get_options_recommendation(
    kite, symbol, direction, strategy="scalp", capital=100000
):
    """
    Get options trading recommendation
    """
    try:
        options_engine = create_options_engine()

        # Get spot price
        if options_engine.paper_trade:
            spot_price = 18500  # Mock spot price
        else:
            spot_ltp = kite.ltp([f"NSE:{symbol}"])
            spot_price = spot_ltp[f"NSE:{symbol}"]["last_price"]

        # Get option chain
        import asyncio

        if options_engine.paper_trade:
            option_chain = options_engine._mock_option_chain(symbol, spot_price)
        else:
            option_chain = asyncio.run(
                options_engine.analyze_option_chain(kite, symbol, spot_price)
            )

        # Select optimal strategy
        recommendation = options_engine.select_optimal_strikes(
            option_chain, strategy, direction, capital
        )

        if recommendation and "primary" in recommendation:
            option = recommendation["primary"]
            return {
                "symbol": option.symbol,
                "strike": option.strike,
                "option_type": option.option_type,
                "market_price": option.market_price,
                "quantity": recommendation.get("quantity", 1),
                "total_cost": recommendation.get("quantity", 1) * option.market_price,
                "greeks": option.greeks,
                "iv": option.iv,
                "strategy_params": recommendation.get("strategy_params", {}),
                "risk_metrics": recommendation.get("risk_metrics", {}),
                "paper_trade": option.is_mock,
                "liquidity_score": option.liquidity_score,
            }
        else:
            return {
                "error": "No suitable options found",
                "symbol": symbol,
                "direction": direction,
                "strategy": strategy,
            }

    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "direction": direction,
            "strategy": strategy,
        }


def calculate_portfolio_exposure(positions):
    """
    Calculate total portfolio exposure and risk metrics
    """
    if not positions:
        return {
            "total_exposure": 0,
            "long_exposure": 0,
            "short_exposure": 0,
            "net_exposure": 0,
            "concentration_risk": "LOW",
            "top_positions": [],
        }

    total_long = sum(
        pos.get("value", 0) for pos in positions if pos.get("quantity", 0) > 0
    )
    total_short = sum(
        abs(pos.get("value", 0)) for pos in positions if pos.get("quantity", 0) < 0
    )
    total_exposure = total_long + total_short
    net_exposure = total_long - total_short

    # Calculate concentration risk
    if positions:
        max_position = max(positions, key=lambda x: abs(x.get("value", 0)))
        max_position_pct = (
            abs(max_position.get("value", 0)) / total_exposure * 100
            if total_exposure > 0
            else 0
        )

        if max_position_pct > 30:
            concentration_risk = "HIGH"
        elif max_position_pct > 20:
            concentration_risk = "MEDIUM"
        else:
            concentration_risk = "LOW"
    else:
        concentration_risk = "NONE"

    # Top positions by exposure
    top_positions = sorted(
        positions, key=lambda x: abs(x.get("value", 0)), reverse=True
    )[:5]

    return {
        "total_exposure": total_exposure,
        "long_exposure": total_long,
        "short_exposure": total_short,
        "net_exposure": net_exposure,
        "concentration_risk": concentration_risk,
        "top_positions": [
            {
                "symbol": pos.get("symbol"),
                "value": pos.get("value", 0),
                "percentage": (
                    abs(pos.get("value", 0)) / total_exposure * 100
                    if total_exposure > 0
                    else 0
                ),
            }
            for pos in top_positions
        ],
    }


def get_market_regime_signal(candles, lookback_days=20):
    """
    Determine market regime (trending vs ranging)
    """
    engine = create_technical_engine()

    try:
        # Get ATR for volatility assessment
        atr_result = engine.calculate_smart_atr(candles, 14)

        # Get RSI for momentum assessment
        rsi_result = engine.calculate_adaptive_rsi(candles, 14)

        # Get MACD for trend assessment
        macd_result = engine.calculate_macd(candles)

        # Determine regime
        volatility_regime = atr_result.metadata.get("regime", "NORMAL")
        rsi_value = rsi_result.value
        macd_histogram = macd_result.metadata.get("histogram", 0)

        # Market regime logic
        if volatility_regime == "HIGH_VOLATILITY":
            if abs(macd_histogram) > 10:
                regime = "TRENDING_VOLATILE"
            else:
                regime = "RANGING_VOLATILE"
        elif volatility_regime == "LOW_VOLATILITY":
            if 30 < rsi_value < 70:
                regime = "RANGING_CALM"
            else:
                regime = "TRENDING_CALM"
        else:
            if abs(macd_histogram) > 5:
                regime = "TRENDING"
            else:
                regime = "RANGING"

        return {
            "regime": regime,
            "volatility": volatility_regime,
            "trend_strength": abs(macd_histogram),
            "momentum": rsi_value,
            "recommendation": _get_regime_recommendation(regime),
            "paper_trade": engine.paper_trade,
        }

    except Exception as e:
        return {"regime": "UNKNOWN", "error": str(e), "paper_trade": True}


def _get_regime_recommendation(regime):
    """
    Get trading recommendations based on market regime
    """
    recommendations = {
        "TRENDING_VOLATILE": {
            "strategy": "momentum",
            "position_size": "reduced",
            "holding_period": "short",
            "stop_loss": "tight",
        },
        "RANGING_VOLATILE": {
            "strategy": "mean_reversion",
            "position_size": "reduced",
            "holding_period": "very_short",
            "stop_loss": "very_tight",
        },
        "RANGING_CALM": {
            "strategy": "range_trading",
            "position_size": "normal",
            "holding_period": "medium",
            "stop_loss": "normal",
        },
        "TRENDING_CALM": {
            "strategy": "trend_following",
            "position_size": "increased",
            "holding_period": "long",
            "stop_loss": "wide",
        },
        "TRENDING": {
            "strategy": "momentum",
            "position_size": "normal",
            "holding_period": "medium",
            "stop_loss": "normal",
        },
        "RANGING": {
            "strategy": "mean_reversion",
            "position_size": "normal",
            "holding_period": "short",
            "stop_loss": "normal",
        },
    }

    return recommendations.get(
        regime,
        {
            "strategy": "conservative",
            "position_size": "reduced",
            "holding_period": "short",
            "stop_loss": "tight",
        },
    )
