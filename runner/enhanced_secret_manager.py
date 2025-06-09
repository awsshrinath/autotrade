# runner/enhanced_secret_manager.py

import os
import logging
from typing import Optional

try:
    from google.auth import default
    from google.cloud import secretmanager
    from google.oauth2 import service_account
    GCP_AVAILABLE = True
except ImportError:
    GCP_AVAILABLE = False

class EnhancedSecretManager:
    """Enhanced Secret Manager with robust authentication and fallbacks"""
    
    def __init__(self, logger=None, project_id="autotrade-453303"):
        self.logger = logger or logging.getLogger(__name__)
        self.project_id = project_id
        self.project_number = "342081360262"  # Known project number
        self.client = None
        self.available = False
        
        if GCP_AVAILABLE:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Secret Manager client with multiple authentication methods"""
        
        # Multiple authentication methods for flexibility
        # In Kubernetes, prioritize pod service account first
        self.auth_methods = [
            self._auth_with_default,             # Default pod service account (Kubernetes-native)
            self._auth_with_gcp_sa_key_env,      # GitHub secret  
            self._auth_with_service_account_key,  # Local key file
            self._auth_with_environment,         # Environment-based
        ]
        
        for method in self.auth_methods:
            try:
                client = method()
                if client:
                    self.client = client
                    self.available = True
                    self._log_success(f"Secret Manager initialized with {method.__name__}")
                    return
            except Exception as e:
                self._log_warning(f"{method.__name__} failed: {e}")
        
        self._log_error("All authentication methods failed")
    
    def _auth_with_gcp_sa_key_env(self):
        """Try authentication with GCP_SA_KEY environment variable"""
        
        gcp_sa_key = os.getenv("GCP_SA_KEY")
        if gcp_sa_key and gcp_sa_key != "emergency_mode_no_key":
            try:
                import base64
                import tempfile
                import json
                
                # Decode the base64 encoded key from GitHub secret
                key_content = base64.b64decode(gcp_sa_key).decode('utf-8')
                
                # Validate it's a proper JSON service account key
                key_data = json.loads(key_content)
                if 'private_key' not in key_data or 'client_email' not in key_data:
                    raise ValueError("Invalid service account key format")
                
                # Create temporary key file
                with tempfile.NamedTemporaryFile(mode='w', suffix='-sa-key.json', delete=False) as temp_key:
                    temp_key.write(key_content)
                    temp_key_path = temp_key.name
                
                # Use the temporary key file for authentication
                credentials = service_account.Credentials.from_service_account_file(temp_key_path)
                client = secretmanager.SecretManagerServiceClient(credentials=credentials)
                
                # Test the client
                self._test_client(client)
                self._log_info("Using GCP_SA_KEY from environment")
                
                # Clean up temporary file
                try:
                    os.unlink(temp_key_path)
                except:
                    pass
                
                return client
                
            except Exception as e:
                self._log_warning(f"GCP_SA_KEY authentication failed: {e}")
        
        return None
    
    def _auth_with_service_account_key(self):
        """Try authentication with service account key file"""
        
        # Look for service account key files
        key_paths = [
            "./gpt-runner-sa-key.json",
            "./autotrade.json", 
            "./keys/autotrade.json",
            "./service-account-key.json",
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        ]
        
        for key_path in key_paths:
            if key_path and os.path.exists(key_path):
                try:
                    credentials = service_account.Credentials.from_service_account_file(key_path)
                    client = secretmanager.SecretManagerServiceClient(credentials=credentials)
                    
                    # Test the client
                    self._test_client(client)
                    self._log_info(f"Using service account key: {key_path}")
                    return client
                    
                except Exception as e:
                    self._log_warning(f"Service account key {key_path} failed: {e}")
        
        return None
    
    def _auth_with_environment(self):
        """Try authentication with environment variables"""
        
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if google_creds and os.path.exists(google_creds):
            try:
                credentials = service_account.Credentials.from_service_account_file(google_creds)
                client = secretmanager.SecretManagerServiceClient(credentials=credentials)
                
                # Test the client
                self._test_client(client)
                self._log_info(f"Using environment credentials: {google_creds}")
                return client
                
            except Exception as e:
                self._log_warning(f"Environment credentials failed: {e}")
        
        return None
    
    def _auth_with_default(self):
        """Try authentication with default credentials (without impersonation) - Kubernetes-native"""
        
        try:
            # In Kubernetes, use the default service account attached to the pod
            # This should automatically work without any explicit credentials
            import google.auth
            
            # Get default credentials (this uses the pod's service account in K8s)
            credentials, project = google.auth.default()
            
            # Create client with the default credentials (no impersonation)
            client = secretmanager.SecretManagerServiceClient(credentials=credentials)
            
            # Update project ID if discovered from environment
            if project and not self.project_id:
                self.project_id = project
                
            # Test the client
            self._test_client(client)
            self._log_info(f"Using default pod service account credentials for project: {project or self.project_id}")
            return client
            
        except Exception as e:
            self._log_warning(f"Default pod service account failed: {e}")
            
            # Fallback: Try explicit default without any configuration
            try:
                # Just create the client without any explicit credentials
                # This relies entirely on the pod's service account
                client = secretmanager.SecretManagerServiceClient()
                
                # Test the client
                self._test_client(client)
                self._log_info("Using minimal default credentials (pod service account)")
                return client
                
            except Exception as e2:
                self._log_warning(f"Minimal default credentials also failed: {e2}")
        
        return None
    
    def _test_client(self, client):
        """Test if the client can access secrets"""
        
        # Try to list secrets as a quick test
        try:
            request = secretmanager.ListSecretsRequest(parent=f"projects/{self.project_id}")
            # Just check if we can make the request
            response = client.list_secrets(request=request, timeout=10)
            # Try to get at least one result
            next(iter(response), None)
            
        except Exception as e:
            # If listing fails, try with project number
            try:
                request = secretmanager.ListSecretsRequest(parent=f"projects/{self.project_number}")
                response = client.list_secrets(request=request, timeout=10)
                next(iter(response), None)
                # If this works, update project reference
                self.project_id = self.project_number
                
            except Exception as e2:
                raise Exception(f"Client test failed with both project ID and number: {e}, {e2}")
    
    def access_secret(self, secret_id: str) -> Optional[str]:
        """Access a secret with multiple fallback approaches"""
        
        if not self.available or not self.client:
            self._log_error("Secret Manager not available")
            return None
        
        # Try different resource name formats
        resource_formats = [
            f"projects/{self.project_id}/secrets/{secret_id}/versions/latest",
            f"projects/{self.project_number}/secrets/{secret_id}/versions/latest",
        ]
        
        for resource_name in resource_formats:
            try:
                response = self.client.access_secret_version(name=resource_name)
                secret_value = response.payload.data.decode("UTF-8")
                self._log_success(f"Successfully accessed secret: {secret_id}")
                return secret_value
                
            except Exception as e:
                self._log_warning(f"Failed to access {secret_id} with {resource_name}: {e}")
        
        self._log_error(f"All attempts to access secret {secret_id} failed")
        return None
    
    def get_openai_api_key(self) -> Optional[str]:
        """Get OpenAI API key with fallbacks"""
        
        # First try environment variable
        env_key = os.getenv("OPENAI_API_KEY")
        if env_key and env_key != "emergency_mode_no_key":
            self._log_info("Using OpenAI API key from environment")
            return env_key
        
        # Then try Secret Manager
        secret_key = self.access_secret("OPENAI_API_KEY")
        if secret_key:
            return secret_key
        
        # Try alternative secret name
        alt_secret_key = self.access_secret("openai-secret")
        if alt_secret_key:
            return alt_secret_key
        
        self._log_error("No OpenAI API key found in any source")
        return None
    
    def _log_success(self, message: str):
        """Log success message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"✅ [SecretManager] {message}")
        else:
            self.logger.info(f"[SecretManager] {message}")
    
    def _log_info(self, message: str):
        """Log info message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"ℹ️ [SecretManager] {message}")
        else:
            self.logger.info(f"[SecretManager] {message}")
    
    def _log_warning(self, message: str):
        """Log warning message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"⚠️ [SecretManager] {message}")
        else:
            self.logger.warning(f"[SecretManager] {message}")
    
    def _log_error(self, message: str):
        """Log error message"""
        if hasattr(self.logger, 'log_event'):
            self.logger.log_event(f"❌ [SecretManager] {message}")
        else:
            self.logger.error(f"[SecretManager] {message}")


