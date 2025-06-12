"""
Test suite for real historical data integration in MarketMonitor.
Tests the new functionality that replaces mock data with real data from multiple sources.
"""

import pytest
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add the parent directory to the path so we can import runner modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner.market_monitor import MarketMonitor
from unittest.mock import Mock, patch, MagicMock


class TestRealHistoricalDataIntegration:
    """Test suite for real historical data functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.logger = Mock()
        self.kite_client = Mock()
        self.firestore_client = Mock()
        
        # Create MarketMonitor instance
        self.monitor = MarketMonitor(
            logger=self.logger,
            kite_client=self.kite_client,
            firestore_client=self.firestore_client
        )
        
        # Test date ranges
        self.to_date = datetime.now()
        self.from_date = self.to_date - timedelta(days=7)
        
    def test_nifty_symbol_mapping(self):
        """Test symbol mapping for different data sources"""
        # Test numeric instrument tokens
        assert self.monitor._get_nifty_symbol_mapping(256265) == '^NSEI'
        assert self.monitor._get_nifty_symbol_mapping(260105) == '^NSEBANK'
        assert self.monitor._get_nifty_symbol_mapping(11924738) == '^CNXIT'
        
        # Test string instrument names
        assert self.monitor._get_nifty_symbol_mapping('NIFTY 50') == '^NSEI'
        assert self.monitor._get_nifty_symbol_mapping('BANKNIFTY') == '^NSEBANK'
        assert self.monitor._get_nifty_symbol_mapping('NIFTY IT') == '^CNXIT'
        
        # Test default fallback
        assert self.monitor._get_nifty_symbol_mapping('UNKNOWN') == '^NSEI'
        
    @patch('runner.market_monitor.YFINANCE_AVAILABLE', True)
    @patch('runner.market_monitor.yf')
    def test_yfinance_data_fetching_success(self, mock_yf):
        """Test successful data fetching from Yahoo Finance"""
        # Mock yfinance response
        mock_ticker = Mock()
        mock_df = pd.DataFrame({
            'Date': pd.date_range(start=self.from_date, periods=5, freq='D'),
            'Open': [17500, 17520, 17540, 17560, 17580],
            'High': [17550, 17570, 17590, 17610, 17630],
            'Low': [17480, 17500, 17520, 17540, 17560],
            'Close': [17530, 17550, 17570, 17590, 17610],
            'Volume': [10000, 11000, 12000, 13000, 14000]
        })
        mock_df = mock_df.set_index('Date')
        mock_ticker.history.return_value = mock_df
        mock_yf.Ticker.return_value = mock_ticker
        
        # Test the method
        result = self.monitor._fetch_yfinance_data(256265, self.from_date, self.to_date, 'day')
        
        # Verify the result
        assert not result.empty
        assert len(result) == 5
        assert all(col in result.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # Verify yfinance was called correctly
        mock_yf.Ticker.assert_called_once_with('^NSEI')
        mock_ticker.history.assert_called_once()
        
    @patch('runner.market_monitor.YFINANCE_AVAILABLE', False)
    def test_yfinance_not_available(self):
        """Test behavior when yfinance is not available"""
        with pytest.raises(ImportError, match="yfinance not available"):
            self.monitor._fetch_yfinance_data(256265, self.from_date, self.to_date, 'day')
            
    @patch('requests.get')
    def test_alpha_vantage_data_fetching_success(self, mock_requests):
        """Test successful data fetching from Alpha Vantage"""
        # Set up API key
        self.monitor.historical_config['alpha_vantage_api_key'] = 'test_api_key'
        
        # Mock Alpha Vantage response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Time Series (Daily)': {
                '2024-01-01': {
                    '1. open': '17500.0',
                    '2. high': '17550.0',
                    '3. low': '17480.0',
                    '4. close': '17530.0',
                    '5. volume': '10000'
                },
                '2024-01-02': {
                    '1. open': '17520.0',
                    '2. high': '17570.0',
                    '3. low': '17500.0',
                    '4. close': '17550.0',
                    '5. volume': '11000'
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        # Test the method
        result = self.monitor._fetch_alpha_vantage_data(256265, self.from_date, self.to_date, 'day')
        
        # Verify the result
        assert not result.empty
        assert len(result) == 2
        assert all(col in result.columns for col in ['date', 'open', 'high', 'low', 'close', 'volume'])
        
        # Verify API was called correctly
        mock_requests.assert_called_once()
        
    def test_alpha_vantage_no_api_key(self):
        """Test Alpha Vantage behavior without API key"""
        # Ensure no API key is set
        self.monitor.historical_config['alpha_vantage_api_key'] = None
        
        with pytest.raises(ValueError, match="Alpha Vantage API key not configured"):
            self.monitor._fetch_alpha_vantage_data(256265, self.from_date, self.to_date, 'day')
            
    @patch('requests.get')
    def test_alpha_vantage_api_error(self, mock_requests):
        """Test Alpha Vantage API error handling"""
        # Set up API key
        self.monitor.historical_config['alpha_vantage_api_key'] = 'test_api_key'
        
        # Mock error response
        mock_response = Mock()
        mock_response.json.return_value = {
            'Error Message': 'Invalid API call'
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.return_value = mock_response
        
        with pytest.raises(ValueError, match="Alpha Vantage error: Invalid API call"):
            self.monitor._fetch_alpha_vantage_data(256265, self.from_date, self.to_date, 'day')
            
    def test_real_data_source_priority(self):
        """Test that data sources are tried in priority order"""
        # Configure priority order
        self.monitor.historical_config['data_source_priority'] = ['yfinance', 'alpha_vantage', 'kite']
        
        with patch.object(self.monitor, '_fetch_yfinance_data') as mock_yf, \
             patch.object(self.monitor, '_fetch_alpha_vantage_data') as mock_av, \
             patch.object(self.monitor, '_fetch_with_retry') as mock_kite:
            
            # Mock yfinance to succeed
            mock_df = pd.DataFrame({
                'date': [datetime.now()],
                'open': [17500],
                'high': [17550],
                'low': [17480],
                'close': [17530],
                'volume': [10000]
            })
            mock_yf.return_value = mock_df
            
            # Call the method
            result = self.monitor._fetch_real_historical_data(256265, self.from_date, self.to_date, 'day')
            
            # Verify only yfinance was called (first in priority)
            mock_yf.assert_called_once()
            mock_av.assert_not_called()
            mock_kite.assert_not_called()
            
            assert not result.empty
            
    def test_real_data_fallback_chain(self):
        """Test fallback behavior when data sources fail"""
        # Configure priority order
        self.monitor.historical_config['data_source_priority'] = ['yfinance', 'alpha_vantage', 'kite']
        
        with patch.object(self.monitor, '_fetch_yfinance_data') as mock_yf, \
             patch.object(self.monitor, '_fetch_alpha_vantage_data') as mock_av, \
             patch.object(self.monitor, '_fetch_with_retry') as mock_kite:
            
            # Mock yfinance and alpha vantage to fail
            mock_yf.side_effect = Exception("YFinance failed")
            mock_av.side_effect = Exception("Alpha Vantage failed")
            
            # Mock kite to succeed
            mock_df = pd.DataFrame({
                'date': [datetime.now()],
                'open': [17500],
                'high': [17550],
                'low': [17480],
                'close': [17530],
                'volume': [10000]
            })
            mock_kite.return_value = mock_df
            
            # Call the method
            result = self.monitor._fetch_real_historical_data(256265, self.from_date, self.to_date, 'day')
            
            # Verify all sources were tried in order
            mock_yf.assert_called_once()
            mock_av.assert_called_once()
            mock_kite.assert_called_once()
            
            assert not result.empty
            
    def test_real_data_disabled(self):
        """Test behavior when real data fetching is disabled"""
        # Disable real data fetching
        self.monitor.historical_config['use_real_data'] = False
        
        with pytest.raises(ValueError, match="Real data fetching disabled"):
            self.monitor._fetch_real_historical_data(256265, self.from_date, self.to_date, 'day')
            
    def test_integration_with_existing_batch_logic(self):
        """Test integration of real data with existing batch processing"""
        # Enable real data
        self.monitor.historical_config['use_real_data'] = True
        
        with patch.object(self.monitor, '_fetch_real_historical_data') as mock_real_data:
            # Mock successful real data fetch
            mock_df = pd.DataFrame({
                'date': [datetime.now()],
                'open': [17500],
                'high': [17550],
                'low': [17480],
                'close': [17530],
                'volume': [10000]
            })
            mock_real_data.return_value = mock_df
            
            # Test batch processing
            instruments_batch = {'NIFTY 50': 256265}
            result = self.monitor._fetch_historical_data_batch(
                instruments_batch, self.from_date, self.to_date, 'day'
            )
            
            # Verify results
            assert 'NIFTY 50' in result
            assert not result['NIFTY 50'].empty
            mock_real_data.assert_called_once()
            
    def test_cache_integration_with_real_data(self):
        """Test that real data is properly cached"""
        # Clear cache
        self.monitor.data_cache = {}
        
        with patch.object(self.monitor, '_fetch_real_historical_data') as mock_real_data:
            # Mock successful real data fetch
            mock_df = pd.DataFrame({
                'date': [datetime.now()],
                'open': [17500],
                'high': [17550],
                'low': [17480],
                'close': [17530],
                'volume': [10000]
            })
            mock_real_data.return_value = mock_df
            
            # First call should fetch from real data
            result1 = self.monitor._fetch_historical_data(256265, self.from_date, self.to_date, 'day')
            
            # Second call should use cache
            result2 = self.monitor._fetch_historical_data(256265, self.from_date, self.to_date, 'day')
            
            # Verify real data was only called once
            assert mock_real_data.call_count == 1
            
            # Verify both results are identical
            pd.testing.assert_frame_equal(result1, result2)
            
    def test_error_handling_and_logging(self):
        """Test comprehensive error handling and logging"""
        with patch.object(self.monitor, '_fetch_real_historical_data') as mock_real_data:
            # Mock real data to fail
            mock_real_data.side_effect = Exception("All real sources failed")
            
            # Mock kite client to also fail
            self.kite_client = None
            self.monitor.kite_client = None
            
            # Should fallback to mock data
            result = self.monitor._fetch_historical_data(256265, self.from_date, self.to_date, 'day')
            
            # Verify fallback to mock data occurred
            assert not result.empty
            
            # Verify appropriate logging calls were made
            assert self.logger.log_event.call_count > 0
            
    def test_data_quality_and_format_consistency(self):
        """Test that all data sources return consistent format"""
        expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # Test mock data format
        mock_data = self.monitor._generate_mock_data(self.from_date, self.to_date, 'day')
        assert all(col in mock_data.columns for col in expected_columns)
        
        # Test that returned data has proper types
        if not mock_data.empty:
            assert pd.api.types.is_datetime64_any_dtype(mock_data['date'])
            assert pd.api.types.is_numeric_dtype(mock_data['open'])
            assert pd.api.types.is_numeric_dtype(mock_data['high'])
            assert pd.api.types.is_numeric_dtype(mock_data['low'])
            assert pd.api.types.is_numeric_dtype(mock_data['close'])
            assert pd.api.types.is_numeric_dtype(mock_data['volume'])


if __name__ == '__main__':
    pytest.main([__file__]) 