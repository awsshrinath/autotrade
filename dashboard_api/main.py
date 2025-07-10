from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import routers - We will use the legacy endpoints directly for now
from dashboard_api.services import system_service, cognitive_service, real_trade_service
from dashboard_api.routers import auth

# Import optional JWT middleware and rate limiting
from dashboard_api.security.jwt_middleware import OptionalJWTMiddleware
from dashboard_api.security.rate_limiting import limiter, custom_rate_limit_handler, get_rate_limit_status, conditional_rate_limit
from slowapi.errors import RateLimitExceeded
from fastapi import Request

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

# Add optional JWT authentication middleware
# This middleware can be toggled on/off via environment variables
# Default is OFF to maintain backward compatibility
app.add_middleware(OptionalJWTMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)

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

@app.get("/api/cognitive/insights/trade")
async def cognitive_trade_insights():
    service = cognitive_service.get_cognitive_service()
    return await service.get_trade_insights()

# Enhanced cognitive endpoints
@app.get("/api/cognitive/logs/summary")
@conditional_rate_limit("cognitive")
async def cognitive_log_summary(request: Request, source: str, identifier: str):
    """Generate AI-powered summary of logs from GCS, Firestore, or K8s."""
    service = cognitive_service.get_cognitive_service()
    return await service.get_log_summary(source=source, identifier=identifier)

@app.get("/api/cognitive/market/sentiment")
@conditional_rate_limit("cognitive")
async def cognitive_market_sentiment(request: Request, symbol: str = "NIFTY"):
    """Get AI-powered market sentiment analysis for a symbol."""
    service = cognitive_service.get_cognitive_service()
    return await service.analyze_market_sentiment(symbol=symbol)

@app.post("/api/cognitive/cache/clear")
async def cognitive_clear_cache():
    """Clear the cognitive insights cache."""
    service = cognitive_service.get_cognitive_service()
    return service.clear_cache()

@app.get("/api/cognitive/status")
async def cognitive_status():
    """Get comprehensive cognitive system status and capabilities."""
    service = cognitive_service.get_cognitive_service()
    summary = await service.get_cognitive_summary()
    health = await service.get_cognitive_health()
    
    return {
        "service_status": "enabled" if service.is_enabled else "disabled",
        "ai_models": {
            "primary": getattr(service, 'primary_model', 'N/A'),
            "fallback": getattr(service, 'fallback_model', 'N/A')
        },
        "summary": summary,
        "health": health,
        "capabilities": {
            "log_analysis": True,
            "market_sentiment": True,
            "trade_insights": True,
            "caching": True
        },
        "timestamp": summary.get("timestamp")
    }

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

# New GCS and Log Service endpoints for testing
@app.get("/api/logs/status")
async def logs_status():
    """Get the status of log service connections (GCS, Firestore, K8s)."""
    service = system_service.get_system_service()
    return service.get_log_service_status()

@app.get("/api/logs/gcs/files")
@conditional_rate_limit("logs")
async def list_gcs_files(request: Request, prefix: str = None, limit: int = 20, 
                        date_from: str = None, date_to: str = None,
                        pattern: str = None, page_token: str = None):
    """List log files from GCS bucket with advanced filtering and pagination."""
    service = system_service.get_system_service()
    return await service.get_gcs_log_files_paginated(
        prefix=prefix, 
        page_size=limit,
        date_from=date_from,
        date_to=date_to,
        pattern=pattern,
        page_token=page_token
    )

@app.get("/api/logs/gcs/content")
@conditional_rate_limit("logs")
async def get_gcs_file_content(request: Request, file_path: str, search_term: str = None,
                              log_level: str = None, lines_limit: int = None,
                              compressed: bool = False):
    """Get content of a specific log file from GCS with filtering and optional compression."""
    service = system_service.get_system_service()
    
    if compressed:
        return await service.get_compressed_log_content(
            file_path=file_path,
            search_term=search_term,
            log_level=log_level,
            lines_limit=lines_limit or 1000
        )
    else:
        return await service.get_gcs_file_content(
            file_path=file_path,
            search_term=search_term,
            log_level=log_level,
            lines_limit=lines_limit
        )

@app.get("/api/logs/gcs/stream")
async def stream_gcs_file_content(file_path: str, start_byte: int = 0, 
                                 chunk_size: int = None):
    """Stream large log file content in chunks for efficient processing."""
    from starlette.responses import StreamingResponse
    
    service = system_service.get_system_service()
    
    async def generate_chunks():
        async for chunk in service.stream_gcs_log_content(file_path, start_byte, chunk_size):
            yield chunk
    
    return StreamingResponse(
        generate_chunks(), 
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={file_path.split('/')[-1]}",
            "X-File-Path": file_path
        }
    )

@app.get("/api/logs/firestore")
async def get_firestore_logs(limit: int = 20, component: str = None,
                           log_level: str = None, date_from: str = None,
                           date_to: str = None, cursor: str = None):
    """Get recent logs from Firestore with advanced filtering and pagination."""
    service = system_service.get_system_service()
    return await service.get_firestore_logs_batch(
        limit=limit,
        component=component,
        log_level=log_level,
        date_from=date_from,
        date_to=date_to,
        cursor=cursor
    )

@app.get("/api/logs/k8s/pods")
async def list_k8s_pods():
    """List Kubernetes pods in the configured namespace."""
    service = system_service.get_system_service()
    return await service.get_k8s_pods()

@app.get("/api/logs/k8s/pod_logs")
async def get_k8s_pod_logs(pod_name: str, lines: int = 50,
                          since_seconds: int = None, follow: bool = False,
                          search_term: str = None, log_level: str = None):
    """Get logs for a specific Kubernetes pod with filtering."""
    service = system_service.get_system_service()
    return await service.get_k8s_pod_logs(
        pod_name=pod_name,
        lines=lines,
        since_seconds=since_seconds,
        follow=follow,
        search_term=search_term,
        log_level=log_level
    )

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Tron Dashboard API"}

@app.get("/health", tags=["Health Check"])
async def health_check():
    """Simple health check endpoint for Kubernetes probes."""
    return {"status": "ok"}

# Auth status endpoint for monitoring
@app.get("/api/auth/system", tags=["Authentication"])
async def auth_system_info():
    """Get authentication system information and status"""
    from dashboard_api.security.jwt_middleware import get_auth_status
    return get_auth_status()

# Rate limiting status endpoint
@app.get("/api/rate-limit/status", tags=["Rate Limiting"])
async def rate_limit_status():
    """Get rate limiting configuration and status"""
    return get_rate_limit_status()

# For running the app directly during development
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 