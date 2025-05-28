"""
Range Reversal Strategy - Enhanced implementation
Identifies range-bound markets and trades reversals at support/resistance levels
"""

from strategies.base_strategy import BaseStrategy


def calculate_support_resistance(candles, lookback=20):
    """
    Calculate support and resistance levels from price data
    """
    if len(candles) < lookback:
        lookback = len(candles)
    
    if lookback < 5:
        return None, None
    
    recent_candles = candles[-lookback:]
    highs = [candle["high"] for candle in recent_candles]
    lows = [candle["low"] for candle in recent_candles]
    
    # Simple support/resistance calculation
    resistance = max(highs)
    support = min(lows)
    
    # Calculate average range
    avg_range = sum(h - l for h, l in zip(highs, lows)) / len(highs)
    
    return support, resistance, avg_range


def is_range_bound_market(candles, lookback=20, range_threshold=0.05):
    """
    Determine if market is range-bound
    """
    if len(candles) < lookback:
        return False
    
    support, resistance, avg_range = calculate_support_resistance(candles, lookback)
    if not support or not resistance:
        return False
    
    # Calculate range as percentage of price
    mid_price = (support + resistance) / 2
    range_pct = ((resistance - support) / mid_price) * 100 if mid_price > 0 else 0
    
    # Market is range-bound if range is reasonable (not too tight, not too wide)
    return 2 <= range_pct <= 8


def get_reversal_signal(candles, support, resistance):
    """
    Generate reversal signal based on current price position
    """
    if len(candles) < 3:
        return {"signal": "HOLD", "confidence": 0, "reason": "Insufficient data"}
    
    current_price = candles[-1]["close"]
    prev_price = candles[-2]["close"]
    
    # Calculate distance from support/resistance
    range_size = resistance - support
    buffer = range_size * 0.1  # 10% buffer
    
    # Near resistance - look for reversal down
    if current_price >= (resistance - buffer):
        if prev_price < current_price:  # Price moving up into resistance
            signal = "SELL"
            confidence = min(0.9, (current_price - (resistance - buffer)) / buffer)
        else:
            signal = "HOLD"
            confidence = 0.3
    # Near support - look for reversal up
    elif current_price <= (support + buffer):
        if prev_price > current_price:  # Price moving down into support
            signal = "BUY"
            confidence = min(0.9, ((support + buffer) - current_price) / buffer)
        else:
            signal = "HOLD"
            confidence = 0.3
    else:
        signal = "HOLD"
        confidence = 0.5
    
    return {
        "signal": signal,
        "confidence": confidence,
        "support": support,
        "resistance": resistance,
        "current_price": current_price,
        "reason": f"Price at {current_price:.2f}, S/R: {support:.2f}/{resistance:.2f}"
    }


