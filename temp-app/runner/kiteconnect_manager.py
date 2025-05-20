# runner/kiteconnect_manager.py

from kiteconnect import KiteConnect
from runner.secret_manager_client import access_secret

PROJECT_ID = "autotrade-453303"  # Your GCP Project ID

class KiteConnectManager:
    def __init__(self, logger):
        self.logger = logger
        
        # Fetch API credentials from Secret Manager
        self.api_key = access_secret("ZERODHA_API_KEY", PROJECT_ID)
        self.api_secret = access_secret("ZERODHA_API_SECRET", PROJECT_ID)

        # Initialize KiteConnect
        self.kite = KiteConnect(api_key=self.api_key)
        self.kws = None
        self.access_token = None  # Will be set separately

    def set_access_token(self):
        # Fetch daily Access Token securely
        self.access_token = access_secret("ZERODHA_ACCESS_TOKEN", PROJECT_ID)
        self.kite.set_access_token(self.access_token)
        self.logger.log_event("Access token set successfully for KiteConnect session.")

    def get_kite_client(self):
        if self.access_token is None:
            self.set_access_token()
        return self.kite
