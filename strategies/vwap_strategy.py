"""
VWAP Strategy - Self-contained implementation
Calculates VWAP and generates trading signals without external dependencies
"""


def calculate_simple_atr(candles, period=14):
    """
    Simple ATR calculation without pandas dependency
    """
    if len(candles) < period + 1:
        return 0
    
    true_ranges = []
    for i in range(1, len(candles)):
        high = candles[i]["high"]
        low = candles[i]["low"]
        prev_close = candles[i-1]["close"]
        
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        true_range = max(tr1, tr2, tr3)
        true_ranges.append(true_range)
    
    # Simple moving average of true ranges
    if len(true_ranges) >= period:
        atr = sum(true_ranges[-period:]) / period
    else:
        atr = sum(true_ranges) / len(true_ranges) if true_ranges else 0
    
    return atr


def calculate_simple_quantity(capital, price, risk_pct=0.02):
    """
    Simple quantity calculation without external dependencies
    """
    if price <= 0:
        return 0
    
    # Risk-based position sizing
    risk_amount = capital * risk_pct
    max_quantity_by_risk = int(risk_amount / price)
    
    # Traditional position sizing (10% of capital)
    traditional_quantity = int(capital * 0.1 / price)
    
    # Use the smaller of the two for conservative sizing
    return min(max_quantity_by_risk, traditional_quantity, 1000)  # Cap at 1000 for safety


def calculate_vwap(candles, period=20):
    """
    Calculate Volume Weighted Average Price
    """
    if len(candles) < period:
        period = len(candles)
    
    if period == 0:
        return 0
    
    vwap_sum = 0
    volume_sum = 0
    
    for candle in candles[-period:]:
        # Typical price (HLC/3)
        typical_price = (candle["high"] + candle["low"] + candle["close"]) / 3
        volume = candle.get("volume", 1)  # Default volume if not available
        
        vwap_sum += typical_price * volume
        volume_sum += volume
    
    return vwap_sum / volume_sum if volume_sum > 0 else 0


def get_vwap_signal(candles, vwap_period=20):
    """
    Generate VWAP-based trading signal
    """
    if len(candles) < 5:
        return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
    
    vwap = calculate_vwap(candles, vwap_period)
    current_price = candles[-1]["close"]
    
    # Calculate price deviation from VWAP
    deviation_pct = ((current_price - vwap) / vwap) * 100 if vwap > 0 else 0
    
    # Generate signal based on deviation
    if deviation_pct > 2:  # Price significantly above VWAP
        signal = "SELL"  # Expect reversion
        confidence = min(abs(deviation_pct) / 5, 1.0)  # Higher deviation = higher confidence
    elif deviation_pct < -2:  # Price significantly below VWAP
        signal = "BUY"  # Expect reversion
        confidence = min(abs(deviation_pct) / 5, 1.0)
    else:
        signal = "HOLD"
        confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "vwap": vwap,
        "current_price": current_price,
        "deviation_pct": deviation_pct,
        "reason": f"Price {deviation_pct:.2f}% from VWAP"
    }


def vwap_strategy(symbol, candles, capital):
    """
    VWAP-based trading strategy
    """
    if not candles or len(candles) < 10:
        print(f"[VWAP] Not enough data for {symbol}")
        return None

    # Get VWAP signal
    signal_data = get_vwap_signal(candles)
    
    if signal_data["signal"] == "HOLD" or signal_data["confidence"] < 0.6:
        print(f"[VWAP] No clear signal for {symbol}: {signal_data['reason']}")
        return None

    # Calculate position parameters
    current_price = candles[-1]["close"]
    atr = calculate_simple_atr(candles)
    quantity = calculate_simple_quantity(capital, current_price)
    
    # Determine direction
    direction = "bullish" if signal_data["signal"] == "BUY" else "bearish"
    
    # Calculate stop loss and target based on ATR
    if direction == "bullish":
        stop_loss = current_price - (1.5 * atr)
        target = current_price + (2.0 * atr)
    else:
        stop_loss = current_price + (1.5 * atr)
        target = current_price - (2.0 * atr)

    trade = {
        "symbol": symbol,
        "entry_price": current_price,
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "quantity": quantity,
        "direction": direction,
        "strategy": "VWAP",
        "confidence": signal_data["confidence"],
        "vwap": signal_data["vwap"],
        "deviation_pct": signal_data["deviation_pct"],
        "atr": atr
    }

    print(f"[VWAP] Trade signal for {symbol}: {direction} (confidence: {signal_data['confidence']:.2f})")
    return trade


def vwap_exit_strategy(trade, current_candles):
    """
    VWAP-based exit strategy
    """
    if not current_candles:
        return False, "No current data"
    
    current_price = current_candles[-1]["close"]
    entry_price = trade["entry_price"]
    direction = trade["direction"]
    
    # Check stop loss and target
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
    
    # Check VWAP reversal
    signal_data = get_vwap_signal(current_candles)
    if signal_data["confidence"] > 0.7:
        if (direction == "bullish" and signal_data["signal"] == "SELL") or \
           (direction == "bearish" and signal_data["signal"] == "BUY"):
            return True, "VWAP reversal signal"
    
    return False, "Hold position"
