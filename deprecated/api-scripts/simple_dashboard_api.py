#!/usr/bin/env python3
"""
Simple dashboard API with mock data for testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import uvicorn

app = FastAPI(title="Tron Dashboard API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock trade data
@app.get("/api/trade/summary/daily")
async def get_daily_summary():
    return {
        'total_pnl': 15420.50,
        'win_rate': 67.5,
        'active_trades': 3,
        'total_trades': 18,
        'day_start_time': (datetime.now() - timedelta(hours=6)).isoformat(),
        'total_profit': 22680.75,
        'total_loss': -7260.25,
        'largest_win': 4850.00,
        'largest_loss': -2340.00,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/trade/summary/positions")
async def get_summary_positions():
    return {
        'total_exposure': 145250.75,
        'margin_usage_pct': 68.5,
        'available_margin': 85420.25,
        'day_pnl': 15420.50,
        'unrealized_pnl': 220.75,
        'realized_pnl': 15199.75,
        'max_profit_today': 4850.00,
        'max_loss_today': -2340.00,
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/trade/summary/strategy")
async def get_summary_strategy():
    return {
        'top_strategy': {'name': 'Opening Range Breakout'},
        'active_strategies': 4,
        'strategy_performance': [
            {'name': 'ORB', 'pnl': 8420.50, 'win_rate': 72.5, 'trades': 8},
            {'name': 'Scalping', 'pnl': 3250.25, 'win_rate': 65.0, 'trades': 6},
            {'name': 'VWAP', 'pnl': 2890.75, 'win_rate': 58.3, 'trades': 3},
            {'name': 'Range Reversal', 'pnl': 859.00, 'win_rate': 50.0, 'trades': 1}
        ],
        'timestamp': datetime.now().isoformat()
    }

# Mock system data
@app.get("/api/system/status")
async def get_system_status():
    return {
        'overall_status': 'healthy',
        'backend_service': 'running',
        'database_connection': 'connected',
        'api_endpoints': 'available',
        'timestamp': datetime.now().isoformat()
    }

@app.get("/api/system/health")
async def get_system_health():
    return {
        'status': 'healthy',
        'uptime_hours': 24.5,
        'last_check': datetime.now().isoformat(),
        'cpu_usage': 35.2,
        'memory_usage': 58.7,
        'disk_usage': 42.1
    }

@app.get("/api/system/metrics")
async def get_system_metrics():
    return {
        'cpu_usage': 35.2,
        'memory_usage': 58.7,
        'memory_available_gb': 8.5,
        'disk_usage': 42.1,
        'network_connections': 145,
        'timestamp': datetime.now().isoformat()
    }

# Mock cognitive data
@app.get("/api/cognitive/summary")
async def get_cognitive_summary():
    return {
        "status": "active",
        "ai_models_active": 3,
        "insights_generated": 45,
        "confidence_score": 0.87,
        "last_analysis": (datetime.now() - timedelta(minutes=2)).isoformat(),
        "market_sentiment": "bullish",
        "risk_assessment": "moderate",
        "recommendation_accuracy": 0.82,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/cognitive/health")
async def get_cognitive_health():
    return {
        "status": "healthy",
        "uptime": "2h 34m",
        "memory_usage": 0.67,
        "cpu_usage": 0.23,
        "models_loaded": 3,
        "errors_last_hour": 0,
        "api_response_time": 0.145,
        "last_health_check": datetime.now().isoformat(),
        "components": {
            "sentiment_analyzer": "healthy",
            "risk_predictor": "healthy", 
            "pattern_detector": "healthy",
            "recommendation_engine": "healthy"
        }
    }

@app.get("/")
async def root():
    return {"message": "Tron Dashboard API is running", "status": "healthy"}

if __name__ == "__main__":
    print("Starting Simple Tron Dashboard API...")
    print("API available at: http://localhost:8001")
    print("Docs available at: http://localhost:8001/docs")
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=False)