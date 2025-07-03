#!/usr/bin/env python3
"""
Simple script to start the dashboard API with proper paths
"""
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Now import and run the dashboard
if __name__ == "__main__":
    from dashboard_api.main import app
    import uvicorn
    
    print("Starting Tron Dashboard API...")
    print("API will be available at: http://localhost:8001")
    print("API docs will be available at: http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)