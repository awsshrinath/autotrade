"""
Authentication Utility
Simple authentication for dashboard access
"""

import os
import hashlib
from typing import Optional


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate user credentials
    
    Args:
        username: Username to authenticate
        password: Password to authenticate
        
    Returns:
        bool: True if authentication successful, False otherwise
    """
    try:
        # Get credentials from environment variables
        valid_username = os.getenv("DASHBOARD_USERNAME", "admin")
        valid_password = os.getenv("DASHBOARD_PASSWORD", "tron2024")
        
        # Simple comparison (in production, use proper hashing)
        if username == valid_username and password == valid_password:
            return True
        
        # Check for additional users (could be expanded)
        additional_users = {
            "trader": "trader123",
            "viewer": "viewer123"
        }
        
        if username in additional_users and password == additional_users[username]:
            return True
            
        return False
        
    except Exception as e:
        print(f"Authentication error: {e}")
        return False


def hash_password(password: str) -> str:
    """
    Hash password using SHA256
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain text password
        hashed_password: Hashed password to verify against
        
    Returns:
        bool: True if password matches hash
    """
    return hash_password(password) == hashed_password


def get_user_permissions(username: str) -> dict:
    """
    Get user permissions based on username
    
    Args:
        username: Username to get permissions for
        
    Returns:
        dict: User permissions
    """
    permissions = {
        "admin": {
            "can_view": True,
            "can_trade": True,
            "can_modify": True,
            "can_close_positions": True,
            "can_view_system": True
        },
        "trader": {
            "can_view": True,
            "can_trade": True,
            "can_modify": True,
            "can_close_positions": True,
            "can_view_system": False
        },
        "viewer": {
            "can_view": True,
            "can_trade": False,
            "can_modify": False,
            "can_close_positions": False,
            "can_view_system": False
        }
    }
    
    return permissions.get(username, permissions["viewer"]) 