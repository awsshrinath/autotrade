#!/usr/bin/env python3
"""
Startup script for the fixed main runner
Sets up proper authentication and runs the enhanced main runner
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup environment variables for proper authentication"""
    
    print("🔧 Setting up environment for fixed main runner...")
    
    # Service account authentication - use environment variable instead of local file
    key_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not key_file and os.getenv('GCP_SA_KEY'):
        # If running in CI/CD with GCP_SA_KEY secret, create temporary key file
        import tempfile
        import base64
        
        try:
            # Decode the base64 encoded key from GitHub secret
            key_content = base64.b64decode(os.getenv('GCP_SA_KEY')).decode('utf-8')
            
            # Create temporary key file
            with tempfile.NamedTemporaryFile(mode='w', suffix='-sa-key.json', delete=False) as temp_key:
                temp_key.write(key_content)
                key_file = temp_key.name
            
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_file
            print(f"✅ Using service account key from GCP_SA_KEY secret")
            
        except Exception as e:
            print(f"❌ Failed to process GCP_SA_KEY secret: {e}")
            key_file = None
    elif not key_file:
        # Fallback to local key file for local development
        local_key_file = "./gpt-runner-sa-key.json"
        if os.path.exists(local_key_file):
            key_file = local_key_file
            print(f"✅ Using local service account key file")
        else:
            print(f"⚠️ No service account key available")
            key_file = None
    
    # Set paper trading mode
    os.environ["PAPER_TRADE"] = "true"
    print("✅ Set PAPER_TRADE=true")
    
    # Set any other required environment variables
    if not os.environ.get("OPENAI_API_KEY"):
        print("ℹ️ OPENAI_API_KEY not set in environment (will use Secret Manager)")
    
    print("🔧 Environment setup completed!\n")

def run_main_runner():
    """Run the fixed main runner"""
    
    print("🚀 Starting the fixed main runner...")
    print("=" * 60)
    
    try:
        # Import and run the fixed main runner
        from runner.main_runner_fixed import main
        main()
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        
    except Exception as e:
        print(f"\n❌ Error running main runner: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🏁 Main runner completed")

def main():
    """Main function"""
    
    print("🎯 TRON AUTOTRADE - FIXED STARTUP SCRIPT")
    print("=" * 50)
    
    # Setup environment
    setup_environment()
    
    # Run the main runner
    run_main_runner()

if __name__ == "__main__":
    main() 