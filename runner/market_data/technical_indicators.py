import numpy as np
from typing import Dict, List, Any

class TechnicalIndicators:
    """Advanced technical indicators for trend vs range classification"""
    
    @staticmethod
    def calculate_adx(high_prices: List[float], low_prices: List[float], close_prices: List[float], 
                      period: int = 14) -> Dict[str, float]:
        """Calculate Average Directional Index (ADX)"""
        if len(high_prices) < period + 1:
            return {"adx": np.nan, "di_plus": np.nan, "di_minus": np.nan}
        
        # Convert to numpy arrays
        high = np.array(high_prices)
        low = np.array(low_prices)
        close = np.array(close_prices)
        
        # Calculate True Range (TR)
        tr1 = high[1:] - low[1:]
        tr2 = np.abs(high[1:] - close[:-1])
        tr3 = np.abs(low[1:] - close[:-1])
        tr = np.maximum(tr1, np.maximum(tr2, tr3))
        
        # Calculate Directional Movement
        dm_plus = np.where((high[1:] - high[:-1]) > (low[:-1] - low[1:]), 
                          np.maximum(high[1:] - high[:-1], 0), 0)
        dm_minus = np.where((low[:-1] - low[1:]) > (high[1:] - high[:-1]), 
                           np.maximum(low[:-1] - low[1:], 0), 0)
        
        # Smooth the values
        def wilder_smooth(values, period):
            alpha = 1.0 / period
            smoothed = np.zeros_like(values)
            smoothed[0] = values[0]
            for i in range(1, len(values)):
                smoothed[i] = alpha * values[i] + (1 - alpha) * smoothed[i-1]
            return smoothed
        
        if len(tr) >= period:
            atr = wilder_smooth(tr, period)
            dm_plus_smooth = wilder_smooth(dm_plus, period)
            dm_minus_smooth = wilder_smooth(dm_minus, period)
            
            # Calculate DI+ and DI-
            di_plus = 100 * dm_plus_smooth / atr
            di_minus = 100 * dm_minus_smooth / atr
            
            # Calculate DX
            dx = 100 * np.abs(di_plus - di_minus) / (di_plus + di_minus + 1e-10)
            
            # Calculate ADX
            adx = wilder_smooth(dx, period)
            
            return {
                "adx": adx[-1] if len(adx) > 0 else np.nan,
                "di_plus": di_plus[-1] if len(di_plus) > 0 else np.nan,
                "di_minus": di_minus[-1] if len(di_minus) > 0 else np.nan
            }
        
        return {"adx": np.nan, "di_plus": np.nan, "di_minus": np.nan}
    
    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2) -> Dict[str, float]:
        """Calculate Bollinger Bands"""
        if len(prices) < period:
            return {"upper": np.nan, "middle": np.nan, "lower": np.nan, "width": np.nan}
        
        prices_array = np.array(prices)
        sma = np.mean(prices_array[-period:])
        std = np.std(prices_array[-period:])
        
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        width = (upper - lower) / sma * 100
        
        return {
            "upper": upper,
            "middle": sma,
            "lower": lower,
            "width": width
        }
    
    @staticmethod
    def analyze_price_action(high_prices: List[float], low_prices: List[float], 
                           close_prices: List[float], lookback: int = 10) -> Dict[str, Any]:
        """Analyze price action for trend identification"""
        if len(close_prices) < lookback:
            return {"trend": "unknown", "strength": 0}
        
        highs = np.array(high_prices[-lookback:])
        lows = np.array(low_prices[-lookback:])
        closes = np.array(close_prices[-lookback:])
        
        # Higher highs and higher lows analysis
        higher_highs = sum(1 for i in range(1, len(highs)) if highs[i] > highs[i-1])
        lower_lows = sum(1 for i in range(1, len(lows)) if lows[i] < lows[i-1])
        higher_lows = sum(1 for i in range(1, len(lows)) if lows[i] > lows[i-1])
        lower_highs = sum(1 for i in range(1, len(highs)) if highs[i] < highs[i-1])
        
        # Trend strength calculation
        uptrend_strength = (higher_highs + higher_lows) / (2 * (lookback - 1))
        downtrend_strength = (lower_lows + lower_highs) / (2 * (lookback - 1))
        
        # Determine trend
        if uptrend_strength > 0.6:
            trend = "uptrend"
            strength = uptrend_strength
        elif downtrend_strength > 0.6:
            trend = "downtrend"
            strength = downtrend_strength
        else:
            trend = "sideways"
            strength = max(uptrend_strength, downtrend_strength)
        
        return {
            "trend": trend,
            "strength": strength,
            "higher_highs": higher_highs,
            "higher_lows": higher_lows,
            "lower_highs": lower_highs,
            "lower_lows": lower_lows
        } 