class RangeReversalStrategy(BaseStrategy):
    def __init__(self, kite, logger):
        super().__init__(kite, logger)
        self.traded_symbols = set()
        self.position_count = 0
        self.max_positions = 3

    def find_trade_opportunities(self, market_data):
        """
        Find range reversal trade opportunities
        """
        trades = []
        
        if self.position_count >= self.max_positions:
            self.logger.log_event("[RANGE_REVERSAL] Maximum positions reached")
            return trades
        
        # Default symbols to analyze if no market data provided
        symbols_to_analyze = ["NIFTY", "BANKNIFTY", "SENSEX"]
        
        if isinstance(market_data, dict) and "symbols" in market_data:
            symbols_to_analyze = market_data["symbols"]
        
        for symbol in symbols_to_analyze:
            if symbol in self.traded_symbols:
                continue
                
            # Get candle data (in real implementation, this would come from kite)
            candles = self._get_symbol_candles(symbol, market_data)
            
            if not candles or len(candles) < 20:
                continue
            
            # Check if market is range-bound
            if not is_range_bound_market(candles):
                continue
            
            # Calculate support/resistance
            support, resistance, avg_range = calculate_support_resistance(candles)
            if not support or not resistance:
                continue
            
            # Get reversal signal
            signal_data = get_reversal_signal(candles, support, resistance)
            
            if signal_data["signal"] == "HOLD" or signal_data["confidence"] < 0.6:
                continue
            
            # Create trade
            trade = self._create_trade(symbol, candles, signal_data)
            if trade:
                trades.append(trade)
                self.traded_symbols.add(symbol)
                self.position_count += 1
                self.logger.log_event(f"[RANGE_REVERSAL] Trade opportunity: {trade}")
                
                # Limit to one trade per scan
                break
        
        return trades

    def _get_symbol_candles(self, symbol, market_data):
        """
        Get candle data for symbol (placeholder implementation)
        """
        # In real implementation, this would fetch from kite
        # For now, return mock data or extract from market_data
        if isinstance(market_data, dict) and "candles" in market_data:
            return market_data["candles"].get(symbol, [])
        
        # Mock candle data for testing
        import random
        base_price = 17500 if "NIFTY" in symbol else 45000
        candles = []
        
        for i in range(25):
            # Generate range-bound price action
            price_variation = random.uniform(-0.02, 0.02)  # 2% variation
            open_price = base_price * (1 + price_variation)
            close_price = open_price * (1 + random.uniform(-0.01, 0.01))
            high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.005))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.005))
            
            candles.append({
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": random.randint(100000, 500000)
            })
        
        return candles

    def _create_trade(self, symbol, candles, signal_data):
        """
        Create trade based on signal
        """
        current_price = candles[-1]["close"]
        support = signal_data["support"]
        resistance = signal_data["resistance"]
        direction = "bullish" if signal_data["signal"] == "BUY" else "bearish"
        
        # Calculate position size (simple implementation)
        capital = 100000  # Default capital
        risk_pct = 0.02
        
        if direction == "bullish":
            stop_loss = support * 0.995  # Slightly below support
            target = resistance * 0.995   # Near resistance
        else:
            stop_loss = resistance * 1.005  # Slightly above resistance
            target = support * 1.005       # Near support
        
        # Calculate quantity based on risk
        risk_amount = capital * risk_pct
        price_risk = abs(current_price - stop_loss)
        quantity = int(risk_amount / price_risk) if price_risk > 0 else 50
        quantity = min(quantity, 200)  # Cap quantity
        
        # Determine option symbol (simplified)
        if "NIFTY" in symbol:
            strike = int(current_price / 50) * 50  # Round to nearest 50
            option_type = "CE" if direction == "bullish" else "PE"
            option_symbol = f"NIFTY24DEC{strike}{option_type}"
        else:
            option_symbol = symbol
        
        trade = {
            "symbol": option_symbol,
            "entry_price": current_price,
            "quantity": quantity,
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "strategy": "Range_Reversal",
            "type": "OPTIONS" if "CE" in option_symbol or "PE" in option_symbol else "EQUITY",
            "direction": direction,
            "confidence": signal_data["confidence"],
            "support": support,
            "resistance": resistance
        }
        
        return trade

    def should_exit_trade(self, trade):
        """
        Determine if trade should be exited
        """
        # In real implementation, would check current price against stop/target
        # For now, simple time-based exit or random exit
        import random
        
        # 10% chance of exit on each check (placeholder)
        if random.random() < 0.1:
            self.position_count = max(0, self.position_count - 1)
            if trade["symbol"].split("24")[0] in self.traded_symbols:
                self.traded_symbols.remove(trade["symbol"].split("24")[0])
            return True
        
        return False


def range_reversal_strategy(symbol, candles, capital=100000):
    """
    Standalone range reversal strategy function
    """
    if not candles or len(candles) < 20:
        print(f"[RANGE_REVERSAL] Not enough data for {symbol}")
        return None
    
    # Check if range-bound
    if not is_range_bound_market(candles):
        print(f"[RANGE_REVERSAL] {symbol} not in range-bound market")
        return None
    
    # Get support/resistance
    support, resistance, avg_range = calculate_support_resistance(candles)
    if not support or not resistance:
        return None
    
    # Get signal
    signal_data = get_reversal_signal(candles, support, resistance)
    
    if signal_data["signal"] == "HOLD" or signal_data["confidence"] < 0.6:
        print(f"[RANGE_REVERSAL] No clear signal for {symbol}: {signal_data['reason']}")
        return None
    
    # Create trade
    current_price = candles[-1]["close"]
    direction = "bullish" if signal_data["signal"] == "BUY" else "bearish"
    
    if direction == "bullish":
        stop_loss = support * 0.995
        target = resistance * 0.995
    else:
        stop_loss = resistance * 1.005
        target = support * 1.005
    
    # Calculate quantity
    risk_pct = 0.02
    risk_amount = capital * risk_pct
    price_risk = abs(current_price - stop_loss)
    quantity = int(risk_amount / price_risk) if price_risk > 0 else 50
    quantity = min(quantity, 200)
    
    trade = {
        "symbol": symbol,
        "entry_price": current_price,
        "stop_loss": round(stop_loss, 2),
        "target": round(target, 2),
        "quantity": quantity,
        "direction": direction,
        "strategy": "Range_Reversal",
        "confidence": signal_data["confidence"],
        "support": support,
        "resistance": resistance
    }
    
    print(f"[RANGE_REVERSAL] Trade signal for {symbol}: {direction} (confidence: {signal_data['confidence']:.2f})")
    return trade
