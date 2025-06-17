from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Optional

# Placeholder for user database and password hashing
FAKE_USERS_DB = {
    "testuser": {
        "username": "testuser",
        "full_name": "Test User",
        "email": "test@example.com",
        "hashed_password": "fake_hashed_password_for_testuser", # In a real app, use something like passlib
        "disabled": False,
    }
}

# --- Pydantic Models ---
class UserInDB(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

router = APIRouter()

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2-compatible endpoint to get an access token.
    In a real app, you'd verify the password here.
    """
    user = FAKE_USERS_DB.get(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # In a real app, you would:
    # 1. Verify form_data.password against user['hashed_password']
    # 2. Create a real JWT token
    
    access_token = f"fake_jwt_token_for_{user['username']}" # Placeholder token
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register")
async def register_user(user_data: UserInDB):
    """
    Placeholder for a user registration endpoint.
    """
    username = user_data.username
    if username in FAKE_USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # In a real app, you would hash the password before storing
    FAKE_USERS_DB[username] = user_data.dict()
    return {"message": f"User {username} registered successfully"} 