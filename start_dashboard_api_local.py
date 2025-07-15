#!/usr/bin/env python3
"""
Local Dashboard API Server - Modified to avoid GCP authentication issues
"""
import os
import sys
import uvicorn
from pathlib import Path

# Disable Google Cloud services to avoid authentication issues
os.environ['DISABLE_FIRESTORE'] = 'true'
os.environ['DISABLE_GCS'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Starting Tron Dashboard API (Local Mode - No GCP)...")
print("API will be available at: http://localhost:8001")
print("API docs will be available at: http://localhost:8001/docs")
print("Note: Google Cloud services disabled for local testing")

if __name__ == "__main__":
    try:
        # Import the FastAPI app
        from dashboard_api.main import app
        
        # Run the server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            reload=False,  # Disable reload to avoid issues
            log_level="info"
        )
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1) 