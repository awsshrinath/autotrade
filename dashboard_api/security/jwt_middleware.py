"""
JWT Authentication Middleware for Dashboard API

This middleware provides optional JWT authentication that can be enabled/disabled
via configuration without breaking existing functionality.
"""

import os
import jwt
import time
from typing import Optional, Dict, Any, Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "tron-dashboard-secret-key-change-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Toggle for authentication - can be controlled via environment variable
AUTH_ENABLED = os.getenv("ENABLE_JWT_AUTH", "false").lower() in ("true", "1", "yes", "on")

# Optional endpoints that can bypass authentication even when enabled
BYPASS_ENDPOINTS = {
    "/health",
    "/docs",
    "/openapi.json",
    "/",
    "/api/auth/token",
    "/api/auth/register"
}

# User model for JWT payload
class TokenUser(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    permissions: list = []
    exp: int = 0

class JWTManager:
    """Manages JWT token creation and validation"""
    
    def __init__(self):
        self.secret_key = JWT_SECRET_KEY
        self.algorithm = JWT_ALGORITHM
        self.expiration_hours = JWT_EXPIRATION_HOURS
        
    def create_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT token for a user"""
        payload = {
            **user_data,
            "exp": int(time.time()) + (self.expiration_hours * 3600),
            "iat": int(time.time()),
            "iss": "tron-dashboard-api"
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        return token
    
    def verify_token(self, token: str) -> Optional[TokenUser]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={"verify_exp": True, "verify_iat": True}
            )
            
            return TokenUser(**payload)
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying JWT token: {e}")
            return None

# Global JWT manager instance
jwt_manager = JWTManager()

# FastAPI HTTP Bearer security scheme (optional)
bearer_scheme = HTTPBearer(auto_error=False)

class OptionalJWTMiddleware:
    """
    Middleware that provides optional JWT authentication.
    Can be toggled on/off without breaking existing functionality.
    """
    
    def __init__(self, app):
        self.app = app
        
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
            
        request = Request(scope, receive)
        
        # Check if authentication is enabled
        if not AUTH_ENABLED:
            # Authentication disabled - pass through without checking
            await self.app(scope, receive, send)
            return
            
        # Check if endpoint should bypass authentication
        path = request.url.path
        if self._should_bypass_auth(path):
            await self.app(scope, receive, send)
            return
            
        # Attempt to authenticate the request
        user = await self._authenticate_request(request)
        
        if user is None:
            # Authentication failed - return 401
            response = JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Authentication required",
                    "error": "missing_or_invalid_token",
                    "auth_enabled": True
                },
                headers={"WWW-Authenticate": "Bearer"}
            )
            await response(scope, receive, send)
            return
            
        # Add user to request state for use in endpoints
        scope["state"] = getattr(scope.get("state", {}), "__dict__", {})
        scope["state"]["user"] = user
        
        await self.app(scope, receive, send)
        
    def _should_bypass_auth(self, path: str) -> bool:
        """Check if a path should bypass authentication"""
        # Exact matches
        if path in BYPASS_ENDPOINTS:
            return True
            
        # Pattern matches
        bypass_patterns = [
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/static/",
            "/favicon.ico"
        ]
        
        for pattern in bypass_patterns:
            if path.startswith(pattern):
                return True
                
        return False
        
    async def _authenticate_request(self, request: Request) -> Optional[TokenUser]:
        """Authenticate a request using JWT token"""
        try:
            # Try to get token from Authorization header
            authorization = request.headers.get("Authorization")
            if not authorization:
                return None
                
            # Parse Bearer token
            if not authorization.startswith("Bearer "):
                return None
                
            token = authorization.split(" ")[1]
            if not token:
                return None
                
            # Verify the token
            user = jwt_manager.verify_token(token)
            return user
            
        except Exception as e:
            logger.error(f"Error during authentication: {e}")
            return None

def get_current_user(request: Request) -> Optional[TokenUser]:
    """
    Dependency to get current authenticated user.
    Returns None if authentication is disabled or no user found.
    """
    if not AUTH_ENABLED:
        # Return a default user when auth is disabled
        return TokenUser(
            username="anonymous",
            email="anonymous@tron-dashboard.local",
            full_name="Anonymous User",
            permissions=["read"],
            exp=int(time.time()) + 86400
        )
        
    # Get user from request state (set by middleware)
    state = getattr(request, "state", None)
    if state:
        return getattr(state, "user", None)
    return None

def require_auth(request: Request) -> TokenUser:
    """
    Dependency that requires authentication.
    Raises HTTPException if no valid user found.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user

def get_auth_status() -> Dict[str, Any]:
    """Get current authentication status and configuration"""
    return {
        "auth_enabled": AUTH_ENABLED,
        "algorithm": JWT_ALGORITHM,
        "expiration_hours": JWT_EXPIRATION_HOURS,
        "bypass_endpoints": list(BYPASS_ENDPOINTS),
        "secret_configured": bool(JWT_SECRET_KEY and JWT_SECRET_KEY != "tron-dashboard-secret-key-change-in-production")
    } 