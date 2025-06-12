"""
Scalp Strategy - Self-contained implementation
Quick scalping strategy for options trading without external dependencies
"""

from runner.market_monitor import get_nifty_trend


def calculate_simple_atr_scalp(candles, period=10):
    """
    Simple ATR calculation for scalping (shorter period)
    """
    if len(candles) < 2:
        return 10  # Default ATR for options
    
    true_ranges = []
    for i in range(1, min(len(candles), period + 1)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = max(tr1, tr2, tr3)
        true_ranges.append(true_range)
    
    return sum(true_ranges) / len(true_ranges) if true_ranges else 10


def calculate_scalp_quantity(capital, price, risk_pct=0.01):
    """
    Calculate quantity for scalping with lower risk
    """
    if price <= 0:
        return 0
    
    # Conservative position sizing for scalping
    risk_amount = capital * risk_pct  # 1% risk for scalping
    max_quantity_by_risk = int(risk_amount / price)
    
    # Scalping typically uses smaller position sizes
    scalp_quantity = int(capital * 0.05 / price)  # 5% of capital
    
    # Use smaller of the two, with reasonable limits for options
    quantity = min(max_quantity_by_risk, scalp_quantity)
    return max(25, min(quantity, 500))  # Between 25 and 500 lots


def pick_simple_strike(index_name, direction, current_price=None, premium_range=(80, 150)):
    """
    Simple strike picker without external dependencies
    """
    if not current_price:
        # Default prices for different indices
        if "NIFTY" in index_name.upper():
            current_price = 17500
        elif "BANK" in index_name.upper():
            current_price = 45000
        else:
            current_price = 17500
    
    # Calculate ATM strike
    if "NIFTY" in index_name.upper():
        strike_interval = 50
        atm_strike = round(current_price / strike_interval) * strike_interval
    else:
        strike_interval = 100
        atm_strike = round(current_price / strike_interval) * strike_interval
    
    # Select strike based on direction
    if direction == "bullish":
        # Slightly OTM call
        selected_strike = atm_strike + strike_interval
        option_type = "CE"
    else:
        # Slightly OTM put
        selected_strike = atm_strike - strike_interval
        option_type = "PE"
    
    # Generate option symbol (simplified)
    symbol = f"{index_name.upper()}24DEC{selected_strike}{option_type}"
    
    # Estimate premium (simplified)
    import random
    estimated_premium = random.uniform(premium_range[0], premium_range[1])
    
    # Generate mock candle data
    candles = []
    for i in range(15):
        base = estimated_premium * (1 + random.uniform(-0.1, 0.1))
        candles.append({
            "high": base * 1.02,
            "low": base * 0.98,
            "close": base,
            "volume": random.randint(1000, 5000)
        })
    
    return {
        "symbol": symbol,
        "ltp": round(estimated_premium, 2),
        "strike": selected_strike,
        "option_type": option_type,
        "candles": candles
    }


def get_scalp_signal(candles, trend):
    """
    Generate scalping signal based on recent price action
    """
    if len(candles) < 3:
        return {"signal": "HOLD", "confidence": 0.5, "reason": "Insufficient data"}
    
    # Get recent prices
    current_price = candles[-1]["close"]
    prev_price = candles[-2]["close"]
    prev2_price = candles[-3]["close"]
    
    # Calculate momentum
    momentum = (current_price - prev2_price) / prev2_price if prev2_price > 0 else 0
    recent_change = (current_price - prev_price) / prev_price if prev_price > 0 else 0
    
    # Scalping signals based on momentum and trend alignment
    if trend == "bullish":
        if momentum > 0.02 and recent_change > 0.01:  # Strong upward momentum
            signal = "BUY"
            confidence = min(0.9, abs(momentum) * 10)
        elif momentum < -0.01:  # Counter-trend
            signal = "HOLD"
            confidence = 0.3
        else:
            signal = "HOLD"
            confidence = 0.5
    else:  # bearish trend
        if momentum < -0.02 and recent_change < -0.01:  # Strong downward momentum
            signal = "BUY"  # Buy puts in bearish trend
            confidence = min(0.9, abs(momentum) * 10)
        elif momentum > 0.01:  # Counter-trend
            signal = "HOLD"
            confidence = 0.3
        else:
            signal = "HOLD"
            confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "momentum": momentum,
        "recent_change": recent_change,
        "reason": f"Momentum: {momentum:.3f}, Recent: {recent_change:.3f}"
    }


