#!/usr/bin/env python3
"""
Minimal API server to test dashboard endpoints without Google Cloud dependencies
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

# Completely disable Google Cloud services
os.environ['DISABLE_FIRESTORE'] = 'true'
os.environ['DISABLE_GCS'] = 'true'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
os.environ['GCP_PROJECT_ID'] = ''

app = FastAPI(title="Tron Dashboard API - Test Mode")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/analytics/pnl/daily")
async def analytics_pnl_daily():
    return {
        "timeframe": "7d",
        "total_pnl": 0.0,
        "daily_pnl": [],
        "message": "No trading data available - Paper trading should generate P&L data when strategies are active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/analytics/metrics")
async def analytics_metrics():
    return {
        "total_trades": 0,
        "win_rate": 0.0,
        "avg_profit": 0.0,
        "max_drawdown": 0.0,
        "sharpe_ratio": 0.0,
        "message": "No trading metrics available - Paper trading should generate performance metrics when trades are executed",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/risk/metrics") 
async def risk_metrics():
    return {
        "portfolio_value": 0.0,
        "max_risk_per_trade": 0.0,
        "current_exposure": 0.0,
        "risk_level": "NO_DATA",
        "message": "No risk metrics available - Paper trading should generate risk data when positions are active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/strategy/all")
async def strategy_all():
    return {
        "strategies": [],
        "message": "No strategy data available - Paper trading should generate strategy performance data when strategies are running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/system/health/services")
async def system_health_services():
    import shutil
    import os
    
    # Get actual system metrics
    total, used, free = shutil.disk_usage("/")
    disk_usage_pct = (used / total) * 100
    
    # Get process info
    import platform
    
    return {
        "status": "healthy",
        "services": [
            {"name": "API Server", "status": "active", "uptime": "active"},
            {"name": "Database", "status": "disconnected", "note": "Paper trading mode - Firestore disabled"},
            {"name": "Risk Monitor", "status": "active", "note": "Paper trading mode"}
        ],
        "system_metrics": {
            "disk_usage_pct": round(disk_usage_pct, 2),
            "platform": platform.system(),
            "python_version": platform.python_version(),
            "architecture": platform.machine()
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/trade/positions/live") 
async def trade_positions_live():
    return {
        "positions": [],
        "message": "No live positions available - Paper trading should generate position data when trades are executed",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/cognitive/summary")
async def cognitive_summary():
    return {
        "status": "active",
        "insights": [],
        "confidence": 0.0,
        "message": "No cognitive insights available - Paper trading should generate market insights when strategies are analyzing data",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/logs/sources")
async def logs_sources():
    return {
        "sources": [],
        "message": "No log sources available - Paper trading should generate log data when trading operations are active",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("🚀 Starting Simple Tron Dashboard API Test Server...")
    print("📡 API available at: http://localhost:8001")
    print("🔧 All Google Cloud services disabled")
    print("📊 Serving demo data for dashboard testing")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info") 