"""
Main FastAPI application for the Log Aggregator.
Initializes the FastAPI app, includes routers, and defines global dependencies.
"""

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import structlog
from datetime import datetime

from .utils.config import get_config
# Routers will be imported here later - temporarily disabled for debugging
# from .routers import gcs_router, firestore_router, k8s_router, summary_router
# from .routers import gcs_router, firestore_router, k8s_router, summary_router

logger = structlog.get_logger(__name__)

app_config = get_config()

app = FastAPI(
    title="Log Aggregator API",
    description="API service to collect, aggregate, and summarize logs from various sources.",
    version="0.1.0",
    openapi_url=f"{app_config.api_prefix}/openapi.json",
    docs_url=f"{app_config.api_prefix}/docs",
    redoc_url=f"{app_config.api_prefix}/redoc"
)

# CORS Middleware
if app_config.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip() for origin in app_config.cors_origins.split(",")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logger.error(f"Request validation error: {exc_str}", request_url=str(request.url))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

# Placeholder for root endpoint
@app.get(f"{app_config.api_prefix}/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the Log Aggregator API!"}

# Basic health check endpoint
@app.get(f"{app_config.api_prefix}/health", tags=["Health"])
async def health_check():
    # Basic health check - just return that the API is running
    return {
        "status": "ok", 
        "message": "Log Aggregator API is running", 
        "version": "0.1.0"
    }

# Include routers (temporarily disabled for debugging)
# app.include_router(gcs_router.router, prefix=f"{app_config.api_prefix}/logs/gcs", tags=["GCS Logs"])
# app.include_router(firestore_router.router, prefix=f"{app_config.api_prefix}/logs/firestore", tags=["Firestore Logs"])
# app.include_router(k8s_router.router, prefix=f"{app_config.api_prefix}/logs/k8s", tags=["Kubernetes Logs"])
# app.include_router(summary_router.router, prefix=f"{app_config.api_prefix}/summary", tags=["Log Summarization"])

# app.include_router(gcs_router.router, prefix=f"{app_config.api_prefix}/gcs", tags=["GCS Logs"])
# app.include_router(firestore_router.router, prefix=f"{app_config.api_prefix}/firestore", tags=["Firestore Logs"])
# app.include_router(k8s_router.router, prefix=f"{app_config.api_prefix}/k8s", tags=["Kubernetes Logs"])
# app.include_router(summary_router.router, prefix=f"{app_config.api_prefix}/summary", tags=["Log Summarization"])

if __name__ == "__main__":
    logger.info("Starting Log Aggregator API with Uvicorn...")
    uvicorn.run(
        app,  # Use the app directly instead of string import
        host=app_config.api_host,
        port=app_config.api_port,
        reload=False,  # Disable reload to avoid multiprocessing issues  
        log_level=app_config.log_level.lower()
    ) 