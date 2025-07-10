"""
Rate Limiting for Dashboard API

This module provides configurable rate limiting for API endpoints using slowapi.
Rate limiting can be enabled/disabled and configured via environment variables.
"""

import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configuration from environment variables
RATE_LIMITING_ENABLED = os.getenv("ENABLE_RATE_LIMITING", "false").lower() in ("true", "1", "yes", "on")

# Generous default rate limits to avoid disrupting current usage
DEFAULT_RATE_LIMIT = os.getenv("RATE_LIMIT_PER_MINUTE", "1000")  # 1000 requests per minute
API_RATE_LIMIT = os.getenv("API_RATE_LIMIT_PER_MINUTE", "500")    # 500 requests per minute for API endpoints
AUTH_RATE_LIMIT = os.getenv("AUTH_RATE_LIMIT_PER_MINUTE", "10")   # 10 login attempts per minute
LOGS_RATE_LIMIT = os.getenv("LOGS_RATE_LIMIT_PER_MINUTE", "100")  # 100 log requests per minute

# Redis configuration for distributed rate limiting (optional)
REDIS_URL = os.getenv("REDIS_URL", None)

# Rate limiter storage
if REDIS_URL:
    # Use Redis for distributed environments
    import redis
    from slowapi.middleware import SlowAPIMiddleware
    redis_client = redis.from_url(REDIS_URL)
    storage_uri = REDIS_URL
else:
    # Use in-memory storage for single instance
    storage_uri = "memory://"

def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on client identifier.
    Uses IP address by default, but can be enhanced with user-based limiting.
    """
    # Basic IP-based limiting
    client_ip = get_remote_address(request)
    
    # If authentication is enabled and user is authenticated, use user-based limiting
    if hasattr(request.state, 'user') and request.state.user:
        user_id = getattr(request.state.user, 'username', client_ip)
        return f"user:{user_id}"
    
    return f"ip:{client_ip}"

# Create limiter instance
limiter = Limiter(
    key_func=get_rate_limit_key,
    storage_uri=storage_uri,
    enabled=RATE_LIMITING_ENABLED
)

def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Custom rate limit exceeded handler with informative error messages.
    """
    response = JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after": exc.retry_after,
            "limit": exc.detail,
            "rate_limiting_enabled": RATE_LIMITING_ENABLED,
            "endpoint": request.url.path
        },
        headers={"Retry-After": str(exc.retry_after)}
    )
    
    logger.warning(f"Rate limit exceeded for {get_rate_limit_key(request)} on {request.url.path}")
    return response

# Rate limiting decorators for different endpoint types
def general_rate_limit():
    """General rate limit for most endpoints"""
    return limiter.limit(f"{DEFAULT_RATE_LIMIT}/minute")

def api_rate_limit():
    """Rate limit for API endpoints"""
    return limiter.limit(f"{API_RATE_LIMIT}/minute")

def auth_rate_limit():
    """Strict rate limit for authentication endpoints"""
    return limiter.limit(f"{AUTH_RATE_LIMIT}/minute")

def logs_rate_limit():
    """Rate limit for log endpoints (moderate usage)"""
    return limiter.limit(f"{LOGS_RATE_LIMIT}/minute")

def cognitive_rate_limit():
    """Rate limit for AI/cognitive endpoints (resource intensive)"""
    cognitive_limit = os.getenv("COGNITIVE_RATE_LIMIT_PER_MINUTE", "50")
    return limiter.limit(f"{cognitive_limit}/minute")

def no_rate_limit():
    """No rate limiting - for health checks and public endpoints"""
    return lambda func: func

# Conditional rate limiting based on configuration
def conditional_rate_limit(limit_type: str = "general"):
    """
    Apply rate limiting conditionally based on configuration.
    Returns a no-op decorator if rate limiting is disabled.
    """
    if not RATE_LIMITING_ENABLED:
        return no_rate_limit()
    
    limit_map = {
        "general": general_rate_limit(),
        "api": api_rate_limit(),
        "auth": auth_rate_limit(),
        "logs": logs_rate_limit(),
        "cognitive": cognitive_rate_limit()
    }
    
    return limit_map.get(limit_type, general_rate_limit())

def get_rate_limit_status() -> dict:
    """Get current rate limiting configuration and status"""
    return {
        "rate_limiting_enabled": RATE_LIMITING_ENABLED,
        "storage_type": "redis" if REDIS_URL else "memory",
        "limits": {
            "general": f"{DEFAULT_RATE_LIMIT}/minute",
            "api": f"{API_RATE_LIMIT}/minute", 
            "auth": f"{AUTH_RATE_LIMIT}/minute",
            "logs": f"{LOGS_RATE_LIMIT}/minute",
            "cognitive": f"{os.getenv('COGNITIVE_RATE_LIMIT_PER_MINUTE', '50')}/minute"
        },
        "key_strategy": "ip_and_user_based",
        "redis_configured": bool(REDIS_URL)
    }

# Statistics tracking (optional)
class RateLimitStats:
    """Track rate limiting statistics"""
    
    def __init__(self):
        self.total_requests = 0
        self.limited_requests = 0
        self.endpoint_stats = {}
    
    def record_request(self, endpoint: str, limited: bool = False):
        """Record a request for statistics"""
        self.total_requests += 1
        if limited:
            self.limited_requests += 1
        
        if endpoint not in self.endpoint_stats:
            self.endpoint_stats[endpoint] = {"total": 0, "limited": 0}
        
        self.endpoint_stats[endpoint]["total"] += 1
        if limited:
            self.endpoint_stats[endpoint]["limited"] += 1
    
    def get_stats(self) -> dict:
        """Get rate limiting statistics"""
        return {
            "total_requests": self.total_requests,
            "limited_requests": self.limited_requests,
            "limit_rate": (self.limited_requests / max(self.total_requests, 1)) * 100,
            "endpoint_stats": self.endpoint_stats
        }

# Global statistics instance
rate_limit_stats = RateLimitStats() 