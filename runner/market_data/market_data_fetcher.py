import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import time
import json
from typing import Dict, Any, Optional, List

class MarketDataFetcher:
    """Enhanced market data fetcher with multiple API sources and fallback mechanisms"""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Cache for last known good data
        self.cache = {
            'sgx_nifty': None,
            'dow_futures': None,
            'last_updated': None
        }
        
        # API endpoints
        self.endpoints = {
            'yahoo_finance': 'https://query1.finance.yahoo.com/v8/finance/chart/',
            'investing_com': 'https://api.investing.com/api/financialdata/',
            'alpha_vantage': 'https://www.alphavantage.co/query'
        }
        
        # Symbol mappings for different APIs
        self.symbols = {
            'sgx_nifty': {
                'yahoo': 'NIFTY.NS',  # NSE Nifty
                'investing': 'nifty-50',
                'backup_symbol': '^NSEI'  # Alternative Yahoo symbol
            },
            'dow_futures': {
                'yahoo': 'YM=F',  # Dow Jones Mini Futures
                'investing': 'us-30-futures',
                'backup_symbol': 'DJI=F'  # Alternative futures symbol
            }
        }

    def _make_request(self, url: str, params: dict = None, timeout: int = 10) -> Optional[dict]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(url, params=params, timeout=timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] API request failed: {url} - {str(e)}")
            return None
        except json.JSONDecodeError as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] JSON decode failed for {url}: {str(e)}")
            return None

    def fetch_yahoo_finance_data(self, symbol: str) -> Optional[dict]:
        """Fetch data from Yahoo Finance API"""
        url = f"{self.endpoints['yahoo_finance']}{symbol}"
        params = {
            'interval': '1m',
            'range': '1d',
            'includePrePost': 'true'
        }
        
        data = self._make_request(url, params)
        if not data or 'chart' not in data:
            return None
            
        try:
            chart = data['chart']['result'][0]
            meta = chart['meta']
            quote = chart['indicators']['quote'][0]
            
            current_price = meta.get('regularMarketPrice', 0)
            previous_close = meta.get('previousClose', 0)
            change = current_price - previous_close if previous_close else 0
            change_percent = (change / previous_close * 100) if previous_close else 0
            
            return {
                'symbol': symbol,
                'current_price': current_price,
                'previous_close': previous_close,
                'change': change,
                'change_percent': change_percent,
                'volume': meta.get('regularMarketVolume', 0),
                'market_state': meta.get('marketState', 'UNKNOWN'),
                'timestamp': datetime.now().isoformat(),
                'source': 'yahoo_finance'
            }
        except (KeyError, TypeError) as e:
            if self.logger:
                self.logger.log_event(f"[ERROR] Failed to parse Yahoo Finance data for {symbol}: {str(e)}")
            return None

    def fetch_sgx_nifty_data(self) -> Optional[dict]:
        """Fetch SGX Nifty data with multiple fallbacks"""
        symbols_to_try = [
            self.symbols['sgx_nifty']['yahoo'],
            self.symbols['sgx_nifty']['backup_symbol']
        ]
        
        for symbol in symbols_to_try:
            if self.logger:
                self.logger.log_event(f"Attempting to fetch SGX Nifty data using symbol: {symbol}")
            
            data = self.fetch_yahoo_finance_data(symbol)
            if data:
                # Convert to SGX sentiment format
                trend = "neutral"
                if data['change_percent'] > 0.5:
                    trend = "bullish"
                elif data['change_percent'] < -0.5:
                    trend = "bearish"
                    
                return {
                    'price': data['current_price'],
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                    'trend': trend,
                    'market_state': data['market_state'],
                    'timestamp': data['timestamp'],
                    'source': data['source']
                }
        
        # If all attempts fail, return cached data if available
        if self.cache.get('sgx_nifty'):
            if self.logger:
                self.logger.log_event("[WARNING] Using cached SGX Nifty data - live fetch failed")
            return self.cache['sgx_nifty']
            
        return None

    def fetch_dow_futures_data(self) -> Optional[dict]:
        """Fetch Dow Futures data with multiple fallbacks"""
        symbols_to_try = [
            self.symbols['dow_futures']['yahoo'],
            self.symbols['dow_futures']['backup_symbol']
        ]
        
        for symbol in symbols_to_try:
            if self.logger:
                self.logger.log_event(f"Attempting to fetch Dow Futures data using symbol: {symbol}")
            
            data = self.fetch_yahoo_finance_data(symbol)
            if data:
                # Convert to Dow sentiment format
                trend = "neutral"
                if data['change_percent'] > 0.3:
                    trend = "bullish"
                elif data['change_percent'] < -0.3:
                    trend = "bearish"
                    
                return {
                    'price': data['current_price'],
                    'change': data['change'],
                    'change_percent': data['change_percent'],
                    'trend': trend,
                    'market_state': data['market_state'],
                    'timestamp': data['timestamp'],
                    'source': data['source']
                }
        
        # If all attempts fail, return cached data if available
        if self.cache.get('dow_futures'):
            if self.logger:
                self.logger.log_event("[WARNING] Using cached Dow Futures data - live fetch failed")
            return self.cache['dow_futures']
            
        return None

    def update_cache(self, sgx_data: dict = None, dow_data: dict = None):
        """Update the data cache"""
        if sgx_data:
            self.cache['sgx_nifty'] = sgx_data
        if dow_data:
            self.cache['dow_futures'] = dow_data
        self.cache['last_updated'] = datetime.now().isoformat()

    def fetch_all_premarket_data(self) -> dict:
        """Fetch all pre-market data with proper error handling"""
        start_time = time.time()
        
        # Fetch SGX Nifty data
        sgx_data = self.fetch_sgx_nifty_data()
        
        # Fetch Dow Futures data  
        dow_data = self.fetch_dow_futures_data()
        
        # Update cache with successful fetches
        self.update_cache(sgx_data, dow_data)
        
        # Compile comprehensive pre-market data
        premarket_data = {
            "sgx_nifty": sgx_data or {"change": 0, "trend": "neutral", "error": "Data unavailable"},
            "dow_futures": dow_data or {"change": 0, "trend": "neutral", "error": "Data unavailable"},
            "crude_oil": {"change": 0, "trend": "neutral", "note": "Placeholder - can be enhanced"},
            "dollar_index": {"change": 0, "trend": "neutral", "note": "Placeholder - can be enhanced"},
            "vix": {"value": 15.5, "trend": "moderate", "note": "Use India VIX from Kite"},
            "market_sentiment": self._determine_overall_sentiment(sgx_data, dow_data),
            "fetch_time_seconds": round(time.time() - start_time, 2),
            "last_updated": datetime.now().isoformat()
        }
        
        if self.logger:
            self.logger.log_event(f"Pre-market data fetch completed in {premarket_data['fetch_time_seconds']}s")
            
        return premarket_data

    def _determine_overall_sentiment(self, sgx_data: dict, dow_data: dict) -> str:
        """Determine overall market sentiment from multiple sources"""
        bullish_signals = 0
        bearish_signals = 0
        total_signals = 0
        
        if sgx_data and 'trend' in sgx_data:
            total_signals += 1
            if sgx_data['trend'] == 'bullish':
                bullish_signals += 1
            elif sgx_data['trend'] == 'bearish':
                bearish_signals += 1
                
        if dow_data and 'trend' in dow_data:
            total_signals += 1
            if dow_data['trend'] == 'bullish':
                bullish_signals += 1
            elif dow_data['trend'] == 'bearish':
                bearish_signals += 1
        
        if total_signals == 0:
            return "neutral"
            
        if bullish_signals > bearish_signals:
            return "bullish"
        elif bearish_signals > bullish_signals:
            return "bearish"
        else:
            return "neutral" 