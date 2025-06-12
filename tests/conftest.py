#!/usr/bin/env python3
"""
Pytest configuration file for test setup and fixtures
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch

# Add the parent directory (project root) to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Mock GCP authentication for tests
@pytest.fixture(autouse=True)
def mock_gcp_auth():
    """Mock GCP authentication to avoid credential errors in tests"""
    with patch('google.auth.default') as mock_auth:
        # Mock credentials and project
        mock_credentials = Mock()
        mock_credentials.valid = True
        mock_auth.return_value = (mock_credentials, 'test-project')
        
        # Mock Firestore client
        with patch('google.cloud.firestore.Client') as mock_firestore:
            mock_firestore_instance = Mock()
            mock_firestore.return_value = mock_firestore_instance
            
            # Mock Storage client
            with patch('google.cloud.storage.Client') as mock_storage:
                mock_storage_instance = Mock()
                mock_storage.return_value = mock_storage_instance
                
                yield

@pytest.fixture
def mock_kite_client():
    """Mock KiteConnect client for trading tests"""
    mock_client = Mock()
    mock_client.ltp.return_value = {
        'NSE:NIFTY 50': {'last_price': 17500.0},
        'NSE:BANKNIFTY': {'last_price': 38000.0}
    }
    mock_client.historical_data.return_value = [
        {
            'date': '2024-01-01',
            'open': 17500.0,
            'high': 17600.0,
            'low': 17400.0,
            'close': 17550.0,
            'volume': 100000
        }
    ]
    return mock_client

@pytest.fixture
def mock_logger():
    """Mock logger for tests"""
    logger = Mock()
    logger.log_event = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.warning = Mock()
    return logger

# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env():
    """Set up test environment variables"""
    os.environ['PAPER_TRADE'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    os.environ['GOOGLE_CLOUD_PROJECT'] = 'test-project'
    yield
