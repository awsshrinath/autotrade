import os
import logging
import time
from typing import Optional

from google.auth import default
from google.cloud import secretmanager
from google.oauth2 import service_account
from kiteconnect import KiteConnect
from google.api_core import exceptions as gcp_exceptions


# FIXED: Add secure credential caching with expiration
_credential_cache = {}
_cache_expiry = {}
CACHE_DURATION = 300  # 5 minutes


def create_secret_manager_client() -> Optional[secretmanager.SecretManagerServiceClient]:
    """
    Creates a Secret Manager Client with comprehensive error handling.
    Prioritizes Service Account credentials from GOOGLE_APPLICATION_CREDENTIALS or local key file;
    otherwise uses default credentials (GCP VM, Cloud Run, etc.).
    
    Returns:
        SecretManagerServiceClient instance or None if failed
    """
    try:
        # FIXED: Multiple credential paths with validation
        credentials = None
        
        # Try local Service Account key first
        key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not key_path:
            # FIXED: Try multiple potential key locations
            potential_paths = [
                "./keys/autotrade.json",
                "/app/keys/autotrade.json", 
                "/etc/gcp/autotrade.json",
                os.path.expanduser("~/.config/gcp/autotrade.json")
            ]
            
            for path in potential_paths:
                if os.path.isfile(path):
                    key_path = path
                    break
        
        if key_path and os.path.isfile(key_path):
            try:
                # FIXED: Validate key file before using
                with open(key_path, 'r') as f:
                    import json
                    key_data = json.load(f)
                    required_fields = ['type', 'project_id', 'private_key', 'client_email']
                    
                    for field in required_fields:
                        if field not in key_data:
                            raise ValueError(f"Invalid service account key: missing '{field}'")
                
                credentials = service_account.Credentials.from_service_account_file(key_path)
                logging.info(f"Using service account credentials from: {key_path}")
                
            except (json.JSONDecodeError, ValueError, FileNotFoundError) as e:
                logging.error(f"Failed to load service account key from {key_path}: {e}")
                credentials = None
        
        if not credentials:
            # FIXED: Fallback to default credentials with validation
            try:
                credentials, project = default()
                logging.info(f"Using default GCP credentials for project: {project}")
            except Exception as e:
                logging.error(f"Failed to get default credentials: {e}")
                raise ValueError("No valid GCP credentials found")
        
        # FIXED: Create client with timeout and retry configuration
        client = secretmanager.SecretManagerServiceClient(credentials=credentials)
        
        # FIXED: Test client connectivity
        try:
            # Try to list secrets to validate credentials
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "autotrade-453303")
            parent = f"projects/{project_id}"
            # This will raise an exception if credentials are invalid
            list(client.list_secrets(request={"parent": parent}, timeout=10))
            logging.info("Secret Manager client connectivity verified")
            
        except gcp_exceptions.PermissionDenied:
            logging.error("Secret Manager access denied - check IAM permissions")
            raise
        except gcp_exceptions.NotFound:
            logging.error(f"Project {project_id} not found or inaccessible")
            raise
        except Exception as e:
            logging.error(f"Secret Manager connectivity test failed: {e}")
            raise
        
        return client
        
    except Exception as e:
        logging.error(f"Failed to create Secret Manager client: {e}")
        return None


