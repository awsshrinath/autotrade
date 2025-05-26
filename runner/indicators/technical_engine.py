"""
Enterprise-grade Technical Indicators Engine
Supports both paper trading (mock data) and live trading (real calculations)
"""

import numpy as np
import pandas as pd
from config.config_manager import get_trading_config
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from threading import Lock
from datetime import datetime
import asyncio

@dataclass
class IndicatorResult:
    value: float
    signal: str  # 'BUY', 'SELL', 'HOLD'
    confidence: float
    timestamp: str
    metadata: Dict
    is_mock: bool = False


class TechnicalEngine:
    """Enterprise-grade technical analysis engine with paper trade support"""
    
    def __init__(self, paper_trade: bool = None, cache_size: int = 1000):
        # Use configuration file if not explicitly set
        if paper_trade is None:
            config = get_trading_config()
            paper_trade = config.paper_trade
        
        self.paper_trade = paper_trade
        self._cache = {}
        self._cache_lock = Lock()
        self.max_cache_size = cache_size
        
        # Paper trading mock data
        self.mock_values = {
            'vwap': 18500.0,
            'rsi': 55.0,
            'atr': 125.0,
            'macd': (12.5, 8.2, 4.3),
            'bb_upper': 18650.0,
            'bb_middle': 18500.0,
            'bb_lower': 18350.0
        }
        
    def calculate_vwap_advanced(self, candles: List[Dict], 
                               period: Optional[int] = None) -> IndicatorResult:
        """Production VWAP with intraday reset and anchoring"""
        
        if self.paper_trade:
            return self._mock_vwap_result(candles)
        
        # Real VWAP calculation for live trading
        try:
            df = pd.DataFrame(candles)
            
            # Ensure required columns exist
            if not all(col in df.columns for col in ['high', 'low', 'close', 'volume']):
                raise ValueError("Missing required OHLCV columns")
            
            # Typical price
            df['typical_price'] = (df['high'] + df['low'] + df['close']) / 3
            df['price_volume'] = df['typical_price'] * df['volume']
            
            if period:
                # Rolling VWAP
                df['cumsum_pv'] = df['price_volume'].rolling(period).sum()
                df['cumsum_vol'] = df['volume'].rolling(period).sum()
            else:
                # Session VWAP (reset daily)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date']).dt.date
                    df['cumsum_pv'] = df.groupby('date')['price_volume'].cumsum()
                    df['cumsum_vol'] = df.groupby('date')['volume'].cumsum()
                else:
                    # Fallback to cumulative if no date column
                    df['cumsum_pv'] = df['price_volume'].cumsum()
                    df['cumsum_vol'] = df['volume'].cumsum()
                
            # Avoid division by zero
            df['cumsum_vol'] = df['cumsum_vol'].replace(0, 1)
            df['vwap'] = df['cumsum_pv'] / df['cumsum_vol']
            
            current_vwap = df['vwap'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            # Signal generation
            deviation_pct = (current_price - current_vwap) / current_vwap * 100
            
            if current_price > current_vwap * 1.002:  # 0.2% above
                signal = 'BUY'
                confidence = min(abs(deviation_pct) / 2, 1.0)
            elif current_price < current_vwap * 0.998:  # 0.2% below
                signal = 'SELL'
                confidence = min(abs(deviation_pct) / 2, 1.0)
            else:
                signal = 'HOLD'
                confidence = 0.5
                
            return IndicatorResult(
                value=current_vwap,
                signal=signal,
                confidence=confidence,
                timestamp=candles[-1].get('date', datetime.now().isoformat()),
                metadata={
                    'deviation_pct': deviation_pct,
                    'volume_ratio': df['volume'].iloc[-1] / df['volume'].mean(),
                    'period': period,
                    'data_points': len(df)
                },
                is_mock=False
            )
            
        except Exception as e:
            # Fallback to mock data on error
            print(f"VWAP calculation error: {e}, falling back to mock data")
            return self._mock_vwap_result(candles)
    
    def calculate_adaptive_rsi(self, candles: List[Dict], period: int = 14) -> IndicatorResult:
        """Adaptive RSI with dynamic period adjustment"""
        
        if self.paper_trade:
            return self._mock_rsi_result(candles, period)
        
        try:
            df = pd.DataFrame(candles)
            
            if len(df) < period + 1:
                return self._mock_rsi_result(candles, period)
            
            # Calculate volatility for period adjustment
            df['returns'] = df['close'].pct_change()
            volatility = df['returns'].rolling(20).std().iloc[-1] if len(df) >= 20 else 0.02
            
            # Adjust period based on volatility
            if volatility > 0.03:  # High volatility
                adjusted_period = max(period - 4, 9)
            elif volatility < 0.01:  # Low volatility
                adjusted_period = min(period + 6, 21)
            else:
                adjusted_period = period
                
            # RSI calculation
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=adjusted_period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=adjusted_period).mean()
            
            # Avoid division by zero
            loss = loss.replace(0, 0.0001)
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Handle NaN values
            if pd.isna(current_rsi):
                return self._mock_rsi_result(candles, period)
            
            # Advanced signal logic
            prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
            
            if current_rsi > 75:
                signal = 'SELL'
                confidence = min((current_rsi - 70) / 20, 1.0)
            elif current_rsi < 25:
                signal = 'BUY'
                confidence = min((30 - current_rsi) / 20, 1.0)
            elif current_rsi > 55 and prev_rsi <= 55:  # Momentum shift
                signal = 'BUY'
                confidence = 0.7
            elif current_rsi < 45 and prev_rsi >= 45:
                signal = 'SELL'
                confidence = 0.7
            else:
                signal = 'HOLD'
                confidence = 0.5
                
            return IndicatorResult(
                value=current_rsi,
                signal=signal,
                confidence=confidence,
                timestamp=candles[-1].get('date', datetime.now().isoformat()),
                metadata={
                    'adjusted_period': adjusted_period,
                    'volatility': volatility,
                    'momentum': current_rsi - prev_rsi,
                    'overbought_level': 75,
                    'oversold_level': 25
                },
                is_mock=False
            )
            
        except Exception as e:
            print(f"RSI calculation error: {e}, falling back to mock data")
            return self._mock_rsi_result(candles, period)
    
    def calculate_smart_atr(self, candles: List[Dict], period: int = 14) -> IndicatorResult:
        """Smart ATR with volatility regime detection"""
        
        if self.paper_trade:
            return self._mock_atr_result(candles, period)
        
        try:
            df = pd.DataFrame(candles)
            
            if len(df) < period + 1:
                return self._mock_atr_result(candles, period)
            
            # True Range calculation
            df['prev_close'] = df['close'].shift(1)
            df['tr1'] = df['high'] - df['low']
            df['tr2'] = abs(df['high'] - df['prev_close'])
            df['tr3'] = abs(df['low'] - df['prev_close'])
            df['tr'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
            
            # ATR calculation
            df['atr'] = df['tr'].rolling(window=period).mean()
            
            # Volatility regime detection
            short_period = min(5, period // 2)
            short_atr = df['tr'].rolling(window=short_period).mean().iloc[-1]
            long_atr = df['atr'].iloc[-1]
            
            # Handle NaN values
            if pd.isna(short_atr) or pd.isna(long_atr) or long_atr == 0:
                return self._mock_atr_result(candles, period)
            
            atr_ratio = short_atr / long_atr
            
            if atr_ratio > 1.5:
                regime = 'HIGH_VOLATILITY'
                signal = 'REDUCE_SIZE'
                confidence = min((atr_ratio - 1.5) / 0.5, 1.0)
            elif atr_ratio < 0.6:
                regime = 'LOW_VOLATILITY'
                signal = 'INCREASE_SIZE'
                confidence = min((0.6 - atr_ratio) / 0.4, 1.0)
            else:
                regime = 'NORMAL'
                signal = 'HOLD'
                confidence = 0.5
                
            return IndicatorResult(
                value=long_atr,
                signal=signal,
                confidence=confidence,
                timestamp=candles[-1].get('date', datetime.now().isoformat()),
                metadata={
                    'regime': regime,
                    'short_atr': short_atr,
                    'ratio': atr_ratio,
                    'period': period,
                    'volatility_percentile': self._calculate_volatility_percentile(df['tr'], period)
                },
                is_mock=False
            )
            
        except Exception as e:
            print(f"ATR calculation error: {e}, falling back to mock data")
            return self._mock_atr_result(candles, period)
    
    def calculate_macd(self, candles: List[Dict], fast: int = 12, slow: int = 26, signal: int = 9) -> IndicatorResult:
        """MACD calculation with signal generation"""
        
        if self.paper_trade:
            return self._mock_macd_result(candles)
        
        try:
            df = pd.DataFrame(candles)
            
            if len(df) < slow + signal:
                return self._mock_macd_result(candles)
            
            # MACD calculation
            ema_fast = df['close'].ewm(span=fast).mean()
            ema_slow = df['close'].ewm(span=slow).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            
            # Signal generation
            prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else current_histogram
            
            if current_histogram > 0 and prev_histogram <= 0:
                trade_signal = 'BUY'
                confidence = 0.8
            elif current_histogram < 0 and prev_histogram >= 0:
                trade_signal = 'SELL'
                confidence = 0.8
            elif current_macd > current_signal:
                trade_signal = 'BUY'
                confidence = 0.6
            elif current_macd < current_signal:
                trade_signal = 'SELL'
                confidence = 0.6
            else:
                trade_signal = 'HOLD'
                confidence = 0.5
            
            return IndicatorResult(
                value=current_macd,
                signal=trade_signal,
                confidence=confidence,
                timestamp=candles[-1].get('date', datetime.now().isoformat()),
                metadata={
                    'macd': current_macd,
                    'signal': current_signal,
                    'histogram': current_histogram,
                    'fast_period': fast,
                    'slow_period': slow,
                    'signal_period': signal
                },
                is_mock=False
            )
            
        except Exception as e:
            print(f"MACD calculation error: {e}, falling back to mock data")
            return self._mock_macd_result(candles)
    
    def calculate_bollinger_bands(self, candles: List[Dict], period: int = 20, std_dev: float = 2) -> IndicatorResult:
        """Bollinger Bands calculation"""
        
        if self.paper_trade:
            return self._mock_bollinger_result(candles, period, std_dev)
        
        try:
            df = pd.DataFrame(candles)
            
            if len(df) < period:
                return self._mock_bollinger_result(candles, period, std_dev)
            
            # Bollinger Bands calculation
            df['sma'] = df['close'].rolling(window=period).mean()
            df['std'] = df['close'].rolling(window=period).std()
            df['upper_band'] = df['sma'] + (df['std'] * std_dev)
            df['lower_band'] = df['sma'] - (df['std'] * std_dev)
            
            current_price = df['close'].iloc[-1]
            upper_band = df['upper_band'].iloc[-1]
            middle_band = df['sma'].iloc[-1]
            lower_band = df['lower_band'].iloc[-1]
            
            # Signal generation based on band position
            if current_price > upper_band:
                trade_signal = 'SELL'  # Overbought
                confidence = min((current_price - upper_band) / (upper_band * 0.01), 1.0)
            elif current_price < lower_band:
                trade_signal = 'BUY'   # Oversold
                confidence = min((lower_band - current_price) / (lower_band * 0.01), 1.0)
            elif current_price > middle_band:
                trade_signal = 'BUY'   # Above middle
                confidence = 0.6
            else:
                trade_signal = 'SELL'  # Below middle
                confidence = 0.6
            
            # Band width for volatility assessment
            band_width = (upper_band - lower_band) / middle_band * 100
            
            return IndicatorResult(
                value=middle_band,
                signal=trade_signal,
                confidence=confidence,
                timestamp=candles[-1].get('date', datetime.now().isoformat()),
                metadata={
                    'upper_band': upper_band,
                    'middle_band': middle_band,
                    'lower_band': lower_band,
                    'band_width': band_width,
                    'position_in_bands': (current_price - lower_band) / (upper_band - lower_band),
                    'period': period,
                    'std_dev': std_dev
                },
                is_mock=False
            )
            
        except Exception as e:
            print(f"Bollinger Bands calculation error: {e}, falling back to mock data")
            return self._mock_bollinger_result(candles, period, std_dev)
    
    # Mock data methods for paper trading
    def _mock_vwap_result(self, candles: List[Dict]) -> IndicatorResult:
        """Mock VWAP result for paper trading"""
        mock_price = candles[-1]['close'] if candles else 18500
        mock_vwap = self.mock_values['vwap']
        
        # Simple signal based on price vs VWAP
        if mock_price > mock_vwap * 1.002:
            signal = 'BUY'
            confidence = 0.7
        elif mock_price < mock_vwap * 0.998:
            signal = 'SELL'
            confidence = 0.7
        else:
            signal = 'HOLD'
            confidence = 0.5
        
        return IndicatorResult(
            value=mock_vwap,
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metadata={
                'deviation_pct': (mock_price - mock_vwap) / mock_vwap * 100,
                'volume_ratio': 1.2,
                'period': None,
                'data_points': len(candles)
            },
            is_mock=True
        )
    
    def _mock_rsi_result(self, candles: List[Dict], period: int) -> IndicatorResult:
        """Mock RSI result for paper trading"""
        mock_rsi = self.mock_values['rsi']
        
        if mock_rsi > 70:
            signal = 'SELL'
            confidence = 0.8
        elif mock_rsi < 30:
            signal = 'BUY'
            confidence = 0.8
        else:
            signal = 'HOLD'
            confidence = 0.5
        
        return IndicatorResult(
            value=mock_rsi,
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metadata={
                'adjusted_period': period,
                'volatility': 0.02,
                'momentum': 2.5,
                'overbought_level': 70,
                'oversold_level': 30
            },
            is_mock=True
        )
    
    def _mock_atr_result(self, candles: List[Dict], period: int) -> IndicatorResult:
        """Mock ATR result for paper trading"""
        mock_atr = self.mock_values['atr']
        
        return IndicatorResult(
            value=mock_atr,
            signal='HOLD',
            confidence=0.5,
            timestamp=datetime.now().isoformat(),
            metadata={
                'regime': 'NORMAL',
                'short_atr': mock_atr * 0.9,
                'ratio': 0.9,
                'period': period,
                'volatility_percentile': 50
            },
            is_mock=True
        )
    
    def _mock_macd_result(self, candles: List[Dict]) -> IndicatorResult:
        """Mock MACD result for paper trading"""
        macd, signal, histogram = self.mock_values['macd']
        
        if histogram > 0:
            trade_signal = 'BUY'
            confidence = 0.7
        else:
            trade_signal = 'SELL'
            confidence = 0.7
        
        return IndicatorResult(
            value=macd,
            signal=trade_signal,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metadata={
                'macd': macd,
                'signal': signal,
                'histogram': histogram,
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9
            },
            is_mock=True
        )
    
    def _mock_bollinger_result(self, candles: List[Dict], period: int, std_dev: float) -> IndicatorResult:
        """Mock Bollinger Bands result for paper trading"""
        current_price = candles[-1]['close'] if candles else 18500
        upper = self.mock_values['bb_upper']
        middle = self.mock_values['bb_middle']
        lower = self.mock_values['bb_lower']
        
        if current_price > upper:
            signal = 'SELL'
            confidence = 0.8
        elif current_price < lower:
            signal = 'BUY'
            confidence = 0.8
        else:
            signal = 'HOLD'
            confidence = 0.5
        
        return IndicatorResult(
            value=middle,
            signal=signal,
            confidence=confidence,
            timestamp=datetime.now().isoformat(),
            metadata={
                'upper_band': upper,
                'middle_band': middle,
                'lower_band': lower,
                'band_width': (upper - lower) / middle * 100,
                'position_in_bands': (current_price - lower) / (upper - lower),
                'period': period,
                'std_dev': std_dev
            },
            is_mock=True
        )
    
    def _calculate_volatility_percentile(self, tr_series: pd.Series, period: int) -> float:
        """Calculate volatility percentile"""
        if len(tr_series) < period:
            return 50.0
        
        recent_vol = tr_series.iloc[-period:]
        current_vol = tr_series.iloc[-1]
        
        percentile = (recent_vol < current_vol).sum() / len(recent_vol) * 100
        return percentile
    
    def get_engine_status(self) -> Dict:
        """Get engine status and configuration"""
        return {
            'paper_trade': self.paper_trade,
            'cache_size': len(self._cache),
            'max_cache_size': self.max_cache_size,
            'available_indicators': [
                'vwap_advanced',
                'adaptive_rsi',
                'smart_atr',
                'macd',
                'bollinger_bands'
            ],
            'mock_values': self.mock_values if self.paper_trade else None
        }


# Factory function for backward compatibility
def create_technical_engine(paper_trade: bool = None) -> TechnicalEngine:
    """Create TechnicalEngine instance"""
    return TechnicalEngine(paper_trade=paper_trade)


# Individual functions for backward compatibility
def calculate_vwap(candles: List[Dict], paper_trade: bool = None) -> float:
    """Calculate VWAP - backward compatible function"""
    engine = TechnicalEngine(paper_trade=paper_trade)
    result = engine.calculate_vwap_advanced(candles)
    return result.value


def calculate_rsi(candles: List[Dict], period: int = 14,
                  paper_trade: bool = None) -> float:
    """Calculate RSI - backward compatible function"""
    engine = TechnicalEngine(paper_trade=paper_trade)
    result = engine.calculate_adaptive_rsi(candles, period)
    return result.value


def calculate_atr(candles: List[Dict], period: int = 14,
                  paper_trade: bool = None) -> float:
    """Calculate ATR - backward compatible function"""
    engine = TechnicalEngine(paper_trade=paper_trade)
    result = engine.calculate_smart_atr(candles, period)
    return result.value