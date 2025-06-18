# runner/kiteconnect_manager.py

import logging
import time
from typing import Optional
from kiteconnect import KiteConnect, KiteTicker
from kiteconnect.exceptions import (
    KiteException, 
    TokenException, 
    PermissionException, 
    OrderException,
    DataException,
    NetworkException,
    APIException
)

from runner.secret_manager import access_secret, validate_secret_access
from runner.logger import TradingLogger

PROJECT_ID = "autotrade-453303"  # Your GCP Project ID


class KiteConnectManager:
    def __init__(self, logger: TradingLogger, project_id: str = PROJECT_ID):
        self.logger = logger
        self.project_id = project_id
        self.kite = None
        self.access_token = None
        self.api_key = None
        self.api_secret = None
        self.connection_validated = False
        self.last_validation_time = 0
        self.validation_interval = 300  # 5 minutes
        
        # FIXED: Initialize with comprehensive error handling
        self._initialize_credentials()

    def _initialize_credentials(self):
        """Initialize API credentials with comprehensive error handling"""
        try:
            # FIXED: Validate secret access first
            if not validate_secret_access(self.project_id):
                self.logger.log_event("❌ Secret validation failed - some secrets are inaccessible")
                raise ValueError("Required secrets are not accessible")
            
            # FIXED: Fetch API credentials with error handling
            self.api_key = access_secret("ZERODHA_API_KEY", self.project_id)
            if not self.api_key:
                error_msg = "Failed to retrieve Zerodha API key"
                self.logger.log_event(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            self.api_secret = access_secret("ZERODHA_API_SECRET", self.project_id)
            if not self.api_secret:
                error_msg = "Failed to retrieve Zerodha API secret"
                self.logger.log_event(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            # FIXED: Validate credential format
            if len(self.api_key) < 10:
                error_msg = "API key appears to be invalid (too short)"
                self.logger.log_event(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            if len(self.api_secret) < 10:
                error_msg = "API secret appears to be invalid (too short)"
                self.logger.log_event(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
            # FIXED: Initialize KiteConnect with error handling
            try:
                self.kite = KiteConnect(api_key=self.api_key)
                self.logger.log_event("✅ KiteConnect client initialized successfully")
            except Exception as e:
                error_msg = f"Failed to initialize KiteConnect client: {e}"
                self.logger.log_event(f"❌ {error_msg}")
                raise ValueError(error_msg)
            
        except Exception as e:
            self.logger.log_event(f"❌ Failed to initialize KiteConnect credentials: {e}")
            # FIXED: Don't raise exception in __init__, let calling code handle it
            self.kite = None

    def set_access_token(self) -> bool:
        """
        Fetch and set daily Access Token securely with comprehensive error handling
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.kite:
                self.logger.log_event("❌ KiteConnect client not initialized")
                return False
            
            # FIXED: Fetch daily Access Token with validation
            self.access_token = access_secret("ZERODHA_ACCESS_TOKEN", self.project_id)
            if not self.access_token:
                self.logger.log_event("❌ Failed to retrieve Zerodha access token")
                return False
            
            # FIXED: Validate token format
            if len(self.access_token) < 20:  # Basic validation
                self.logger.log_event("❌ Access token appears to be invalid (too short)")
                return False
            
            # FIXED: Set access token with error handling
            try:
                self.kite.set_access_token(self.access_token)
                self.logger.log_event("✅ Access token set successfully for KiteConnect session")
                
                # FIXED: Validate the token by testing connection
                return self._validate_connection()
                
            except TokenException as e:
                error_msg = f"Invalid access token: {e}"
                self.logger.log_event(f"❌ {error_msg}")
                return False
                
            except Exception as e:
                error_msg = f"Failed to set access token: {e}"
                self.logger.log_event(f"❌ {error_msg}")
                return False
                
        except Exception as e:
            self.logger.log_event(f"❌ Unexpected error setting access token: {e}")
            return False

    def _validate_connection(self) -> bool:
        """
        Validate KiteConnect connection by testing API calls
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            if not self.kite or not self.access_token:
                return False
            
            # FIXED: Test connection with multiple API calls
            try:
                # Test 1: Get profile
                profile = self.kite.profile()
                if not profile or 'user_id' not in profile:
                    self.logger.log_event("❌ Profile test failed - invalid response")
                    return False
                
                user_id = profile.get('user_id', 'unknown')
                user_name = profile.get('user_name', 'unknown')
                self.logger.log_event(f"✅ Connection validated for user: {user_name} ({user_id})")
                
                # Test 2: Get margins (basic API test)
                margins = self.kite.margins()
                if not margins:
                    self.logger.log_event("⚠️ Margins test failed but profile succeeded")
                else:
                    equity_available = margins.get('equity', {}).get('available', {}).get('cash', 0)
                    self.logger.log_event(f"✅ Account margins validated - Available cash: ₹{equity_available}")
                
                # Test 3: Get positions (another basic test)
                try:
                    positions = self.kite.positions()
                    if positions:
                        net_positions = positions.get('net', [])
                        self.logger.log_event(f"✅ Positions data accessible - {len(net_positions)} positions")
                    else:
                        self.logger.log_event("✅ Positions data accessible - no positions")
                except Exception as e:
                    self.logger.log_event(f"⚠️ Positions test failed: {e}")
                
                self.connection_validated = True
                self.last_validation_time = time.time()
                return True
                
            except TokenException as e:
                self.logger.log_event(f"❌ Token validation failed: {e}")
                return False
                
            except PermissionException as e:
                self.logger.log_event(f"❌ Permission denied: {e}")
                return False
                
            except NetworkException as e:
                self.logger.log_event(f"❌ Network error during validation: {e}")
                return False
                
            except DataException as e:
                self.logger.log_event(f"❌ Data error during validation: {e}")
                return False
                
            except Exception as e:
                self.logger.log_event(f"❌ Unexpected error during validation: {e}")
                return False
                
        except Exception as e:
            self.logger.log_event(f"❌ Connection validation failed: {e}")
            return False

    def get_kite_client(self, project_id: str = None) -> Optional[KiteConnect]:
        """
        Get KiteConnect client with validation and automatic token refresh
        
        Args:
            project_id: For backward compatibility (not used)
            
        Returns:
            KiteConnect instance or None if not available
        """
        try:
            # FIXED: Check if we need to revalidate connection
            current_time = time.time()
            needs_validation = (
                not self.connection_validated or 
                current_time - self.last_validation_time > self.validation_interval
            )
            
            if needs_validation:
                self.logger.log_event("🔄 Re-validating KiteConnect connection...")
                if not self._validate_connection():
                    self.logger.log_event("❌ Connection validation failed - attempting token refresh")
                    
                    # FIXED: Try to refresh token
                    if not self.set_access_token():
                        self.logger.log_event("❌ Token refresh failed")
                        return None
            
            # FIXED: Return client only if validated
            if self.connection_validated:
                return self.kite
            else:
                self.logger.log_event("❌ KiteConnect client not validated")
                return None
                
        except Exception as e:
            self.logger.log_event(f"❌ Error getting KiteConnect client: {e}")
            return None

    def test_connection(self) -> bool:
        """
        Test KiteConnect connection and log detailed status
        
        Returns:
            True if connection is working, False otherwise
        """
        try:
            self.logger.log_event("🧪 Testing KiteConnect connection...")
            
            if not self.kite:
                self.logger.log_event("❌ KiteConnect client not initialized")
                return False
            
            if not self.access_token:
                self.logger.log_event("❌ Access token not set")
                return False
            
            return self._validate_connection()
            
        except Exception as e:
            self.logger.log_event(f"❌ Connection test failed: {e}")
            return False

    def get_connection_status(self) -> dict:
        """
        Get detailed connection status for monitoring
        
        Returns:
            Dictionary with connection status details
        """
        return {
            'kite_initialized': self.kite is not None,
            'access_token_set': self.access_token is not None,
            'connection_validated': self.connection_validated,
            'last_validation_time': self.last_validation_time,
            'time_since_validation': time.time() - self.last_validation_time if self.last_validation_time else None,
            'api_key_available': self.api_key is not None,
            'api_secret_available': self.api_secret is not None,
            'project_id': self.project_id
        }

    def reset_connection(self) -> bool:
        """
        Reset and reinitialize the connection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.log_event("🔄 Resetting KiteConnect connection...")
            
            # Clear current state
            self.connection_validated = False
            self.last_validation_time = 0
            self.access_token = None
            
            # Reinitialize
            self._initialize_credentials()
            
            if self.kite:
                return self.set_access_token()
            else:
                self.logger.log_event("❌ Failed to reinitialize KiteConnect client")
                return False
                
        except Exception as e:
            self.logger.log_event(f"❌ Failed to reset connection: {e}")
            return False

    def safe_api_call(self, method_name: str, *args, **kwargs):
        """
        Make a safe API call with error handling and retries
        
        Args:
            method_name: Name of the KiteConnect method to call
            *args, **kwargs: Arguments to pass to the method
            
        Returns:
            API response or None if failed
        """
        if not self.kite:
            self.logger.log_event(f"❌ Cannot call {method_name} - KiteConnect client not available")
            return None
        
        # FIXED: Ensure connection is valid before API call
        if not self.connection_validated:
            if not self.test_connection():
                self.logger.log_event(f"❌ Cannot call {method_name} - connection not validated")
                return None
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                method = getattr(self.kite, method_name)
                result = method(*args, **kwargs)
                
                if attempt > 0:
                    self.logger.log_event(f"✅ {method_name} succeeded on attempt {attempt + 1}")
                
                return result
                
            except TokenException as e:
                self.logger.log_event(f"❌ Token error in {method_name}: {e}")
                # Try to refresh token
                if attempt < max_retries - 1 and self.set_access_token():
                    continue
                return None
                
            except NetworkException as e:
                self.logger.log_event(f"⚠️ Network error in {method_name} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
                
            except (PermissionException, OrderException, DataException) as e:
                self.logger.log_event(f"❌ API error in {method_name}: {e}")
                return None
                
            except Exception as e:
                self.logger.log_event(f"❌ Unexpected error in {method_name} (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
        
        self.logger.log_event(f"❌ {method_name} failed after {max_retries} attempts")
        return None

    def connect(self):
        """
        Connect to Kite API and validate secret access
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            self.logger.log_info("Connecting to Kite API...")
            
            if not self.kite:
                self.logger.log_event("❌ KiteConnect client not initialized")
                return False
            
            if not self.access_token:
                self.logger.log_event("❌ Access token not set")
                return False
            
            self.logger.log_info("Successfully connected to Kite API.")
            
            # Validate secret access after connecting
            if not validate_secret_access(self.logger):
                self.logger.log_critical("Secret access validation failed. Check GCP permissions.")
                # Depending on the desired behavior, you might want to raise an exception here
                # raise Exception("Secret access validation failed.")

            return True
            
        except TokenException:
            self.logger.log_warning("Kite access token expired or invalid. Attempting to refresh.")
            return False
        except APIException as e:
            self.logger.log_error(f"Kite API error during connection: {e}")
            raise  # Re-raise the exception after logging
        except Exception as e:
            self.logger.log_critical(f"An unexpected error occurred during Kite connection: {e}")
            raise

    def get_user_profile(self):
        """
        Get user profile from Kite API
        
        Returns:
            User profile dictionary or None if failed
        """
        try:
            return self.kite.profile()
        except APIException as e:
            self.logger.log_error(f"API error while fetching user profile: {e}")
            return None
        except Exception as e:
            self.logger.log_error(f"An unexpected error occurred while fetching user profile: {e}")
            return None

    def close_session(self):
        """
        Close KiteConnect session and invalidate access token
        
        Returns:
            True if successful, False otherwise
        """
        self.logger.log_info("Closing KiteConnect session (logging out).")
        try:
            # Invalidate the access token to log out
            self.kite.invalidate_access_token()
            return True
        except APIException as e:
            self.logger.log_warning(f"API error during logout: {e}. This can sometimes happen if the session is already invalid.")
            return False
        except Exception as e:
            self.logger.log_error(f"An unexpected error occurred during logout: {e}")
            return False
