"""
Comprehensive mocking for external dependencies in tests
"""
import sys
from unittest.mock import MagicMock

def setup_all_mocks():
    """Setup all required mocks for testing"""
    
    # Google Cloud mocks
    mock_google = MagicMock()
    mock_google.auth = MagicMock()
    mock_google.oauth2 = MagicMock()
    mock_google.oauth2.service_account = MagicMock()
    mock_google.cloud = MagicMock()
    mock_google.api_core = MagicMock()
    mock_google.api_core.exceptions = MagicMock()
    
    sys.modules['google'] = mock_google
    sys.modules['google.auth'] = mock_google.auth
    sys.modules['google.oauth2'] = mock_google.oauth2
    sys.modules['google.oauth2.service_account'] = mock_google.oauth2.service_account
    sys.modules['google.cloud'] = mock_google.cloud
    sys.modules['google.cloud.firestore'] = MagicMock()
    sys.modules['google.cloud.storage'] = MagicMock()
    sys.modules['google.cloud.secretmanager'] = MagicMock()
    sys.modules['google.api_core'] = mock_google.api_core
    sys.modules['google.api_core.exceptions'] = mock_google.api_core.exceptions
    
    # KiteConnect mocks
    mock_kiteconnect = MagicMock()
    mock_kiteconnect.exceptions = MagicMock()
    sys.modules['kiteconnect'] = mock_kiteconnect
    sys.modules['kiteconnect.exceptions'] = mock_kiteconnect.exceptions
    
    # Other API mocks
    sys.modules['openai'] = MagicMock()
    sys.modules['anthropic'] = MagicMock()
    sys.modules['investpy'] = MagicMock()
    
    # Data analysis mocks
    sys.modules['numpy'] = MagicMock()
    sys.modules['pandas'] = MagicMock()
    sys.modules['yfinance'] = MagicMock()
    sys.modules['pandas_ta'] = MagicMock()
    sys.modules['scipy'] = MagicMock()
    sys.modules['sklearn'] = MagicMock()
    
    print("All test mocks setup complete")