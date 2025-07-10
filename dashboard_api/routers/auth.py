from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional
import hashlib
import time

# Import our JWT middleware and rate limiting
from dashboard_api.security.jwt_middleware import jwt_manager, get_current_user, get_auth_status
from dashboard_api.security.rate_limiting import conditional_rate_limit

# Simple user database (In production, use a real database)
FAKE_USERS_DB = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "fake_hashed_password_for_testuser",
        "disabled": False,
        "permissions": ["read", "write"]
    },
    "admin": {
        "username": "admin",
        "full_name": "Admin User", 
        "email": "admin@tron-dashboard.com",
        "hashed_password": hashlib.sha256("admin123".encode()).hexdigest(),
        "disabled": False,
        "permissions": ["read", "write", "admin"]
    }
}

# --- Pydantic Models ---
class UserInDB(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str
    permissions: list = []

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user: dict

class UserInfo(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    permissions: list = []

router = APIRouter()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash. Simple implementation for demo."""
    # For demo purposes, accept the fake password or actual hash
    if hashed_password == "fake_hashed_password_for_testuser" and plain_password == "testpassword":
        return True
    
    # For admin user with actual hash
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password

@router.post("/token", response_model=Token)
@conditional_rate_limit("auth")
async def login_for_access_token(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2-compatible endpoint to get a JWT access token.
    """
    user = FAKE_USERS_DB.get(form_data.username)
    if not user or user.get("disabled", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create JWT token with user data
    user_data = {
        "username": user["username"],
        "email": user.get("email"),
        "full_name": user.get("full_name"),
        "permissions": user.get("permissions", [])
    }
    
    access_token = jwt_manager.create_token(user_data)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": jwt_manager.expiration_hours * 3600,
        "user": user_data
    }

@router.post("/register")
@conditional_rate_limit("auth")
async def register_user(request: Request, user_data: UserInDB):
    """
    User registration endpoint with proper password hashing.
    """
    username = user_data.username
    if username in FAKE_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Hash the password before storing
    hashed_password = hashlib.sha256(user_data.hashed_password.encode()).hexdigest()
    
    FAKE_USERS_DB[username] = {
        "username": username,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "hashed_password": hashed_password,
        "disabled": False,
        "permissions": user_data.permissions or ["read"]
    }
    
    return {"message": f"User {username} registered successfully"}

@router.get("/me", response_model=UserInfo)
async def get_current_user_info(request: Request):
    """
    Get current authenticated user information.
    Works regardless of whether auth is enabled.
    """
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return UserInfo(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        permissions=user.permissions
    )

@router.get("/status")
async def get_authentication_status():
    """
    Get authentication system status and configuration.
    Useful for debugging and frontend integration.
    """
    status = get_auth_status()
    status.update({
        "available_users": list(FAKE_USERS_DB.keys()),
        "default_permissions": ["read"],
        "demo_credentials": {
            "testuser": "testpassword",
            "admin": "admin123"
        } if not status["auth_enabled"] else None
    })
    
    return status

@router.post("/logout")
async def logout(request: Request):
    """
    Logout endpoint. Since JWT is stateless, this is mainly for frontend state management.
    In a production system, you might maintain a token blacklist.
    """
    user = get_current_user(request)
    username = user.username if user else "anonymous"
    
    return {
        "message": f"User {username} logged out successfully",
        "timestamp": int(time.time())
    } 