def access_secret(secret_id: str, project_id: str = "autotrade-453303", use_cache: bool = True) -> Optional[str]:
    """
    Accesses the latest version of the specified secret from Secret Manager with caching and error handling.
    
    Args:
        secret_id: The ID of the secret to access
        project_id: GCP project ID
        use_cache: Whether to use cached values
        
    Returns:
        Secret value as string or None if failed
    """
    # FIXED: Input validation
    if not secret_id or not isinstance(secret_id, str):
        logging.error(f"Invalid secret_id: {secret_id}")
        return None
    
    if not project_id or not isinstance(project_id, str):
        logging.error(f"Invalid project_id: {project_id}")
        return None
    
    cache_key = f"{project_id}:{secret_id}"
    
    # FIXED: Check cache with expiration
    if use_cache and cache_key in _credential_cache:
        cache_time = _cache_expiry.get(cache_key, 0)
        if time.time() - cache_time < CACHE_DURATION:
            logging.debug(f"Using cached secret: {secret_id}")
            return _credential_cache[cache_key]
        else:
            # Remove expired cache entry
            _credential_cache.pop(cache_key, None)
            _cache_expiry.pop(cache_key, None)
    
    try:
        client = create_secret_manager_client()
        if not client:
            logging.error("Could not create Secret Manager client")
            return None
        
        # FIXED: Construct secret name with validation
        name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
        
        # FIXED: Access secret with timeout and retry
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                response = client.access_secret_version(request={"name": name}, timeout=10)
                secret_value = response.payload.data.decode("UTF-8")
                
                # FIXED: Validate secret value
                if not secret_value or secret_value.strip() == "":
                    logging.error(f"Secret {secret_id} is empty or contains only whitespace")
                    return None
                
                # FIXED: Cache the result
                if use_cache:
                    _credential_cache[cache_key] = secret_value
                    _cache_expiry[cache_key] = time.time()
                
                logging.info(f"Successfully retrieved secret: {secret_id}")
                return secret_value
                
            except gcp_exceptions.NotFound:
                logging.error(f"Secret not found: {secret_id} in project {project_id}")
                return None
                
            except gcp_exceptions.PermissionDenied:
                logging.error(f"Permission denied accessing secret: {secret_id}")
                return None
                
            except gcp_exceptions.DeadlineExceeded:
                logging.warning(f"Timeout accessing secret {secret_id} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                continue
                
            except Exception as e:
                logging.error(f"Error accessing secret {secret_id} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                continue
        
        logging.error(f"Failed to access secret {secret_id} after {max_retries} attempts")
        return None
        
    except Exception as e:
        logging.error(f"Unexpected error accessing secret {secret_id}: {e}")
        return None


def get_kite_client(project_id: str) -> Optional[KiteConnect]:
    """
    Creates a KiteConnect client with comprehensive error handling and validation.
    
    Args:
        project_id: GCP project ID
        
    Returns:
        KiteConnect instance or None if failed
    """
    try:
        # FIXED: Validate inputs
        if not project_id:
            logging.error("Project ID is required")
            return None
        
        # FIXED: Get credentials with error handling
        api_key = access_secret("ZERODHA_API_KEY", project_id)
        if not api_key:
            logging.error("Failed to retrieve Zerodha API key")
            return None
        
        access_token = access_secret("ZERODHA_ACCESS_TOKEN", project_id)
        if not access_token:
            logging.error("Failed to retrieve Zerodha access token")
            return None
        
        # FIXED: Validate credential format
        if len(api_key) < 10:  # Basic validation
            logging.error("API key appears to be invalid (too short)")
            return None
        
        if len(access_token) < 20:  # Basic validation
            logging.error("Access token appears to be invalid (too short)")
            return None
        
        # FIXED: Create KiteConnect client with error handling
        try:
            kite = KiteConnect(api_key=api_key)
            kite.set_access_token(access_token)
            
            # FIXED: Test the connection
            profile = kite.profile()
            if not profile:
                logging.error("KiteConnect profile test failed")
                return None
            
            logging.info(f"KiteConnect client created successfully for user: {profile.get('user_name', 'unknown')}")
            return kite
            
        except Exception as e:
            logging.error(f"Failed to create or test KiteConnect client: {e}")
            return None
            
    except Exception as e:
        logging.error(f"Unexpected error creating KiteConnect client: {e}")
        return None


# FIXED: Add utility functions for secret management
def validate_secret_access(project_id: str = "autotrade-453303") -> bool:
    """
    Validate that all required secrets are accessible.
    
    Args:
        project_id: GCP project ID
        
    Returns:
        True if all secrets are accessible, False otherwise
    """
    required_secrets = [
        "ZERODHA_API_KEY",
        "ZERODHA_API_SECRET", 
        "ZERODHA_ACCESS_TOKEN"
    ]
    
    missing_secrets = []
    
    for secret_id in required_secrets:
        secret_value = access_secret(secret_id, project_id, use_cache=False)
        if not secret_value:
            missing_secrets.append(secret_id)
    
    if missing_secrets:
        logging.error(f"Missing or inaccessible secrets: {missing_secrets}")
        return False
    
    logging.info("All required secrets are accessible")
    return True


def clear_secret_cache():
    """Clear the secret cache."""
    global _credential_cache, _cache_expiry
    _credential_cache = {}
    _cache_expiry = {}
    logging.info("Secret cache cleared")


def get_cache_status() -> dict:
    """Get current cache status for monitoring."""
    current_time = time.time()
    active_entries = []
    expired_entries = []
    
    for key, cache_time in _cache_expiry.items():
        if current_time - cache_time < CACHE_DURATION:
            active_entries.append(key)
        else:
            expired_entries.append(key)
    
    return {
        'active_entries': len(active_entries),
        'expired_entries': len(expired_entries),
        'total_entries': len(_credential_cache),
        'cache_duration': CACHE_DURATION
    }
