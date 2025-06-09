#!/usr/bin/env python3
"""
Dashboard Restart Script
Cleanly restarts the Streamlit dashboard in offline mode
"""

import os
import sys
import subprocess
import time
import signal
from pathlib import Path

def kill_existing_streamlit():
    """Kill any existing Streamlit processes"""
    try:
        if os.name == 'nt':  # Windows
            subprocess.run(['taskkill', '/f', '/im', 'streamlit.exe'], 
                         capture_output=True, text=True)
        else:  # Unix/Linux/Mac
            subprocess.run(['pkill', '-f', 'streamlit'], 
                         capture_output=True, text=True)
        time.sleep(2)
        print("✅ Existing Streamlit processes terminated")
    except Exception as e:
        print(f"⚠️ Note: {e}")

def start_dashboard():
    """Start the dashboard in offline mode"""
    print("🚀 Starting Tron Trading Dashboard...")
    print("📍 URL: http://localhost:8501")
    print("🔌 Mode: Offline (No GCP dependencies)")
    print("✨ Features: System Health, Live Trades, Cognitive Insights")
    print("\n" + "="*50)
    
    try:
        # Change to project directory
        project_root = Path(__file__).parent
        os.chdir(project_root)
        
        # Start Streamlit dashboard
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            'dashboard/main.py',
            '--server.port', '8501',
            '--server.headless', 'true',
            '--browser.gatherUsageStats', 'false'
        ], check=True)
        
    except KeyboardInterrupt:
        print("\n🛑 Dashboard stopped by user")
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

if __name__ == "__main__":
    kill_existing_streamlit()
    start_dashboard() 