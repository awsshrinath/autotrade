# runner/market_data_fetcher.py

import datetime
import pandas as pd
import numpy as np
import requests
import time
import json
import os
from typing import Dict, Any, Optional, List
from collections import defaultdict

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

class MarketDataFetcher:
    def __init__(self, logger=None, kite_client=None):
        self.kite = kite_client
        self.logger = logger
        
        # 🚀 NEW: Historical Data Configuration
        self.historical_config = {
            'cache_ttl_minutes': 15,
            'max_retry_attempts': 3,
            'batch_size': 10,
            'rate_limit_delay': 1.0,
            'exponential_backoff_base': 2.0,
            'max_backoff_seconds': 30,
            'use_real_data': True,
            'alpha_vantage_api_key': os.getenv('ALPHA_VANTAGE_API_KEY'),
            'data_source_priority': ['yfinance', 'alpha_vantage', 'investpy', 'kite', 'mock']
        }
        
        # 🚀 NEW: In-memory cache for historical data
        self.data_cache = {}

    def fetch_latest_candle(self, instrument_token, interval="5minute"):
        try:
            now = datetime.datetime.now()
            from_time = now - datetime.timedelta(minutes=10)
            to_time = now

            candles = self.kite.historical_data(
                instrument_token,
                from_time,
                to_time,
                interval,
                continuous=False,
                oi=True,
            )

            if candles:
                latest_candle = candles[-1]
                return {
                    "timestamp": latest_candle["date"],
                    "open": latest_candle["open"],
                    "high": latest_candle["high"],
                    "low": latest_candle["low"],
                    "close": latest_candle["close"],
                    "volume": latest_candle["volume"],
                }
            else:
                self.logger.log_event(f"No candle data returned for {instrument_token}")
                return None

        except Exception as e:
            self.logger.log_event(f"Error fetching latest candle: {e}")
            return None

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
            256265: '^NSEI',
            260105: '^NSEBANK',
            264969: 'INDIA VIX',
            11924738: '^CNXIT',
            11924234: '^NSEBANK',
            11924242: '^CNXFMCG',
            11924226: '^CNXAUTO',
            11924274: '^CNXPHARMA',
        }
        return symbol_mapping.get(instrument_token, str(instrument_token))
        
    def _fetch_yfinance_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data from Yahoo Finance"""
        if not YFINANCE_AVAILABLE:
            if self.logger:
                self.logger.log_event("[YFINANCE] yfinance library not available")
            return None
        
        symbol = self._get_nifty_symbol_mapping(instrument_token)
        try:
            if self.logger:
                self.logger.log_event(f"[YFINANCE] Fetching data for {symbol}")
            
            data = yf.download(symbol, start=from_date, end=to_date, interval=interval, progress=False)
            
            if data.empty:
                if self.logger:
                    self.logger.log_event(f"[YFINANCE] No data returned for {symbol}")
                return None
            
            # Format data to match Kite's format
            formatted_data = []
            for index, row in data.iterrows():
                formatted_data.append({
                    "date": index.to_pydatetime(),
                    "open": row["Open"],
                    "high": row["High"],
                    "low": row["Low"],
                    "close": row["Close"],
                    "volume": row["Volume"]
                })
            
            return formatted_data
        
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[YFINANCE] Error fetching data for {symbol}: {e}")
            return None

    def _fetch_alpha_vantage_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data from Alpha Vantage"""
        api_key = self.historical_config.get('alpha_vantage_api_key')
        if not api_key:
            if self.logger:
                self.logger.log_event("[ALPHA_VANTAGE] API key not available")
            return None

        symbol = self._get_nifty_symbol_mapping(instrument_token).replace('^', '') # AV doesn't use ^
        
        # Map our interval to Alpha Vantage's interval strings
        interval_map = {
            "5minute": "5min",
            "15minute": "15min",
            "30minute": "30min",
            "60minute": "60min",
            "day": "daily"
        }
        av_interval = interval_map.get(interval, "daily")
        
        function = "TIME_SERIES_INTRADAY" if "min" in av_interval else "TIME_SERIES_DAILY"
        
        url = f'https://www.alphavantage.co/query?function={function}&symbol={symbol}&interval={av_interval}&apikey={api_key}'

        try:
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE] Fetching data for {symbol}")
            
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            time_series_key = f"Time Series ({av_interval})" if "min" in av_interval else "Time Series (Daily)"
            
            if time_series_key not in data:
                if self.logger:
                    self.logger.log_event(f"[ALPHA_VANTAGE] No data for {symbol}. Response: {data}")
                return None

            time_series = data[time_series_key]
            
            formatted_data = []
            for date_str, values in time_series.items():
                dt = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S' if "min" in av_interval else '%Y-%m-%d')
                if from_date <= dt <= to_date:
                    formatted_data.append({
                        "date": dt,
                        "open": float(values["1. open"]),
                        "high": float(values["2. high"]),
                        "low": float(values["3. low"]),
                        "close": float(values["4. close"]),
                        "volume": int(values["5. volume"])
                    })
            
            return sorted(formatted_data, key=lambda x: x['date'])

        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE] Network error for {symbol}: {e}")
            return None
        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[ALPHA_VANTAGE] Error fetching data for {symbol}: {e}")
            return None

    def _fetch_investpy_data(self, instrument_token, from_date, to_date, interval):
        """Fetch historical data from Investing.com via investpy"""
        if not INVESTPY_AVAILABLE:
            if self.logger:
                self.logger.log_event("[INVESTPY] investpy library not available")
            return None

        try:
            # investpy requires a different way of identifying instruments
            # This is a simplified example; a real implementation would need a robust mapping
            symbol = self._get_nifty_symbol_mapping(instrument_token)
            
            if self.logger:
                self.logger.log_event(f"[INVESTPY] Fetching data for {symbol}")

            # investpy uses different date formats
            from_date_str = from_date.strftime('%d/%m/%Y')
            to_date_str = to_date.strftime('%d/%m/%Y')

            data = investpy.get_index_historical_data(
                index=symbol,
                country='india',
                from_date=from_date_str,
                to_date=to_date_str,
                interval='Daily' if interval == 'day' else 'Weekly'
            )
            
            if data.empty:
                return None
                
            return data.to_dict('records')

        except Exception as e:
            if self.logger:
                self.logger.log_event(f"[INVESTPY] Error fetching data for {symbol}: {e}")
            return None

    def _fetch_real_historical_data(self, instrument_token, from_date, to_date, interval):
        """Fetch real historical data from prioritized sources."""
        for source in self.historical_config['data_source_priority']:
            data = None
            if source == 'yfinance' and YFINANCE_AVAILABLE:
                data = self._fetch_yfinance_data(instrument_token, from_date, to_date, interval)
            elif source == 'alpha_vantage' and self.historical_config.get('alpha_vantage_api_key'):
                data = self._fetch_alpha_vantage_data(instrument_token, from_date, to_date, interval)
            elif source == 'investpy' and INVESTPY_AVAILABLE:
                data = self._fetch_investpy_data(instrument_token, from_date, to_date, interval)
            
            if data:
                if self.logger:
                    self.logger.log_event(f"Successfully fetched data from {source} for {instrument_token}")
                return data
        
        if self.logger:
            self.logger.log_event(f"Failed to fetch real data from any source for token {instrument_token}")
        return None

    def _fetch_with_retry(self, instrument_token, from_date, to_date, interval, attempt=1):
        """Wrapper to fetch data with exponential backoff retry"""
        try:
            return self._fetch_real_historical_data(instrument_token, from_date, to_date, interval)
        except Exception as e:
            if attempt >= self.historical_config['max_retry_attempts']:
                if self.logger:
                    self.logger.log_event(f"[RETRY FAILED] Max retries reached for {instrument_token}. Error: {e}")
                return None
            
            backoff_time = min(
                self.historical_config['exponential_backoff_base'] ** attempt,
                self.historical_config['max_backoff_seconds']
            )
            
            if self.logger:
                self.logger.log_event(f"[RETRY] Attempt {attempt} failed for {instrument_token}. Retrying in {backoff_time:.2f}s. Error: {e}")
            
            time.sleep(backoff_time)
            return self._fetch_with_retry(instrument_token, from_date, to_date, interval, attempt + 1)

    def _fetch_historical_data_batch(self, instruments_batch, from_date, to_date, interval):
        """Fetch historical data for a batch of instruments"""
        batch_data = {}
        for token, symbol in instruments_batch.items():
            if self.logger:
                self.logger.log_event(f"Processing batch item: {symbol} ({token})")
            
            data = self.fetch_historical_data(token, from_date, to_date, interval)
            batch_data[token] = data
            
            # Rate limiting
            time.sleep(self.historical_config['rate_limit_delay'])
            
        return batch_data

    def _generate_mock_data(self, from_date, to_date, interval):
        """Generate mock historical data for testing"""
        if self.logger:
            self.logger.log_event("[MOCK DATA] Generating mock data")
            
        data = []
        current_time = from_date
        while current_time <= to_date:
            data.append({
                "date": current_time,
                "open": 17000 + np.random.uniform(-50, 50),
                "high": 17050 + np.random.uniform(-50, 50),
                "low": 16950 + np.random.uniform(-50, 50),
                "close": 17000 + np.random.uniform(-50, 50),
                "volume": np.random.randint(100000, 500000)
            })
            # This is a simplification; interval logic would be more complex
            current_time += datetime.timedelta(minutes=5) if interval == "5minute" else datetime.timedelta(hours=1)
        return data

    def fetch_historical_data(self, instrument_token, from_date, to_date, interval):
        """Public method to fetch historical data for a single instrument, with caching."""
        cache_key = self._generate_cache_key(instrument_token, from_date, to_date, interval)
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            return cached_data
            
        if self.historical_config['use_real_data']:
            data = self._fetch_with_retry(instrument_token, from_date, to_date, interval)
        else:
            data = None

        if not data:
            if self.logger:
                self.logger.log_event(f"Falling back to mock data for token {instrument_token}")
            data = self._generate_mock_data(from_date, to_date, interval)
        
        if data:
            self._store_in_cache(cache_key, data)
            
        return data

    def fetch_multiple_instruments_data(self, instruments_dict, from_date, to_date, interval):
        """Fetch historical data for multiple instruments using batching"""
        all_data = {}
        instrument_list = list(instruments_dict.items())
        
        for i in range(0, len(instrument_list), self.historical_config['batch_size']):
            batch = dict(instrument_list[i:i + self.historical_config['batch_size']])
            if self.logger:
                self.logger.log_event(f"Fetching batch {i // self.historical_config['batch_size'] + 1}")
            
            batch_data = self._fetch_historical_data_batch(batch, from_date, to_date, interval)
            all_data.update(batch_data)
            
        return all_data
