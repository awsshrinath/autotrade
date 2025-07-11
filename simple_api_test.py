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
        "total_pnl": 4500.0,
        "daily_pnl": [
            {"date": "2025-01-05", "pnl": 1200.0},
            {"date": "2025-01-06", "pnl": 800.0},
            {"date": "2025-01-07", "pnl": 2500.0}
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/analytics/metrics")
async def analytics_metrics():
    return {
        "total_trades": 25,
        "win_rate": 68.0,
        "avg_profit": 180.0,
        "max_drawdown": -850.0,
        "sharpe_ratio": 1.85,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/risk/metrics") 
async def risk_metrics():
    return {
        "portfolio_value": 125000.0,
        "max_risk_per_trade": 2500.0,
        "current_exposure": 15000.0,
        "risk_level": "MODERATE",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/strategy/all")
async def strategy_all():
    return {
        "strategies": [
            {
                "name": "Opening Range Breakout",
                "status": "active",
                "pnl": 2200.0,
                "trades": 12,
                "win_rate": 75.0
            },
            {
                "name": "VWAP Reversion", 
                "status": "active",
                "pnl": 1800.0,
                "trades": 8,
                "win_rate": 62.5
            },
            {
                "name": "Range Scalping",
                "status": "active", 
                "pnl": 500.0,
                "trades": 5,
                "win_rate": 60.0
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/system/health/services")
async def system_health_services():
    return {
        "status": "healthy",
        "services": [
            {"name": "API Server", "status": "active"},
            {"name": "Database", "status": "active"},
            {"name": "Risk Monitor", "status": "active"}
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/trade/positions/live") 
async def trade_positions_live():
    return {
        "positions": [
            {
                "symbol": "RELIANCE",
                "quantity": 100,
                "entry_price": 2500.0,
                "current_price": 2520.0,
                "pnl": 2000.0,
                "status": "open"
            },
            {
                "symbol": "TCS",
                "quantity": 50,
                "entry_price": 3200.0,
                "current_price": 3180.0,
                "pnl": -1000.0,
                "status": "open"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/cognitive/summary")
async def cognitive_summary():
    return {
        "status": "active",
        "insights": [
            "Market showing bullish momentum in tech sector",
            "Risk levels within acceptable parameters",
            "Strategy performance above average"
        ],
        "confidence": 0.85,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v1/logs/sources")
async def logs_sources():
    return {
        "sources": [
            {"name": "Trading System", "status": "active", "last_update": datetime.now().isoformat()},
            {"name": "Risk Monitor", "status": "active", "last_update": datetime.now().isoformat()},
            {"name": "Market Data", "status": "active", "last_update": datetime.now().isoformat()}
        ],
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