def scalp_strategy(index_name, option_chain=None, capital=100000):
    """
    Scalping strategy for quick options trades
    """
    # Get market trend
    try:
        trend = get_nifty_trend()
    except:
        # Fallback if market monitor fails
        import random
        trend = random.choice(["bullish", "bearish", "neutral"])
    
    if trend not in ["bullish", "bearish"]:
        print("[SCALP] No clear trend detected.")
        return None

    # Select strike and get option info
    strike_info = pick_simple_strike(
        index_name=index_name, 
        direction=trend, 
        premium_range=(80, 150)
    )
    
    if not strike_info:
        print("[SCALP] No suitable strike found")
        return None

    symbol = strike_info["symbol"]
    ltp = strike_info["ltp"]
    candles = strike_info["candles"]

    # Get scalping signal
    signal_data = get_scalp_signal(candles, trend)
    
    if signal_data["signal"] == "HOLD" or signal_data["confidence"] < 0.6:
        print(f"[SCALP] No clear scalp signal: {signal_data['reason']}")
        return None

    # Calculate position parameters
    atr = calculate_simple_atr_scalp(candles)
    quantity = calculate_scalp_quantity(capital, ltp)

    # Scalping uses tighter stops and targets
    if trend == "bullish":
        stop_loss = ltp - min(30, atr * 2)  # Tight stop
        target = ltp + min(60, atr * 3)     # Quick target
    else:
        stop_loss = ltp + min(30, atr * 2)
        target = ltp - min(60, atr * 3)

    trade = {
        "symbol": symbol,
        "entry_price": ltp,
        "stop_loss": round(max(stop_loss, 5), 2),  # Minimum 5 rupees
        "target": round(target, 2),
        "quantity": quantity,
        "direction": trend,
        "strategy": "Scalp",
        "confidence": signal_data["confidence"],
        "momentum": signal_data["momentum"],
        "atr": atr,
        "strike": strike_info["strike"],
        "option_type": strike_info["option_type"]
    }

    print(f"[SCALP] Trade signal for {symbol}: {trend} (confidence: {signal_data['confidence']:.2f})")
    return trade


def scalp_exit_strategy(trade, current_candles):
    """
    Scalping exit strategy - quick exits
    """
    if not current_candles:
        return False, "No current data"
    
    current_price = current_candles[-1]["close"]
    entry_price = trade["entry_price"]
    direction = trade["direction"]
    
    # Check stop loss and target (tighter for scalping)
    if direction == "bullish":
        if current_price <= trade["stop_loss"]:
            return True, "Stop loss hit"
        elif current_price >= trade["target"]:
            return True, "Target reached"
    else:
        if current_price >= trade["stop_loss"]:
            return True, "Stop loss hit"
        elif current_price <= trade["target"]:
            return True, "Target reached"
    
    # Time-based exit for scalping (if held too long)
    # In real implementation, would check time elapsed
    import random
    if random.random() < 0.15:  # 15% chance of time-based exit
        return True, "Time-based exit"
    
    # Quick profit taking for scalping
    profit_pct = (current_price - entry_price) / entry_price if entry_price > 0 else 0
    if direction == "bullish" and profit_pct > 0.25:  # 25% profit
        return True, "Quick profit taking"
    elif direction == "bearish" and profit_pct < -0.25:
        return True, "Quick profit taking"
    
    return False, "Hold position"
