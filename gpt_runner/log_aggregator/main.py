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

from .utils.config import get_config
# Routers will be imported here later
# from .routers import gcs_router, firestore_router, k8s_router, summary_router
from .routers import gcs_router, firestore_router, k8s_router, summary_router

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

# Placeholder for health check endpoint
@app.get(f"{app_config.api_prefix}/health", tags=["Health"])
async def health_check():
    # In a real application, you might check dependencies like database connections
    # For a more detailed health check, we can test service connections
    from ..services.gcs_service import get_gcs_service
    from ..services.firestore_service import get_firestore_service
    from ..services.k8s_service import get_k8s_service
    from ..services.gpt_service import get_gpt_service

    service_status = {
        "gcs_service": "not_tested",
        "firestore_service": "not_tested",
        "k8s_service": "not_tested",
        "gpt_service_openai": "not_tested",
    }
    overall_healthy = True

    try:
        gcs_available = await get_gcs_service().test_connection()
        service_status["gcs_service"] = "ok" if gcs_available else "error"
        if not gcs_available: overall_healthy = False
    except Exception as e:
        logger.warning("GCS health check failed", error=str(e))
        service_status["gcs_service"] = "error"
        overall_healthy = False
    
    try:
        firestore_available = await get_firestore_service().test_connection()
        service_status["firestore_service"] = "ok" if firestore_available else "error"
        if not firestore_available: overall_healthy = False
    except Exception as e:
        logger.warning("Firestore health check failed", error=str(e))
        service_status["firestore_service"] = "error"
        overall_healthy = False

    try:
        k8s_available = await get_k8s_service().test_connection()
        service_status["k8s_service"] = "ok" if k8s_available else "error"
        if not k8s_available: overall_healthy = False
    except Exception as e:
        logger.warning("Kubernetes health check failed", error=str(e))
        service_status["k8s_service"] = "error"
        overall_healthy = False

    try:
        gpt_connections = await get_gpt_service().test_connection()
        service_status["gpt_service_openai"] = "ok" if gpt_connections.get("openai") else "error"
        if not gpt_connections.get("openai"): overall_healthy = False
    except Exception as e:
        logger.warning("GPT service health check failed", error=str(e))
        service_status["gpt_service_openai"] = "error"
        overall_healthy = False

    if overall_healthy:
        return {"status": "ok", "message": "All services are healthy", "dependencies": service_status}
    else:
        # If any critical service is down, we might return a 503 Service Unavailable
        # For now, just indicating in the message.
        return {"status": "degraded", "message": "One or more dependent services are not healthy.", "dependencies": service_status}

# Include routers (placeholders for now)
# app.include_router(gcs_router.router, prefix=f"{app_config.api_prefix}/logs/gcs", tags=["GCS Logs"])
# app.include_router(firestore_router.router, prefix=f"{app_config.api_prefix}/logs/firestore", tags=["Firestore Logs"])
# app.include_router(k8s_router.router, prefix=f"{app_config.api_prefix}/logs/k8s", tags=["Kubernetes Logs"])
# app.include_router(summary_router.router, prefix=f"{app_config.api_prefix}/summary", tags=["Log Summarization"])

app.include_router(gcs_router.router, prefix=f"{app_config.api_prefix}/gcs", tags=["GCS Logs"])
app.include_router(firestore_router.router, prefix=f"{app_config.api_prefix}/firestore", tags=["Firestore Logs"])
app.include_router(k8s_router.router, prefix=f"{app_config.api_prefix}/k8s", tags=["Kubernetes Logs"])
app.include_router(summary_router.router, prefix=f"{app_config.api_prefix}/summary", tags=["Log Summarization"])

if __name__ == "__main__":
    logger.info("Starting Log Aggregator API with Uvicorn...")
    uvicorn.run(
        "main:app",
        host=app_config.server_host,
        port=app_config.server_port,
        reload=app_config.debug_mode,
        log_level=app_config.log_level.lower()
    ) 