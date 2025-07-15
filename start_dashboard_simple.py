#!/usr/bin/env python3
"""
Simple Dashboard API starter that bypasses authentication issues
"""
import os
import sys
import uvicorn

# Disable all Google Cloud services to avoid authentication issues
os.environ["DISABLE_GCS"] = "true"
os.environ["DISABLE_FIRESTORE"] = "true"
os.environ["GCP_PROJECT_ID"] = "demo-project"

# Set demo mode
os.environ["DEMO_MODE"] = "true"

# Simple main function
def main():
    print("Starting Tron Dashboard API (Simple Mode)...")
    print("API will be available at: http://localhost:8001")
    print("API docs will be available at: http://localhost:8001/docs")
    print("Google Cloud services: DISABLED")
    print("Mode: DEMO with sample data")
    
    # Import and start the app
    try:
        from dashboard_api.main import app
        uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 