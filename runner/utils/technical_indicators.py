"""
Technical indicators module for trading strategies.
Now uses the enterprise TechnicalEngine with paper trade support.
"""

from runner.indicators.technical_engine import create_technical_engine
import os


def calculate_rsi(data, period=14):
    """
    Calculate Relative Strength Index (RSI)
    """
    engine = create_technical_engine()
    result = engine.calculate_adaptive_rsi(data, period)
    return result.value


def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate Moving Average Convergence Divergence (MACD)
    """
    engine = create_technical_engine()
    result = engine.calculate_macd(data, fast_period, slow_period, signal_period)
    return result.metadata['macd'], result.metadata['signal'], result.metadata['histogram']


def calculate_bollinger_bands(data, period=20, std_dev=2):
    """
    Calculate Bollinger Bands
    """
    engine = create_technical_engine()
    result = engine.calculate_bollinger_bands(data, period, std_dev)
    return result.metadata['upper_band'], result.value, result.metadata['lower_band']


def calculate_moving_average(data, period=20, ma_type="simple"):
    """
    Calculate Moving Average (simplified)
    """
    # For compatibility, using bollinger bands middle line as SMA
    engine = create_technical_engine()
    result = engine.calculate_bollinger_bands(data, period, 1)
    return result.value


def calculate_vwap(data):
    """
    Calculate Volume Weighted Average Price (VWAP)
    """
    engine = create_technical_engine()
    result = engine.calculate_vwap_advanced(data)
    return result.value


# Additional helper functions for backward compatibility
def calculate_atr(data, period=14):
    """
    Calculate Average True Range (ATR)
    """
    engine = create_technical_engine()
    result = engine.calculate_smart_atr(data, period)
    return result.value


def get_technical_signals(data, strategy='comprehensive'):
    """
    Get comprehensive technical signals
    """
    engine = create_technical_engine()
    
    signals = {
        'vwap': engine.calculate_vwap_advanced(data),
        'rsi': engine.calculate_adaptive_rsi(data),
        'atr': engine.calculate_smart_atr(data),
        'macd': engine.calculate_macd(data),
        'bollinger': engine.calculate_bollinger_bands(data)
    }
    
    # Aggregate signals
    buy_signals = sum(1 for s in signals.values() if s.signal == 'BUY')
    sell_signals = sum(1 for s in signals.values() if s.signal == 'SELL')
    
    if buy_signals > sell_signals:
        overall_signal = 'BUY'
        confidence = buy_signals / len(signals)
    elif sell_signals > buy_signals:
        overall_signal = 'SELL'
        confidence = sell_signals / len(signals)
    else:
        overall_signal = 'HOLD'
        confidence = 0.5
    
    return {
        'overall_signal': overall_signal,
        'confidence': confidence,
        'individual_signals': {k: {'signal': v.signal, 'confidence': v.confidence, 'value': v.value} 
                              for k, v in signals.items()},
        'paper_trade': engine.paper_trade
    }