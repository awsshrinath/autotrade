"""
Option utilities module for options trading strategies.
Now uses the enterprise OptionsEngine with paper trade support.
"""

from runner.options.pricing_engine import create_options_engine
import os


def calculate_implied_volatility(
    option_price,
    strike_price,
    spot_price,
    time_to_expiry,
    interest_rate=0.06,
    option_type="call",
):
    """
    Calculate implied volatility for an option
    """
    engine = create_options_engine()
    option_type_code = "CE" if option_type.lower() == "call" else "PE"
    return engine.implied_volatility(
        option_price,
        spot_price,
        strike_price,
        time_to_expiry,
        interest_rate,
        option_type_code,
    )


def calculate_greeks(
    option_price,
    strike_price,
    spot_price,
    time_to_expiry,
    interest_rate=0.06,
    volatility=0.2,
    option_type="call",
):
    """
    Calculate option Greeks (Delta, Gamma, Theta, Vega, Rho)
    """
    engine = create_options_engine()
    option_type_code = "CE" if option_type.lower() == "call" else "PE"
    greeks = engine.calculate_greeks(
        spot_price,
        strike_price,
        time_to_expiry,
        interest_rate,
        volatility,
        option_type_code,
    )
    return greeks.__dict__


def get_option_chain(kite, symbol, expiry_date=None):
    """
    Get option chain for a symbol and expiry date
    """
    engine = create_options_engine()

    if engine.paper_trade:
        # Use mock option chain for paper trading
        spot_price = 18500  # Default spot price for mock
        return engine._mock_option_chain(symbol, spot_price, expiry_date)
    else:
        # Get real option chain
        try:
            spot_ltp = kite.ltp([f"NSE:{symbol}"])
            spot_price = spot_ltp[f"NSE:{symbol}"]["last_price"]

            import asyncio

            return asyncio.run(
                engine.analyze_option_chain(kite, symbol, spot_price, expiry_date)
            )
        except Exception as e:
            print(f"Error fetching option chain: {e}")
            return []


def select_option_strike(spot_price, direction, strategy="default", capital=100000):
    """
    Select appropriate option strike based on spot price, direction and strategy
    """
    engine = create_options_engine()

    # Create mock option chain for strike selection
    option_chain = engine._mock_option_chain("NIFTY", spot_price)

    # Select optimal strikes based on strategy
    result = engine.select_optimal_strikes(option_chain, strategy, direction, capital)

    if result and "primary" in result:
        return {
            "symbol": result["primary"].symbol,
            "strike": result["primary"].strike,
            "option_type": result["primary"].option_type,
            "market_price": result["primary"].market_price,
            "quantity": result.get("quantity", 1),
            "strategy_params": result.get("strategy_params", {}),
            "greeks": result["primary"].greeks,
            "iv": result["primary"].iv,
            "is_mock": result["primary"].is_mock,
        }

    return None


def get_next_expiry_and_atm_option(symbol, spot_price):
    """
    Get the next expiry date and at-the-money option for a symbol
    """
    engine = create_options_engine()

    # Get next expiry
    expiry_date = engine._get_next_expiry()

    # Round spot price to nearest 100 for ATM strike
    atm_strike = round(spot_price / 100) * 100

    # Generate option symbols
    expiry_str = expiry_date.replace("-", "")
    call_option = f"{symbol}{expiry_str}{int(atm_strike)}CE"
    put_option = f"{symbol}{expiry_str}{int(atm_strike)}PE"

    return expiry_date, call_option, put_option


def calculate_option_price(
    spot_price,
    strike_price,
    time_to_expiry,
    volatility=0.2,
    interest_rate=0.06,
    option_type="call",
):
    """
    Calculate theoretical option price using Black-Scholes
    """
    engine = create_options_engine()
    option_type_code = "CE" if option_type.lower() == "call" else "PE"

    return engine.black_scholes_price(
        spot_price,
        strike_price,
        time_to_expiry,
        interest_rate,
        volatility,
        option_type_code,
    )


def analyze_option_strategy(kite, symbol, strategy_type, direction, capital=100000):
    """
    Analyze and recommend option strategy
    """
    engine = create_options_engine()

    try:
        if engine.paper_trade:
            spot_price = 18500  # Mock spot price
        else:
            spot_ltp = kite.ltp([f"NSE:{symbol}"])
            spot_price = spot_ltp[f"NSE:{symbol}"]["last_price"]

        # Get option chain
        import asyncio

        if engine.paper_trade:
            option_chain = engine._mock_option_chain(symbol, spot_price)
        else:
            option_chain = asyncio.run(
                engine.analyze_option_chain(kite, symbol, spot_price)
            )

        # Select optimal strategy
        strategy_result = engine.select_optimal_strikes(
            option_chain, strategy_type, direction, capital
        )

        if strategy_result:
            return {
                "strategy": strategy_type,
                "direction": direction,
                "recommended_option": strategy_result.get("primary"),
                "position_size": strategy_result.get("quantity", 1),
                "risk_metrics": strategy_result.get("risk_metrics", {}),
                "strategy_params": strategy_result.get("strategy_params", {}),
                "total_cost": (
                    strategy_result.get("quantity", 1)
                    * strategy_result.get("primary", {}).market_price
                    if strategy_result.get("primary")
                    else 0
                ),
                "paper_trade": engine.paper_trade,
                "analysis_timestamp": engine._get_next_expiry(),
            }
        else:
            return {
                "error": "No suitable options found for strategy",
                "strategy": strategy_type,
                "direction": direction,
                "paper_trade": engine.paper_trade,
            }

    except Exception as e:
        return {
            "error": str(e),
            "strategy": strategy_type,
            "direction": direction,
            "paper_trade": engine.paper_trade,
        }


def get_options_portfolio_risk(positions):
    """
    Calculate portfolio-level options risk metrics
    """
    if not positions:
        return {
            "total_delta": 0,
            "total_gamma": 0,
            "total_theta": 0,
            "total_vega": 0,
            "portfolio_value": 0,
            "risk_level": "NONE",
        }

    total_delta = sum(pos.get("delta", 0) * pos.get("quantity", 0) for pos in positions)
    total_gamma = sum(pos.get("gamma", 0) * pos.get("quantity", 0) for pos in positions)
    total_theta = sum(pos.get("theta", 0) * pos.get("quantity", 0) for pos in positions)
    total_vega = sum(pos.get("vega", 0) * pos.get("quantity", 0) for pos in positions)
    portfolio_value = sum(pos.get("market_value", 0) for pos in positions)

    # Risk assessment
    if abs(total_delta) > 100 or abs(total_gamma) > 10:
        risk_level = "HIGH"
    elif abs(total_delta) > 50 or abs(total_gamma) > 5:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "total_delta": total_delta,
        "total_gamma": total_gamma,
        "total_theta": total_theta,
        "total_vega": total_vega,
        "portfolio_value": portfolio_value,
        "risk_level": risk_level,
        "delta_neutral": abs(total_delta) < 10,
        "theta_decay_per_day": total_theta,
        "volatility_exposure": total_vega,
    }
