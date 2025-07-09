from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers - We will use the legacy endpoints directly for now
from dashboard_api.services import system_service, cognitive_service, real_trade_service
from dashboard_api.routers import auth

# Initialize FastAPI app
app = FastAPI(
    title="Tron Dashboard API",
    description="Backend service for the Tron Trading Dashboard.",
    version="1.0.0",
)

# CORS Middleware to allow requests from the Next.js frontend
import os

# Get environment-specific origins
environment = os.getenv("ENVIRONMENT", "development")

if environment == "production":
    origins = [
        "https://tron-trading.com",
        "https://www.tron-trading.com",
        "https://dashboard.tron-trading.com",
        "https://api.tron-trading.com",
        "http://localhost:3000",
    ]
else:
    origins = [
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "*",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Main API Endpoints ---
# The frontend is currently hitting these legacy endpoints.
# We will make them the primary endpoints and use the real data services.

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])

@app.get("/api/system/status")
async def system_status():
    service = system_service.get_system_service()
    return await service.get_system_status()

@app.get("/api/system/health")
async def system_health():
    service = system_service.get_system_service()
    return await service.get_system_health()

@app.get("/api/system/metrics")
async def system_metrics():
    service = system_service.get_system_service()
    return service.get_system_metrics()

@app.get("/api/cognitive/summary")
async def cognitive_summary():
    service = cognitive_service.get_cognitive_service()
    return await service.get_cognitive_summary()

@app.get("/api/cognitive/health")
async def cognitive_health():
    service = cognitive_service.get_cognitive_service()
    return await service.get_cognitive_health()

@app.get("/api/trade/summary/daily")
async def trade_summary_daily():
    service = real_trade_service.get_trade_service()
    return await service.get_daily_summary()

@app.get("/api/trade/summary/positions")
async def trade_summary_positions():
    service = real_trade_service.get_trade_service()
    return await service.get_summary_positions()

@app.get("/api/trade/summary/strategy")
async def trade_summary_strategy():
    service = real_trade_service.get_trade_service()
    return await service.get_summary_strategy()

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Tron Dashboard API"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Simple health check endpoint for Kubernetes probes."""
    return {"status": "ok"}

# For running the app directly during development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 