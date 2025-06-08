#!/usr/bin/env python3
"""
Debug script to test Secret Manager access and identify authentication issues
"""

import os
import sys
from pathlib import Path

def test_secret_access():
    """Test different methods of accessing secrets"""
    
    print("🔍 DEBUGGING SECRET MANAGER ACCESS")
    print("=" * 50)
    
    # Check environment variables
    print("\n1. ENVIRONMENT VARIABLES:")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    print(f"   GOOGLE_APPLICATION_CREDENTIALS: {google_creds}")
    print(f"   OPENAI_API_KEY (env): {'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET'}")
    
    # Check for key files
    print("\n2. SERVICE ACCOUNT KEY FILES:")
    possible_key_paths = [
        "./keys/autotrade.json",
        "../keys/autotrade.json", 
        "./autotrade.json",
        "./service-account-key.json"
    ]
    
    for path in possible_key_paths:
        if os.path.exists(path):
            print(f"   ✅ Found: {path}")
        else:
            print(f"   ❌ Missing: {path}")
    
    # Test authentication methods
    print("\n3. TESTING AUTHENTICATION METHODS:")
    
    # Method 1: Default credentials
    try:
        from google.auth import default
        credentials, project_id = default()
        print(f"   ✅ Default credentials work: Project {project_id}")
        print(f"      Credential type: {type(credentials).__name__}")
    except Exception as e:
        print(f"   ❌ Default credentials failed: {e}")
    
    # Method 2: Service account from environment
    if google_creds and os.path.exists(google_creds):
        try:
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(google_creds)
            print(f"   ✅ Service account from env works: {google_creds}")
        except Exception as e:
            print(f"   ❌ Service account from env failed: {e}")
    
    # Method 3: Direct secret access test
    print("\n4. TESTING SECRET MANAGER ACCESS:")
    
    try:
        from runner.secret_manager_client import access_secret
        
        # Test the exact same call that's failing
        api_key = access_secret("OPENAI_API_KEY", "autotrade-453303")
        print(f"   ✅ Secret access successful: Key length {len(api_key)}")
        print(f"   Key preview: {api_key[:20]}...")
        
    except Exception as e:
        print(f"   ❌ Secret access failed: {e}")
        
        # Try alternative approach
        try:
            from google.cloud import secretmanager
            from google.auth import default
            
            credentials, _ = default()
            client = secretmanager.SecretManagerServiceClient(credentials=credentials)
            name = f"projects/autotrade-453303/secrets/OPENAI_API_KEY/versions/latest"
            response = client.access_secret_version(name=name)
            api_key = response.payload.data.decode("UTF-8")
            print(f"   ✅ Alternative method works: Key length {len(api_key)}")
            
        except Exception as e2:
            print(f"   ❌ Alternative method also failed: {e2}")
    
    # Method 4: Test with project number instead of ID
    print("\n5. TESTING WITH PROJECT NUMBER:")
    
    try:
        from runner.secret_manager_client import create_secret_manager_client
        
        client = create_secret_manager_client()
        
        # Try with project number (342081360262) instead of project ID
        name = f"projects/342081360262/secrets/OPENAI_API_KEY/versions/latest"
        response = client.access_secret_version(name=name)
        api_key = response.payload.data.decode("UTF-8")
        print(f"   ✅ Project number method works: Key length {len(api_key)}")
        
    except Exception as e:
        print(f"   ❌ Project number method failed: {e}")
    
    print("\n6. RECOMMENDATIONS:")
    print("   Based on the results above:")
    
    # Check if running in different environment
    if sys.platform.startswith('win'):
        print("   • You're running on Windows - container environment may differ")
    
    print("   • Try setting GOOGLE_APPLICATION_CREDENTIALS to a service account key")
    print("   • Verify the application runs with the same credentials as gcloud")
    print("   • Consider using project number instead of project ID")

if __name__ == "__main__":
    test_secret_access() 