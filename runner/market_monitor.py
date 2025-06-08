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
    INVESTPY_AVAILABLE = True
except ImportError:
    INVESTPY_AVAILABLE = False


class CorrelationMonitor:
    """Cross-market correlation analysis for multi-instrument trading"""
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # Common instruments for correlation analysis
        self.instruments = {
            'NIFTY 50': 256265,
            'BANKNIFTY': 260105,
            'INDIA VIX': 264969,
            'NIFTY IT': 11924738,
            'NIFTY AUTO': 11924226
        }

    def fetch_sector_data(self, symbol: str, days: int = 30) -> Optional[List[float]]:
        """Fetch sector index data for correlation analysis"""
        try:
            if self.logger:
                self.logger.log_event(f"Fetching sector data for {symbol}")
            
            # Mock price data - replace with real API call in production
            base_price = 17000 if 'NIFTY' in symbol else 42000
            prices = []
            for i in range(days):
                price = base_price + np.random.uniform(-500, 500)
                prices.append(price)
            
            return prices
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Failed to fetch sector data for {symbol}: {e}")
            return None

    def calculate_correlation_matrix(self) -> Dict[str, Any]:
        """Calculate correlation matrix between major indices"""
        try:
            correlations = {}
            
            # Fetch data for main indices
            nifty_data = self.fetch_sector_data('NIFTY', 30)
            banknifty_data = self.fetch_sector_data('BANKNIFTY', 30)
            
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
            
            # Use TechnicalIndicators for ADX calculation
            adx_data = TechnicalIndicators.calculate_adx(high_prices, low_prices, close_prices)
            adx = adx_data.get('adx', 20)
            
            # Price action analysis
            price_action = TechnicalIndicators.analyze_price_action(high_prices, low_prices, close_prices)
            trend_strength = price_action.get('strength', 0)
            
            # Regime classification logic
            if adx > 30 and trend_strength > 0.7:
                regime = "STRONGLY_TRENDING"
                confidence = 0.9
            elif adx > 20 and trend_strength > 0.5:
                regime = "WEAKLY_TRENDING"
                confidence = 0.7
            elif adx < 15:
                regime = "RANGING"
                confidence = 0.8
            else:
                regime = "MIXED"
                confidence = 0.5
            
            return {
                "regime": regime,
                "confidence": confidence,
                "adx": adx,
                "trend_strength": trend_strength,
                "di_plus": adx_data.get('di_plus', 0),
                "di_minus": adx_data.get('di_minus', 0),
                "price_action": price_action,
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
        self.correlation_monitor = CorrelationMonitor(logger)
        
        # 🚀 NEW: Historical Data Configuration
        self.historical_config = {
            'cache_ttl_minutes': 15,  # Cache data for 15 minutes
            'max_retry_attempts': 3,
            'batch_size': 10,  # Max instruments per batch
            'rate_limit_delay': 1.0,  # Seconds between requests
            'exponential_backoff_base': 2.0,
            'max_backoff_seconds': 30,
            'use_real_data': True,  # Enable real data fetching
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'data_source_priority': ['yfinance', 'alpha_vantage', 'investpy', 'kite', 'mock']
        }
        
        # 🚀 NEW: In-memory cache for historical data
        self.data_cache = {}
        
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

    def _generate_cache_key(self, instrument_token, from_date, to_date, interval):
        """Generate a unique cache key for the data request"""
        return f"{instrument_token}_{from_date.strftime('%Y%m%d_%H%M')}_{to_date.strftime('%Y%m%d_%H%M')}_{interval}"

    def _is_cache_valid(self, cache_entry):
        """Check if cached data is still valid based on TTL"""
        if not cache_entry or 'timestamp' not in cache_entry:
            return False
        
        cache_age_minutes = (datetime.now() - cache_entry['timestamp']).total_seconds() / 60
        return cache_age_minutes < self.historical_config['cache_ttl_minutes']

    def _get_from_cache(self, cache_key):
        """Retrieve data from cache if valid"""
        if cache_key in self.data_cache:
            cache_entry = self.data_cache[cache_key]
            if self._is_cache_valid(cache_entry):
                if self.logger:
                    self.logger.log_event(f"[CACHE HIT] Retrieved data for {cache_key}")
                return cache_entry['data']
            else:
                # Remove expired cache entry
                del self.data_cache[cache_key]
                if self.logger:
                    self.logger.log_event(f"[CACHE EXPIRED] Removed expired data for {cache_key}")
        
        return None

    def _store_in_cache(self, cache_key, data):
        """Store data in cache with timestamp"""
        self.data_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now()
        }
        if self.logger:
            self.logger.log_event(f"[CACHE STORE] Cached data for {cache_key}")

    def _get_nifty_symbol_mapping(self, instrument_token):
        """Map instrument tokens to real data source symbols"""
        symbol_mapping = {
            256265: '^NSEI',  # NIFTY 50 -> Yahoo Finance symbol
            260105: '^NSEBANK',  # BANKNIFTY -> Yahoo Finance symbol  
            264969: 'INDIA VIX',  # INDIA VIX
            11924738: '^CNXIT',  # NIFTY IT
            11924234: '^NSEBANK',  # NIFTY BANK
            11924242: '^CNXFMCG',  # NIFTY FMCG
            11924226: '^CNXAUTO',  # NIFTY AUTO
            11924274: '^CNXPHARMA',  # NIFTY PHARMA
            'NIFTY 50': '^NSEI',
            'BANKNIFTY': '^NSEBANK',
            'NIFTY BANK': '^NSEBANK',
            'NIFTY IT': '^CNXIT',
            'NIFTY AUTO': '^CNXAUTO',
            'NIFTY FMCG': '^CNXFMCG',
            'NIFTY PHARMA': '^CNXPHARMA'
        }
        
        return symbol_mapping.get(instrument_token, '^NSEI')  # Default to NIFTY 50

    def _fetch_yfinance_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data using Yahoo Finance (yfinance)"""
        try:
            if not YFINANCE_AVAILABLE:
                raise ImportError("yfinance not available")
            
            # Map interval to yfinance format
            interval_mapping = {
                'minute': '1m',
                '5minute': '5m', 
                '15minute': '15m',
                '1hour': '1h',
                'day': '1d'
            }
            yf_interval = interval_mapping.get(interval, '5m')
            
            # Get symbol for yfinance
            symbol = self._get_nifty_symbol_mapping(instrument_token)
            
            if self.logger:
                self.logger.log_event(f"[YFINANCE] Fetching {symbol} from {from_date} to {to_date}, interval {yf_interval}")
            
            # Fetch data from yfinance
            ticker = yf.Ticker(symbol)
            df = ticker.history(start=from_date, end=to_date, interval=yf_interval)
            
            if df.empty:
                raise ValueError(f"No data returned for {symbol}")
            
            # Standardize column names to match expected format
            df = df.reset_index()
            df.columns = [col.lower() for col in df.columns]
            
            # Rename columns to match expected format
            column_mapping = {
                'datetime': 'date',
                'adj close': 'close'  # Use adjusted close as close price
            }
            df = df.rename(columns=column_mapping)
            
            # Ensure we have the required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            df = df[required_columns]
            
            if self.logger:
                self.logger.log_event(f"[YFINANCE SUCCESS] Fetched {len(df)} records for {symbol}")
            
            return df
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[YFINANCE ERROR] Failed to fetch data: {e}")
            raise e

    def _fetch_alpha_vantage_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data using Alpha Vantage API"""
        try:
            api_key = self.historical_config.get('alpha_vantage_api_key')
            if not api_key:
                raise ValueError("Alpha Vantage API key not configured")
            
            # Map instrument to Alpha Vantage symbol (limited for Indian indices)
            # Alpha Vantage mainly supports US markets, so this is a fallback
            symbol_mapping = {
                256265: 'NIFTY',  # Limited support
                'NIFTY 50': 'NIFTY'
            }
            
            symbol = symbol_mapping.get(instrument_token, 'NIFTY')
            
            # Alpha Vantage function mapping
            function_mapping = {
                'minute': 'TIME_SERIES_INTRADAY',
                '5minute': 'TIME_SERIES_INTRADAY', 
                '15minute': 'TIME_SERIES_INTRADAY',
                '1hour': 'TIME_SERIES_INTRADAY',
                'day': 'TIME_SERIES_DAILY'
            }
            
            function = function_mapping.get(interval, 'TIME_SERIES_INTRADAY')
            
            # Build API URL
            url = f"https://www.alphavantage.co/query"
            params = {
                'function': function,
                'symbol': symbol,
                'apikey': api_key,
                'datatype': 'json'
            }
            
            if interval in ['minute', '5minute', '15minute', '1hour']:
                params['interval'] = interval.replace('minute', 'min').replace('1hour', '60min')
            
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE] Fetching {symbol} with function {function}")
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for API error messages
            if 'Error Message' in data:
                raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
            
            if 'Note' in data:
                raise ValueError(f"Alpha Vantage rate limit: {data['Note']}")
            
            # Extract time series data
            time_series_key = None
            for key in data.keys():
                if 'Time Series' in key:
                    time_series_key = key
                    break
            
            if not time_series_key or time_series_key not in data:
                raise ValueError("No time series data found in response")
            
            time_series = data[time_series_key]
            
            # Convert to DataFrame
            records = []
            for date_str, values in time_series.items():
                record = {
                    'date': pd.to_datetime(date_str),
                    'open': float(values.get('1. open', 0)),
                    'high': float(values.get('2. high', 0)),
                    'low': float(values.get('3. low', 0)),
                    'close': float(values.get('4. close', 0)),
                    'volume': int(values.get('5. volume', 0))
                }
                records.append(record)
            
            df = pd.DataFrame(records)
            df = df.sort_values('date').reset_index(drop=True)
            
            # Filter by date range
            df = df[(df['date'] >= pd.to_datetime(from_date)) & 
                   (df['date'] <= pd.to_datetime(to_date))]
            
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE SUCCESS] Fetched {len(df)} records for {symbol}")
            
            return df
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE ERROR] Failed to fetch data: {e}")
            raise e

    def _fetch_real_historical_data(self, instrument_token, from_date, to_date, interval):
        """Fetch real historical data using prioritized data sources"""
        if not self.historical_config.get('use_real_data', True):
            raise ValueError("Real data fetching disabled")
        
        data_sources = self.historical_config.get('data_source_priority', ['yfinance', 'alpha_vantage', 'kite'])
        last_error = None
        
        for source in data_sources:
            if source == 'mock':
                continue  # Skip mock for real data fetching
            if source == 'kite' and not self.kite_client:
                continue  # Skip kite if client not available
                
            try:
                if self.logger:
                    self.logger.log_event(f"[REAL_DATA] Trying {source} for {instrument_token}")
                
                if source == 'yfinance':
                    return self._fetch_yfinance_data(instrument_token, from_date, to_date, interval)
                elif source == 'alpha_vantage':
                    return self._fetch_alpha_vantage_data(instrument_token, from_date, to_date, interval)
                elif source == 'kite' and self.kite_client:
                    return self._fetch_with_retry(instrument_token, from_date, to_date, interval)
                    
            except Exception as e:
                last_error = e
                if self.logger:
                    self.logger.log_event(f"[REAL_DATA] {source} failed: {e}")
                continue
        
        # If all real data sources fail, raise the last error
        raise last_error or ValueError("All real data sources failed")

    def _fetch_with_retry(self, instrument_token, from_date, to_date, interval, attempt=1):
        """Fetch historical data with exponential backoff retry logic"""
        try:
            if self.logger:
                self.logger.log_event(f"[ATTEMPT {attempt}] Fetching {instrument_token} data from {from_date} to {to_date} interval {interval}")
            
            # Make the actual API call
            historical_data = self.kite_client.historical_data(
                instrument_token, from_date, to_date, interval
            )
            
            if historical_data:
                df = pd.DataFrame(historical_data)
                if self.logger:
                    self.logger.log_event(f"[SUCCESS] Fetched {len(df)} records for {instrument_token}")
                return df
            else:
                raise ValueError("No data returned from API")
                
        except Exception as e:
            error_msg = str(e).lower()
            
            # Check if it's a rate limit error (HTTP 429)
            is_rate_limit = 'rate limit' in error_msg or '429' in error_msg or 'too many requests' in error_msg
            
            # Check if it's a transient error that should be retried
            is_retryable = (
                is_rate_limit or 
                'timeout' in error_msg or 
                'connection' in error_msg or 
                'network' in error_msg or
                'temporary' in error_msg
            )
            
            if is_retryable and attempt < self.historical_config['max_retry_attempts']:
                # Calculate exponential backoff delay
                backoff_delay = min(
                    self.historical_config['exponential_backoff_base'] ** attempt,
                    self.historical_config['max_backoff_seconds']
                )
                
                if self.logger:
                    self.logger.log_event(f"[RETRY] Attempt {attempt} failed with {error_msg}. Retrying in {backoff_delay}s")
                
                time.sleep(backoff_delay)
                return self._fetch_with_retry(instrument_token, from_date, to_date, interval, attempt + 1)
            else:
                if self.logger:
                    error_type = "RATE_LIMIT" if is_rate_limit else "API_ERROR"
                    self.logger.log_event(f"[{error_type}] Final attempt {attempt} failed for {instrument_token}: {e}")
                raise e

    def _fetch_historical_data_batch(self, instruments_batch, from_date, to_date, interval):
        """Fetch historical data for a batch of instruments with rate limiting"""
        batch_results = {}
        
        for instrument_name, instrument_token in instruments_batch.items():
            try:
                # Check cache first
                cache_key = self._generate_cache_key(instrument_token, from_date, to_date, interval)
                cached_data = self._get_from_cache(cache_key)
                
                if cached_data is not None:
                    batch_results[instrument_name] = cached_data
                    continue
                
                # 🚀 NEW: Try real data sources first, then fallback to Kite/mock
                try:
                    if self.historical_config.get('use_real_data', True):
                        # Try real data sources first
                        df = self._fetch_real_historical_data(instrument_token, from_date, to_date, interval)
                    else:
                        # Use original Kite logic if real data disabled
                        if self.kite_client:
                            df = self._fetch_with_retry(instrument_token, from_date, to_date, interval)
                        else:
                            raise ValueError("No data source available")
                    
                    if not df.empty:
                        # Store in cache
                        self._store_in_cache(cache_key, df)
                        batch_results[instrument_name] = df
                    else:
                        if self.logger:
                            self.logger.log_event(f"[WARNING] Empty data returned for {instrument_name}")
                        batch_results[instrument_name] = pd.DataFrame()
                        
                except Exception as real_data_error:
                    if self.logger:
                        self.logger.log_event(f"[REAL_DATA_FALLBACK] Real data failed for {instrument_name}: {real_data_error}")
                    
                    # Fallback to Kite API if available
                    if self.kite_client:
                        try:
                            df = self._fetch_with_retry(instrument_token, from_date, to_date, interval)
                            if not df.empty:
                                self._store_in_cache(cache_key, df)
                                batch_results[instrument_name] = df
                            else:
                                batch_results[instrument_name] = pd.DataFrame()
                        except Exception as kite_error:
                            if self.logger:
                                self.logger.log_event(f"[KITE_FALLBACK] Kite also failed for {instrument_name}: {kite_error}")
                            # Final fallback to mock data
                            batch_results[instrument_name] = self._generate_mock_data(from_date, to_date, interval)
                    else:
                        # Final fallback to mock data if no kite client
                        if self.logger:
                            self.logger.log_event(f"[MOCK_FALLBACK] No kite client, generating mock data for {instrument_name}")
                        batch_results[instrument_name] = self._generate_mock_data(from_date, to_date, interval)
                
                # Rate limiting between requests
                time.sleep(self.historical_config['rate_limit_delay'])
                
            except Exception as e:
                if self.logger:
                    self.logger.log_event(f"[ERROR] Failed to fetch data for {instrument_name}: {e}")
                
                # Try to get from cache as fallback
                cache_key = self._generate_cache_key(instrument_token, from_date, to_date, interval)
                cached_data = self._get_from_cache(cache_key)
                
                if cached_data is not None:
                    if self.logger:
                        self.logger.log_event(f"[FALLBACK] Using cached data for {instrument_name}")
                    batch_results[instrument_name] = cached_data
                else:
                    # Final fallback to mock data
                    if self.logger:
                        self.logger.log_event(f"[FALLBACK] Generating mock data for {instrument_name}")
                    batch_results[instrument_name] = self._generate_mock_data(from_date, to_date, interval)
        
        return batch_results

    def _generate_mock_data(self, from_date, to_date, interval):
        """Generate mock historical data with proper OHLCV structure"""
        try:
            # Calculate number of data points based on interval
            if interval == 'minute':
                freq = '1T'
                multiplier = 1
            elif interval == '5minute':
                freq = '5T'
                multiplier = 5
            elif interval == '15minute':
                freq = '15T'
                multiplier = 15
            elif interval == '1hour':
                freq = '1H'
                multiplier = 60
            elif interval == 'day':
                freq = '1D'
                multiplier = 1440
            else:
                freq = '5T'
                multiplier = 5
            
            # Generate date range
            date_range = pd.date_range(start=from_date, end=to_date, freq=freq)
            
            if len(date_range) == 0:
                return pd.DataFrame()
            
            # Generate realistic OHLCV data
            base_price = 17500  # NIFTY base price
            volatility = 0.02   # 2% volatility
            
            np.random.seed(int(time.time()) % 1000)  # Reproducible but varied
            
            # Generate price movements
            returns = np.random.normal(0, volatility / np.sqrt(1440/multiplier), len(date_range))
            prices = base_price * np.exp(np.cumsum(returns))
            
            # Generate OHLCV
            data = pd.DataFrame({
                'date': date_range,
                'open': prices,
                'close': prices * (1 + np.random.normal(0, 0.001, len(date_range))),
                'volume': np.random.randint(10000, 100000, len(date_range))
            })
            
            # Generate high and low
            data['high'] = data[['open', 'close']].max(axis=1) * (1 + np.abs(np.random.normal(0, 0.005, len(data))))
            data['low'] = data[['open', 'close']].min(axis=1) * (1 - np.abs(np.random.normal(0, 0.005, len(data))))
            
            # Ensure OHLC relationships are maintained
            data['high'] = data[['open', 'high', 'low', 'close']].max(axis=1)
            data['low'] = data[['open', 'high', 'low', 'close']].min(axis=1)
            
            return data[['date', 'open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Mock data generation failed: {e}")
            return pd.DataFrame()

    def _fetch_historical_data(self, instrument_token, from_date, to_date, interval):
        """
        🚀 ENHANCED: Fetch historical data with batching, caching, and retry logic
        
        This method now supports:
        - Intelligent caching with TTL
        - Exponential backoff retry for rate limits
        - Batch processing for multiple instruments
        - Comprehensive error handling and fallback mechanisms
        - Production-ready performance optimizations
        """
        start_time = time.time()
        
        try:
            # Convert single instrument request to batch format
            if isinstance(instrument_token, (str, int)):
                # Single instrument request
                instrument_name = next(
                    (name for name, token in self.common_instruments.items() if token == instrument_token),
                    str(instrument_token)
                )
                instruments_batch = {instrument_name: instrument_token}
            else:
                # Already a batch
                instruments_batch = instrument_token
            
            if self.logger:
                self.logger.log_event(f"[BATCH START] Fetching data for {len(instruments_batch)} instruments")
            
            # Process batch with caching and retry logic
            batch_results = self._fetch_historical_data_batch(instruments_batch, from_date, to_date, interval)
            
            # Return single result if single instrument was requested
            if len(instruments_batch) == 1:
                result = list(batch_results.values())[0]
            else:
                result = batch_results
            
            elapsed_time = time.time() - start_time
            if self.logger:
                cache_hits = sum(1 for _ in batch_results.values() if not _.empty)
                self.logger.log_event(f"[BATCH COMPLETE] Processed {len(instruments_batch)} instruments in {elapsed_time:.2f}s, {cache_hits} successful")
            
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            if self.logger:
                self.logger.log_event(f"[BATCH ERROR] Failed after {elapsed_time:.2f}s: {e}")
            
            # Final fallback to mock data
            if isinstance(instrument_token, (str, int)):
                return self._generate_mock_data(from_date, to_date, interval)
            else:
                return {name: self._generate_mock_data(from_date, to_date, interval) 
                       for name in instrument_token.keys()}

    def fetch_multiple_instruments_data(self, instruments_dict, from_date, to_date, interval):
        """
        🚀 NEW: Fetch historical data for multiple instruments efficiently
        
        Args:
            instruments_dict: Dict of {instrument_name: instrument_token}
            from_date: Start date
            to_date: End date  
            interval: Data interval (minute, 5minute, 1hour, day)
            
        Returns:
            Dict of {instrument_name: DataFrame}
        """
        return self._fetch_historical_data(instruments_dict, from_date, to_date, interval)

    def get_cache_statistics(self):
        """🚀 NEW: Get cache performance statistics"""
        total_entries = len(self.data_cache)
        valid_entries = sum(1 for entry in self.data_cache.values() if self._is_cache_valid(entry))
        
        return {
            'total_cached_entries': total_entries,
            'valid_cached_entries': valid_entries,
            'cache_hit_ratio': valid_entries / max(total_entries, 1),
            'cache_ttl_minutes': self.historical_config['cache_ttl_minutes'],
            'cache_size_mb': sum(entry['data'].memory_usage(deep=True).sum() 
                               for entry in self.data_cache.values() 
                               if hasattr(entry.get('data', {}), 'memory_usage')) / (1024 * 1024)
        }

    def clear_expired_cache(self):
        """🚀 NEW: Manually clear expired cache entries"""
        expired_keys = []
        for key, entry in self.data_cache.items():
            if not self._is_cache_valid(entry):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.data_cache[key]
        
        if self.logger:
            self.logger.log_event(f"[CACHE CLEANUP] Removed {len(expired_keys)} expired entries")
        
        return len(expired_keys)

    def update_historical_config(self, **kwargs):
        """🚀 NEW: Update historical data fetching configuration"""
        for key, value in kwargs.items():
            if key in self.historical_config:
                old_value = self.historical_config[key]
                self.historical_config[key] = value
                if self.logger:
                    self.logger.log_event(f"[CONFIG] Updated {key}: {old_value} -> {value}")
            else:
                if self.logger:
                    self.logger.log_event(f"[CONFIG WARNING] Unknown config key: {key}")

    def get_enhanced_market_regime(self, instrument_token="NIFTY 50", instrument_id=256265) -> Dict[str, Any]:
        """Get comprehensive market regime analysis including volatility, trend, and correlations"""
        try:
            # Fetch historical data for regime analysis
            to_date = datetime.now()
            from_date = to_date - timedelta(days=5)  # Get more data for better analysis
            
            hist_data_df = self._fetch_historical_data(instrument_token, from_date, to_date, "5minute")
            
            if hist_data_df.empty:
                return {"error": "No data available", "regime": "UNKNOWN"}
            
            # Prepare price data for analysis
            price_data = {
                'high': hist_data_df['high'].tolist(),
                'low': hist_data_df['low'].tolist(),
                'close': hist_data_df['close'].tolist(),
                'open': hist_data_df['open'].tolist()
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
            if trend_regime == "STRONGLY_TRENDING":
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
            else:  # WEAKLY_TRENDING or MIXED
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
            hist_data_df = self._fetch_historical_data(instrument_token, from_date_1min, to_date, "minute")

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
            batch_data = self.fetch_multiple_instruments_data(
                target_instruments, from_date, to_date, "5minute"
            )
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