# Convenience functions for backward compatibility
def create_enhanced_secret_manager(logger=None, project_id="autotrade-453303"):
    """Create enhanced secret manager instance"""
    return EnhancedSecretManager(logger=logger, project_id=project_id)

def access_secret_enhanced(secret_id: str, project_id="autotrade-453303", logger=None) -> Optional[str]:
    """Enhanced secret access function"""
    manager = EnhancedSecretManager(logger=logger, project_id=project_id)
    return manager.access_secret(secret_id)

def get_openai_key_enhanced(logger=None) -> Optional[str]:
    """Get OpenAI API key with enhanced error handling"""
    manager = EnhancedSecretManager(logger=logger)
    return manager.get_openai_api_key()


# Test function
def test_enhanced_secret_manager():
    """Test the enhanced secret manager"""
    
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🧪 TESTING ENHANCED SECRET MANAGER")
    print("=" * 40)
    
    manager = EnhancedSecretManager(logger=logger)
    
    print(f"\nSecret Manager Available: {manager.available}")
    print(f"Project ID: {manager.project_id}")
    
    if manager.available:
        # Test OpenAI key access
        openai_key = manager.get_openai_api_key()
        if openai_key:
            print(f"✅ OpenAI Key: {openai_key[:20]}... (length: {len(openai_key)})")
        else:
            print("❌ OpenAI Key: Failed to retrieve")
        
        # Test other secrets
        for secret_name in ["ZERODHA_API_KEY", "ZERODHA_ACCESS_TOKEN"]:
            secret_value = manager.access_secret(secret_name)
            if secret_value:
                print(f"✅ {secret_name}: Retrieved successfully")
            else:
                print(f"❌ {secret_name}: Failed to retrieve")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_enhanced_secret_manager() 