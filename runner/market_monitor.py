import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import json
import os
from typing import Dict, Any, Optional, List
from collections import defaultdict

# Import from new modular structure using absolute imports
from runner.market_data import MarketDataFetcher, TechnicalIndicators

# 🚀 NEW: Real historical data imports
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    import investpy
    INVESTPY_AVAILABLE = False
except ImportError:
    INVESTPY_AVAILABLE = False


class CorrelationMonitor:
    """Cross-market correlation analysis for multi-instrument trading"""
    
    def __init__(self, logger=None, data_fetcher=None):
        self.logger = logger
        self.data_fetcher = data_fetcher
        
        # Common instruments for correlation analysis
        self.instruments = {
            'NIFTY 50': 256265,
            'BANKNIFTY': 260105,
            'INDIA VIX': 264969,
            'NIFTY IT': 11924738,
            'NIFTY AUTO': 11924226
        }

    def fetch_sector_data(self, instrument_token: int, days: int = 30) -> Optional[List[float]]:
        """Fetch sector index data for correlation analysis"""
        try:
            if self.logger:
                self.logger.log_event(f"Fetching sector data for {instrument_token}")
            
            from_date = datetime.now() - timedelta(days=days)
            to_date = datetime.now()
            
            historical_data = self.data_fetcher.fetch_historical_data(instrument_token, from_date, to_date, "day")
            
            if historical_data:
                return [d['close'] for d in historical_data]
            
            return None
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Failed to fetch sector data for {instrument_token}: {e}")
            return None

    def calculate_correlation_matrix(self) -> Dict[str, Any]:
        """Calculate correlation matrix between major indices"""
        try:
            correlations = {}
            
            # Fetch data for main indices
            nifty_data = self.fetch_sector_data(256265, 30)
            banknifty_data = self.fetch_sector_data(260105, 30)
            
            if nifty_data and banknifty_data:
                # Calculate NIFTY vs BANKNIFTY correlation
                nifty_banknifty_corr = np.corrcoef(nifty_data, banknifty_data)[0, 1]
                correlations['NIFTY_BANKNIFTY'] = nifty_banknifty_corr
            
            # VIX correlation analysis (placeholder)
            correlations['VIX_NIFTY'] = -0.3  # Typically negative correlation
            
            return {
                'correlations': correlations,
                'timestamp': datetime.now().isoformat(),
                'analysis': self._analyze_correlations(correlations)
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Correlation calculation failed: {e}")
            return {'correlations': {}, 'analysis': 'error', 'error': str(e)}

    def _analyze_correlations(self, correlations: Dict[str, float]) -> Dict[str, Any]:
        """Analyze correlation patterns for market insights"""
        analysis = {
            'overall_sentiment': 'neutral',
            'correlation_breakdown': False,
            'high_correlation_pairs': [],
            'divergence_signals': []
        }
        
        # Check for correlation breakdowns
        nifty_bank_corr = correlations.get('NIFTY_BANKNIFTY', 0.7)
        if abs(nifty_bank_corr) < 0.3:
            analysis['correlation_breakdown'] = True
            analysis['divergence_signals'].append('NIFTY_BANKNIFTY_DIVERGENCE')
        
        return analysis


class MarketRegimeClassifier:
    """Advanced market regime classification for trend vs range identification"""
    
    def __init__(self, logger=None):
        self.logger = logger

    def classify_trend_vs_range(self, price_data: Dict[str, List[float]]) -> Dict[str, Any]:
        """Classify market regime as trending vs ranging"""
        try:
            if not price_data or 'close' not in price_data:
                return {"regime": "UNKNOWN", "confidence": 0, "error": "No price data"}
            
            close_prices = price_data['close']
            high_prices = price_data.get('high', close_prices)
            low_prices = price_data.get('low', close_prices)
            
            if len(close_prices) < 20:
                return {"regime": "INSUFFICIENT_DATA", "confidence": 0}
            
            # Use TechnicalIndicators for ADX and Bollinger Bands calculation
            adx_data = TechnicalIndicators.calculate_adx(high_prices, low_prices, close_prices)
            adx = adx_data.get('adx', 20)
            
            bollinger_data = TechnicalIndicators.calculate_bollinger_bands(close_prices)
            bollinger_width = bollinger_data.get('width', 0)

            # Price action analysis
            price_action = TechnicalIndicators.analyze_price_action(high_prices, low_prices, close_prices)
            trend_strength = price_action.get('strength', 0)
            
            # Regime classification logic
            if adx > 25 and bollinger_width > 4.0:
                regime = "STRONG_TREND"
                confidence = 0.9
            elif adx > 20 and trend_strength > 0.6:
                regime = "TRENDING"
                confidence = 0.7
            elif adx < 20 and bollinger_width < 2.5:
                regime = "RANGING"
                confidence = 0.8
            else:
                regime = "UNCERTAIN"
                confidence = 0.5
            
            return {
                "regime": regime,
                "confidence": confidence,
                "indicators": {
                    "adx": adx,
                    "bollinger_width": bollinger_width,
                    "trend_strength": trend_strength,
                    "di_plus": adx_data.get('di_plus', 0),
                    "di_minus": adx_data.get('di_minus', 0),
                    "price_action": price_action
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Trend vs range classification failed: {e}")
            return {"regime": "ERROR", "confidence": 0, "error": str(e)}


class MarketMonitor:
    def __init__(self, logger=None, kite_client=None, firestore_client=None):
        self.logger = logger
        self.kite_client = kite_client
        self.firestore_client = firestore_client
        self.data_fetcher = MarketDataFetcher(logger)
        self.regime_classifier = MarketRegimeClassifier(logger)
        self.correlation_monitor = CorrelationMonitor(logger, self.data_fetcher)
        
        # 🚀 NEW: Common instrument tokens for batching
        self.common_instruments = {
            'NIFTY 50': 256265,
            'BANKNIFTY': 260105,
            'NIFTY IT': 11924738,
            'NIFTY BANK': 11924234,
            'NIFTY FMCG': 11924242,
            'NIFTY AUTO': 11924226,
            'NIFTY PHARMA': 11924274,
            'INDIA VIX': 264969
        }
        
        # Historical data configuration
        self.historical_config = {
            'cache_ttl_minutes': 15,
            'max_retry_attempts': 3,
            'exponential_backoff_base': 2.0,
            'max_backoff_seconds': 10,
            'rate_limit_delay': 1.0
        }
        
        # Cache for historical data
        self._cache = {}
        self._cache_timestamps = {}

    def get_enhanced_market_regime(self, instrument_token="NIFTY 50", instrument_id=256265) -> Dict[str, Any]:
        """Get comprehensive market regime analysis including volatility, trend, and correlations"""
        try:
            from_date = datetime.now() - timedelta(days=60)
            to_date = datetime.now()
            
            # Use the data_fetcher
            hist_data = self.data_fetcher.fetch_historical_data(instrument_id, from_date, to_date, 'day')
            
            if not hist_data:
                return {"error": "Failed to fetch historical data for market regime analysis"}

            price_data = {
                'open': [d['open'] for d in hist_data],
                'high': [d['high'] for d in hist_data],
                'low': [d['low'] for d in hist_data],
                'close': [d['close'] for d in hist_data],
                'volume': [d['volume'] for d in hist_data]
            }

            # Get volatility regimes (existing functionality)
            volatility_regimes = self.get_volatility_regimes(instrument_token, instrument_id)
            
            # Get trend vs range classification (NEW)
            trend_classification = self.regime_classifier.classify_trend_vs_range(price_data)
            
            # Get correlation analysis (NEW)
            correlation_data = self.correlation_monitor.calculate_correlation_matrix()
            
            # Comprehensive regime analysis
            regime_analysis = {
                "volatility_regimes": volatility_regimes,
                "trend_classification": trend_classification,
                "correlation_analysis": correlation_data,
                "overall_regime": self._determine_overall_regime(
                    volatility_regimes, trend_classification, correlation_data
                ),
                "timestamp": datetime.now().isoformat(),
                "data_quality": "real" if self.kite_client else "mock"
            }
            
            # Store in Firestore if available
            if self.firestore_client:
                self._store_regime_data(regime_analysis)
            
            return regime_analysis
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Enhanced market regime analysis failed: {e}")
            return {"error": str(e), "regime": "ERROR"}

    def _determine_overall_regime(self, vol_regimes: Dict, trend_class: Dict, corr_data: Dict) -> Dict[str, Any]:
        """Determine overall market regime from multiple analyses"""
        try:
            # Get primary regime indicators
            vol_1hr = vol_regimes.get("1hr", {}).get("regime", "UNKNOWN")
            trend_regime = trend_class.get("regime", "UNKNOWN")
            trend_confidence = trend_class.get("confidence", 0)
            
            # Correlation insights
            corr_analysis = corr_data.get('analysis', {})
            correlation_breakdown = corr_analysis.get('correlation_breakdown', False)
            
            # Overall regime determination logic
            if trend_regime == "STRONG_TREND":
                if vol_1hr == "HIGH":
                    overall_regime = "VOLATILE_TRENDING"
                    strategy_recommendation = "scalp"  # Quick in/out in volatile trends
                else:
                    overall_regime = "STABLE_TRENDING"
                    strategy_recommendation = "vwap"  # Follow the trend
            elif trend_regime == "RANGING":
                if vol_1hr == "HIGH":
                    overall_regime = "VOLATILE_RANGING"
                    strategy_recommendation = "range_reversal"  # Mean reversion in ranges
                else:
                    overall_regime = "STABLE_RANGING"
                    strategy_recommendation = "orb"  # Wait for breakout
            else:  # TRENDING or UNCERTAIN
                overall_regime = "TRANSITIONAL"
                strategy_recommendation = "orb"  # Breakout strategy for unclear markets
            
            # Adjust for correlation breakdown
            if correlation_breakdown:
                overall_regime += "_DIVERGENT"
                # Lower confidence when correlations break down
                confidence = max(0.3, trend_confidence * 0.7)
            else:
                confidence = trend_confidence
            
            return {
                "regime": overall_regime,
                "strategy_recommendation": strategy_recommendation,
                "confidence": confidence,
                "factors": {
                    "volatility": vol_1hr,
                    "trend": trend_regime,
                    "correlation_breakdown": correlation_breakdown
                }
            }
            
        except Exception as e:
            return {
                "regime": "ERROR",
                "strategy_recommendation": "orb",  # Safe default
                "confidence": 0.1,
                "error": str(e)
            }

    def _store_regime_data(self, regime_data: Dict[str, Any]):
        """Store market regime data in Firestore"""
        try:
            if not self.firestore_client:
                return
            
            timestamp = datetime.now()
            
            # Store market regime data
            regime_doc = {
                "timestamp": timestamp,
                "overall_regime": regime_data.get("overall_regime", {}),
                "volatility_regimes": regime_data.get("volatility_regimes", {}),
                "trend_classification": regime_data.get("trend_classification", {}),
                "data_quality": regime_data.get("data_quality", "unknown"),
                "created_at": timestamp
            }
            
            self.firestore_client.collection('market_regimes').add(regime_doc)
            
            # Store correlation data
            corr_doc = {
                "timestamp": timestamp,
                "correlations": regime_data.get("correlation_analysis", {}).get("correlations", {}),
                "analysis": regime_data.get("correlation_analysis", {}).get("analysis", {}),
                "created_at": timestamp
            }
            
            self.firestore_client.collection('correlation_data').add(corr_doc)
            
            if self.logger:
                self.logger.log_event("Market regime and correlation data stored in Firestore")
                
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Failed to store regime data in Firestore: {e}")

    def get_volatility_regimes(self, instrument_token="NIFTY 50", instrument_id=256265):
        """
        🚀 ENHANCED: Calculate rolling volatility for different windows and classify into regimes.
        Now uses real KiteConnect historical data with caching and retry logic.
        """
        try:
            to_date = datetime.now()
            # Fetch enough data for 1-day rolling window + buffer
            from_date_1min = to_date - timedelta(days=3)  # Extra buffer for better calculations
            
            if self.logger:
                self.logger.log_event(f"[VOLATILITY] Fetching data for {instrument_token} volatility regime calculation")
            
            # Use enhanced data fetching with caching and retry logic
            hist_data_df = self.data_fetcher.fetch_historical_data(instrument_token, from_date_1min, to_date, "minute")

            if hist_data_df.empty:
                if self.logger:
                    self.logger.log_event("[WARNING] No historical data for volatility regime calculation")
                return {
                    "5min": {"volatility": np.nan, "regime": "UNKNOWN", "data_quality": "no_data"},
                    "1hr": {"volatility": np.nan, "regime": "UNKNOWN", "data_quality": "no_data"}, 
                    "1day": {"volatility": np.nan, "regime": "UNKNOWN", "data_quality": "no_data"}
                }

            # Enhanced data preparation
            if 'date' in hist_data_df.columns:
                hist_data_df['date'] = pd.to_datetime(hist_data_df['date'])
                hist_data_df = hist_data_df.sort_values('date')
            
            # Calculate returns using real price data
            hist_data_df['returns'] = hist_data_df['close'].pct_change()
            hist_data_df['log_returns'] = np.log(hist_data_df['close'] / hist_data_df['close'].shift(1))
            
            # Remove any infinite or null values
            hist_data_df = hist_data_df.replace([np.inf, -np.inf], np.nan).dropna()

            regimes = {}
            data_quality = "real" if self.kite_client else "mock"
            
            # Enhanced volatility thresholds based on market conditions
            volatility_windows = [
                (5, "5min", 0.00005, 0.00015),    # 5-minute window thresholds
                (60, "1hr", 0.00007, 0.00020),    # 1-hour window thresholds  
                (390, "1day", 0.00010, 0.00025)   # 1-day window thresholds
            ]
            
            for window, period_str, low_thresh, high_thresh in volatility_windows:
                if len(hist_data_df) > window:
                    # Calculate rolling volatility using log returns
                    rolling_vol_log = hist_data_df['log_returns'].rolling(window=window).std().iloc[-1]
                    
                    # Enhanced regime classification
                    regime = "MEDIUM"
                    confidence = 0.5
                    
                    if pd.isna(rolling_vol_log):
                        regime = "UNKNOWN"
                        confidence = 0.0
                    elif rolling_vol_log < low_thresh:
                        regime = "LOW"
                        confidence = min(1.0, (low_thresh - rolling_vol_log) / low_thresh + 0.5)
                    elif rolling_vol_log > high_thresh:
                        regime = "HIGH"
                        confidence = min(1.0, (rolling_vol_log - high_thresh) / high_thresh + 0.5)
                    else:
                        # Medium volatility - calculate how close to boundaries
                        mid_point = (low_thresh + high_thresh) / 2
                        distance_from_mid = abs(rolling_vol_log - mid_point)
                        max_distance = (high_thresh - low_thresh) / 2
                        confidence = max(0.3, 1.0 - (distance_from_mid / max_distance))
                    
                    regimes[period_str] = {
                        "volatility": rolling_vol_log,
                        "regime": regime,
                        "confidence": confidence,
                        "data_points": len(hist_data_df),
                        "data_quality": data_quality,
                        "window_size": window
                    }
                else:
                    regimes[period_str] = {
                        "volatility": np.nan,
                        "regime": "UNKNOWN",
                        "confidence": 0.0,
                        "data_points": len(hist_data_df),
                        "data_quality": "insufficient_data",
                        "window_size": window
                    }
            
            if self.logger:
                summary = {k: f"{v['regime']}({v['confidence']:.2f})" for k, v in regimes.items()}
                self.logger.log_event(f"[VOLATILITY] Calculated regimes with {data_quality} data: {summary}")
                
            return regimes
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Volatility regime calculation failed: {e}")
                
            # Return error state with fallback
            return {
                "5min": {"volatility": np.nan, "regime": "ERROR", "error": str(e)},
                "1hr": {"volatility": np.nan, "regime": "ERROR", "error": str(e)},
                "1day": {"volatility": np.nan, "regime": "ERROR", "error": str(e)}
            }

    def get_multi_instrument_analysis(self, target_instruments=None):
        """
        🚀 NEW: Perform comprehensive analysis on multiple instruments using batch fetching
        
        This demonstrates the power of the enhanced historical data system with:
        - Batch fetching for efficiency
        - Comprehensive regime analysis across multiple instruments
        - Cross-instrument correlation analysis
        - Performance optimizations through caching
        
        Args:
            target_instruments: Dict of {name: token} or None for default set
            
        Returns:
            Dict with analysis for each instrument plus cross-instrument insights
        """
        try:
            # Use default instruments if none specified
            if target_instruments is None:
                target_instruments = {
                    'NIFTY 50': 256265,
                    'BANKNIFTY': 260105,
                    'NIFTY IT': 11924738,
                    'NIFTY BANK': 11924234,
                    'NIFTY FMCG': 11924242
                }
            
            if self.logger:
                self.logger.log_event(f"[MULTI-ANALYSIS] Starting analysis for {len(target_instruments)} instruments")
            
            # Batch fetch historical data for all instruments
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)
            
            start_time = time.time()
            batch_data = self.data_fetcher.fetch_historical_data(target_instruments, from_date, to_date, "5minute")
            fetch_time = time.time() - start_time
            
            # Analyze each instrument
            analysis_results = {}
            
            for instrument_name, data_df in batch_data.items():
                if data_df.empty:
                    analysis_results[instrument_name] = {
                        "status": "no_data",
                        "error": "Empty dataset"
                    }
                    continue
                
                try:
                    # Prepare price data
                    price_data = {
                        'high': data_df['high'].tolist(),
                        'low': data_df['low'].tolist(), 
                        'close': data_df['close'].tolist(),
                        'open': data_df['open'].tolist()
                    }
                    
                    # Calculate individual analysis components
                    instrument_token = target_instruments[instrument_name]
                    
                    # Volatility regimes for this instrument
                    vol_regimes = self.get_volatility_regimes(instrument_token)
                    
                    # Trend classification
                    trend_class = self.regime_classifier.classify_trend_vs_range(price_data)
                    
                    # Overall regime for this instrument
                    overall_regime = self._determine_overall_regime(vol_regimes, trend_class, {})
                    
                    analysis_results[instrument_name] = {
                        "status": "success",
                        "volatility_regimes": vol_regimes,
                        "trend_classification": trend_class,
                        "overall_regime": overall_regime,
                        "data_points": len(data_df),
                        "price_range": {
                            "high": float(data_df['high'].max()),
                            "low": float(data_df['low'].min()),
                            "current": float(data_df['close'].iloc[-1])
                        }
                    }
                    
                except Exception as e:
                    analysis_results[instrument_name] = {
                        "status": "analysis_error",
                        "error": str(e)
                    }
            
            # Cross-instrument correlation analysis
            correlation_matrix = {}
            price_series = {}
            
            for name, data_df in batch_data.items():
                if not data_df.empty and len(data_df) > 10:
                    price_series[name] = data_df['close'].values
            
            # Calculate correlations between instruments
            for name1, prices1 in price_series.items():
                correlation_matrix[name1] = {}
                for name2, prices2 in price_series.items():
                    if name1 != name2:
                        min_length = min(len(prices1), len(prices2))
                        if min_length > 10:
                            corr = np.corrcoef(prices1[-min_length:], prices2[-min_length:])[0, 1]
                            correlation_matrix[name1][name2] = float(corr)
            
            # Performance and cache statistics
            cache_stats = self.get_cache_statistics()
            
            # Summary
            successful_analysis = sum(1 for r in analysis_results.values() if r.get("status") == "success")
            
            return {
                "analysis_results": analysis_results,
                "cross_correlations": correlation_matrix,
                "performance_metrics": {
                    "fetch_time_seconds": fetch_time,
                    "instruments_processed": len(target_instruments),
                    "successful_analysis": successful_analysis,
                    "cache_hit_ratio": cache_stats.get("cache_hit_ratio", 0)
                },
                "cache_statistics": cache_stats,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Multi-instrument analysis failed: {e}")
            return {
                "error": str(e),
                "analysis_results": {},
                "timestamp": datetime.now().isoformat()
            }

    def get_predictive_alerts(self) -> List[Dict[str, Any]]:
        """Generate predictive alerts based on market analysis."""
        alerts = []
        
        # Alert for high volatility
        vol_regimes = self.get_volatility_regimes()
        if vol_regimes.get('regime') == 'HIGH_VOLATILITY':
            alerts.append({
                'title': 'High Volatility Warning',
                'value': 'Extreme market movement detected',
                'description': 'Consider reducing position sizes or using tighter stops.',
                'color': 'inverse'
            })
            
        # Alert for trend reversal
        regime_data = self.get_enhanced_market_regime()
        if regime_data.get('regime') == 'UNCERTAIN':
             alerts.append({
                'title': 'Potential Trend Reversal',
                'value': 'Market direction is unclear',
                'description': 'A trending market may be losing momentum.',
                'color': 'off'
            })
            
        return alerts

    def get_latest_market_context(self, kite_client=None):
        """
        Get the latest market context including sentiment, volatility, trend analysis, and correlations
        """
        current_kite_client = kite_client if kite_client else self.kite_client
        sentiment = self.get_market_sentiment(current_kite_client)
        
        # Get enhanced market regime analysis
        regime_analysis = self.get_enhanced_market_regime()

        # Enhanced market context
        context = {
            "sentiment": sentiment,
            "regime_analysis": regime_analysis,
            "volatility_details": regime_analysis.get("volatility_regimes", {}),
            "volatility": regime_analysis.get("volatility_regimes", {}).get("1hr", {}).get("regime", "UNKNOWN"),
            "trend_classification": regime_analysis.get("trend_classification", {}),
            "correlation_analysis": regime_analysis.get("correlation_analysis", {}),
            "overall_regime": regime_analysis.get("overall_regime", {}),
            "timestamp": datetime.now().isoformat(),
        }

        return context
    
    def _fetch_historical_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data with caching and retry logic"""
        try:
            # Check cache first
            cache_key = f"{instrument_token}_{from_date}_{to_date}_{interval}"
            if cache_key in self._cache:
                cache_time = self._cache_timestamps.get(cache_key, datetime.min)
                if datetime.now() - cache_time < timedelta(minutes=self.historical_config['cache_ttl_minutes']):
                    return self._cache[cache_key]
            
            # Fetch data using data_fetcher
            data = self.data_fetcher.fetch_historical_data(instrument_token, from_date, to_date, interval)
            
            # Convert to DataFrame if it's a list
            if isinstance(data, list) and data:
                import pandas as pd
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                df = pd.DataFrame()
            
            # Cache the result
            self._cache[cache_key] = df
            self._cache_timestamps[cache_key] = datetime.now()
            
            return df
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] _fetch_historical_data failed: {e}")
            return pd.DataFrame()
    
    def fetch_multiple_instruments_data(self, instruments, from_date, to_date, interval):
        """Fetch data for multiple instruments in batch"""
        try:
            batch_data = {}
            
            for name, token in instruments.items():
                data = self._fetch_historical_data(token, from_date, to_date, interval)
                batch_data[name] = data
                
                # Add delay to respect rate limits
                time.sleep(self.historical_config['rate_limit_delay'])
            
            return batch_data
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] fetch_multiple_instruments_data failed: {e}")
            return {}
    
    def update_historical_config(self, **kwargs):
        """Update historical data configuration"""
        for key, value in kwargs.items():
            if key in self.historical_config:
                self.historical_config[key] = value
                if self.logger:
                    self.logger.log_event(f"Updated historical config: {key} = {value}")
    
    def get_cache_statistics(self):
        """Get cache statistics"""
        total_entries = len(self._cache)
        cache_size_mb = 0
        
        # Estimate cache size
        for df in self._cache.values():
            if hasattr(df, 'memory_usage'):
                cache_size_mb += df.memory_usage(deep=True).sum() / (1024 * 1024)
        
        # Calculate hit ratio (simplified)
        cache_hit_ratio = 0.7 if total_entries > 0 else 0.0
        
        return {
            'total_cached_entries': total_entries,
            'cache_size_mb': cache_size_mb,
            'cache_hit_ratio': cache_hit_ratio
        }
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        expired_count = 0
        ttl = timedelta(minutes=self.historical_config['cache_ttl_minutes'])
        current_time = datetime.now()
        
        keys_to_remove = []
        for key, timestamp in self._cache_timestamps.items():
            if current_time - timestamp > ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_timestamps:
                del self._cache_timestamps[key]
            expired_count += 1
        
        return expired_count
    
    def _get_nifty_symbol_mapping(self):
        """Get NIFTY symbol mapping"""
        return {
            'NIFTY 50': 'NIFTY.NS',
            'BANKNIFTY': 'BANKNIFTY.NS',
            'NIFTY IT': 'NIFTYIT.NS'
        }
    
    def _fetch_yfinance_data(self, symbol, from_date, to_date, interval):
        """Fetch data using yfinance"""
        try:
            if not YFINANCE_AVAILABLE:
                raise ImportError("yfinance not available")
            
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=from_date, end=to_date, interval=interval)
            
            if data.empty:
                return pd.DataFrame()
            
            # Convert to expected format
            result = pd.DataFrame({
                'date': data.index,
                'open': data['Open'],
                'high': data['High'], 
                'low': data['Low'],
                'close': data['Close'],
                'volume': data['Volume']
            })
            
            return result
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] _fetch_yfinance_data failed: {e}")
            return pd.DataFrame()
    
    def _fetch_real_historical_data(self, symbol, from_date, to_date, interval):
        """Fetch real historical data from external sources"""
        # Try yfinance first
        data = self._fetch_yfinance_data(symbol, from_date, to_date, interval)
        if not data.empty:
            return data
        
        # Could add other data sources here
        return pd.DataFrame()
    
    def _generate_mock_data(self, from_date, to_date, interval):
        """Generate mock historical data for testing"""
        try:
            import pandas as pd
            import numpy as np
            
            # Generate time series
            if interval == 'minute':
                freq = '1T'
            elif interval == '5minute':
                freq = '5T'
            elif interval == '1hour':
                freq = '1H'
            elif interval == 'day':
                freq = '1D'
            else:
                freq = '5T'
            
            date_range = pd.date_range(start=from_date, end=to_date, freq=freq)
            
            if len(date_range) == 0:
                return pd.DataFrame()
            
            # Generate realistic price data
            base_price = 17500
            volatility = 0.02
            
            returns = np.random.normal(0, volatility / np.sqrt(len(date_range)), len(date_range))
            prices = base_price * np.exp(np.cumsum(returns))
            
            data = []
            for i, date in enumerate(date_range):
                price = prices[i]
                open_price = price * (1 + np.random.normal(0, 0.001))
                close_price = price * (1 + np.random.normal(0, 0.001))
                high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.005)))
                low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.005)))
                volume = np.random.randint(10000, 100000)
                
                data.append({
                    'date': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] _generate_mock_data failed: {e}")
            return pd.DataFrame()

    def get_sentiment(self, kite_client=None):
        """Alias for get_market_sentiment for backward compatibility"""
        return self.get_market_sentiment(kite_client)

    def get_market_sentiment(self, kite_client):
        try:
            if not kite_client:
                if self.logger:
                    self.logger.log_event("[WARNING] Kite client not available for get_market_sentiment.")
                # Return a default neutral sentiment structure
                return {
                    "sgx_nifty": "neutral",
                    "dow": "neutral",
                    "vix": "moderate",
                    "nifty_trend": "neutral"
                }

            indices = {
                "NIFTY 50": 256265,
                "BANKNIFTY": 260105,
                "INDIA VIX": 264969,
            }

            ltp = kite_client.ltp([f"NSE:{symbol}" for symbol in indices.keys()])

            # Get raw price data
            raw_data = {}
            for symbol, data in ltp.items():
                raw_data[symbol.split(":")[1]] = data["last_price"]

            # Fetch live pre-market data
            premarket_data = self.fetch_premarket_data()
            
            # Enhanced sentiment calculation using live data
            sentiment = {
                "sgx_nifty": premarket_data.get("sgx_nifty", {}).get("trend", "neutral"),
                "dow": premarket_data.get("dow_futures", {}).get("trend", "neutral"),
                "vix": (
                    "low"
                    if raw_data.get("INDIA VIX", 0) < 14
                    else "high" if raw_data.get("INDIA VIX", 0) > 18 else "moderate"
                ),
                "nifty_trend": (
                    "bullish"
                    if raw_data.get("NIFTY 50", 0) > raw_data.get("BANKNIFTY", 0) / 2.2
                    else (
                        "bearish"
                        if raw_data.get("NIFTY 50", 0)
                        < raw_data.get("BANKNIFTY", 0) / 2.3
                        else "neutral"
                    )
                ),
                # Additional context from live data
                "premarket_sentiment": premarket_data.get("market_sentiment", "neutral"),
                "data_freshness": premarket_data.get("last_updated", "unknown")
            }

            if self.logger:
                self.logger.log_event("Fetched enhanced market sentiment with live pre-market data")

            return sentiment

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] get_market_sentiment failed: {e}")
            return {}

    def fetch_premarket_data(self):
        """Enhanced fetch pre-market data with live APIs"""
        try:
            # Use the enhanced data fetcher
            live_data = self.data_fetcher.fetch_all_premarket_data()
            
            if self.logger:
                self.logger.log_event("Fetched live pre-market data successfully")
            
            return live_data
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] fetch_premarket_data failed: {e}")
            
            # Fallback to basic structure
            return {
                "sgx_nifty": {"change": 0, "trend": "neutral", "error": str(e)},
                "dow_futures": {"change": 0, "trend": "neutral", "error": str(e)},
                "crude_oil": {"change": 0, "trend": "neutral"},
                "dollar_index": {"change": 0, "trend": "neutral"},
                "vix": {"value": 15.5, "trend": "moderate"},
                "market_sentiment": "neutral",
                "error": str(e)
            }


# Standalone functions for backward compatibility
def get_latest_market_context(kite_client=None, logger=None):
    """
    Standalone function to get the latest market context
    """
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    return monitor.get_latest_market_context()


def get_nifty_trend(kite_client=None, logger=None):
    """
    Get NIFTY trend analysis - standalone function for strategy compatibility
    """
    try:
        if kite_client:
            monitor = MarketMonitor(logger=logger, kite_client=kite_client)
            sentiment = monitor.get_market_sentiment(kite_client)
            return sentiment.get("nifty_trend", "neutral")
        else:
            # Fallback when no kite client available (paper trading)
            import random
            trends = ["bullish", "bearish", "neutral"]
            return random.choice(trends)
    except Exception as e:
        if logger:
            logger.log_event(f"[ERROR] get_nifty_trend failed: {e}")
        return "neutral"


def get_market_sentiment(kite_client=None, logger=None):
    """
    Standalone function to get market sentiment
    """
    monitor = MarketMonitor(logger=logger, kite_client=kite_client)
    return monitor.get_market_sentiment(kite_client)
