"""
Security utilities, including API key authentication for FastAPI endpoints.
"""

from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
import structlog

from .config import get_config

logger = structlog.get_logger(__name__)
config = get_config()

API_KEY_NAME = "X-API-Key"
api_key_header_auth = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header_auth)):
    """
    Dependency to validate the API key provided in the X-API-Key header.
    Raises HTTPException if the API key is invalid or not provided.
    """
    if not config.api_keys: # Check if any API keys are configured
        logger.warning("API key authentication is enabled, but no API_KEYS are configured in the environment. Allowing request.")
        # If no keys are configured, you might choose to allow all requests (development) 
        # or deny all (production default). For now, allowing for flexibility.
        # In a production scenario, this should strictly deny if no keys are set and auth is on.
        return "development_fallback_key" # Or raise HTTPException for stricter control

    configured_keys = [key.strip() for key in config.api_keys.split(",")]
    if api_key_header in configured_keys:
        logger.debug("API key validated successfully.")
        return api_key_header
    else:
        logger.warning("Invalid API key received.", received_key=api_key_header)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )

# Placeholder for a more complex user model if needed in the future
class AuthenticatedUser:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # In a real app, you might look up user details based on the API key
        self.username = f"user_for_{api_key[:8]}" # Example username
        self.roles: list[str] = ["viewer"] # Example role

async def get_current_active_user(api_key: str = Security(get_api_key)) -> AuthenticatedUser:
    """
    Dependency to get the current authenticated user based on the validated API key.
    This is a placeholder for more complex user/permission systems.
    """
    # For now, just returns a simple user object based on the API key itself.
    # In a real system, you would look up user details from a database or identity provider.
    return AuthenticatedUser(api_key=api_key)

# Example of how to protect an endpoint (to be used in routers):
# from .security import get_current_active_user
# from ..models.log_models import AuthenticatedUser # If you define it there
# @router.get("/protected-route", dependencies=[Depends(get_current_active_user)])
# async def protected_route(current_user: AuthenticatedUser = Depends(get_current_active_user)):
#     return {"message": f"Hello {current_user.username}, you have access!"} 