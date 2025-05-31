from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.security import (
    limiter, require_permission, require_role, get_current_user,
    rate_limit_by_user, security_manager
)
from app.models.user import (
    User, UserCreate, UserUpdate, Token, LoginRequest,
    APIKeyCreate, APIKeyResponse, APIKey, Permission, UserRole, TokenData
)
from app.services.user_service import user_service

router = APIRouter()


# Authentication Endpoints
@router.post("/login", response_model=Token, tags=["authentication"])
@limiter.limit(f"{settings.RATE_LIMIT_REQUESTS}/minute")
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Token:
    """
    User login with username and password
    """
    user = await user_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return await user_service.create_access_token(user)


@router.post("/register", response_model=User, tags=["authentication"])
@limiter.limit("5/minute")  # Stricter rate limit for registration
async def register(
    request: Request,
    user_create: UserCreate
) -> User:
    """
    Register a new user
    """
    try:
        user_in_db = await user_service.create_user(user_create)
        
        # Convert to User model (exclude sensitive fields)
        return User(
            id=user_in_db.id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            role=user_in_db.role,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at,
            last_login=user_in_db.last_login,
            login_count=user_in_db.login_count
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=User, tags=["users"])
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user)
) -> User:
    """
    Get current user information
    """
    user_in_db = await user_service.get_user_by_id(current_user.user_id)
    
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=user_in_db.id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at,
        last_login=user_in_db.last_login,
        login_count=user_in_db.login_count
    )


@router.put("/me", response_model=User, tags=["users"])
async def update_current_user(
    user_update: UserUpdate,
    current_user: TokenData = Depends(get_current_user)
) -> User:
    """
    Update current user information
    """
    try:
        updated_user = await user_service.update_user(current_user.user_id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return User(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login,
            login_count=updated_user.login_count
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# User Management Endpoints (Admin only)
@router.get("/users", response_model=List[User], tags=["admin"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    role_filter: Optional[UserRole] = None,
    active_only: bool = True,
    current_user: TokenData = Depends(require_permission(Permission.READ_USERS))
) -> List[User]:
    """
    List all users (Admin only)
    """
    return await user_service.list_users(
        skip=skip,
        limit=limit,
        role_filter=role_filter,
        active_only=active_only
    )


@router.post("/users", response_model=User, tags=["admin"])
async def create_user(
    user_create: UserCreate,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_USERS))
) -> User:
    """
    Create a new user (Admin only)
    """
    try:
        user_in_db = await user_service.create_user(user_create)
        
        return User(
            id=user_in_db.id,
            username=user_in_db.username,
            email=user_in_db.email,
            full_name=user_in_db.full_name,
            role=user_in_db.role,
            is_active=user_in_db.is_active,
            created_at=user_in_db.created_at,
            last_login=user_in_db.last_login,
            login_count=user_in_db.login_count
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/users/{user_id}", response_model=User, tags=["admin"])
async def get_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.READ_USERS))
) -> User:
    """
    Get user by ID (Admin only)
    """
    user_in_db = await user_service.get_user_by_id(user_id)
    
    if not user_in_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(
        id=user_in_db.id,
        username=user_in_db.username,
        email=user_in_db.email,
        full_name=user_in_db.full_name,
        role=user_in_db.role,
        is_active=user_in_db.is_active,
        created_at=user_in_db.created_at,
        last_login=user_in_db.last_login,
        login_count=user_in_db.login_count
    )


@router.put("/users/{user_id}", response_model=User, tags=["admin"])
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_USERS))
) -> User:
    """
    Update user by ID (Admin only)
    """
    try:
        updated_user = await user_service.update_user(user_id, user_update)
        
        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return User(
            id=updated_user.id,
            username=updated_user.username,
            email=updated_user.email,
            full_name=updated_user.full_name,
            role=updated_user.role,
            is_active=updated_user.is_active,
            created_at=updated_user.created_at,
            last_login=updated_user.last_login,
            login_count=updated_user.login_count
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/users/{user_id}", tags=["admin"])
async def delete_user(
    user_id: str,
    current_user: TokenData = Depends(require_permission(Permission.DELETE_USERS))
) -> dict:
    """
    Delete user by ID (Admin only)
    """
    # Prevent self-deletion
    if user_id == current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    success = await user_service.delete_user(user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {"message": "User deleted successfully"}


# API Key Management Endpoints
@router.post("/api-keys", response_model=APIKeyResponse, tags=["api-keys"])
async def create_api_key(
    api_key_create: APIKeyCreate,
    current_user: TokenData = Depends(get_current_user)
) -> APIKeyResponse:
    """
    Create a new API key for the current user
    """
    return await user_service.create_api_key(current_user.user_id, api_key_create)


@router.get("/api-keys", response_model=List[APIKey], tags=["api-keys"])
async def list_my_api_keys(
    current_user: TokenData = Depends(get_current_user)
) -> List[APIKey]:
    """
    List API keys for the current user
    """
    return await user_service.list_user_api_keys(current_user.user_id)


@router.delete("/api-keys/{api_key_id}", tags=["api-keys"])
async def delete_api_key(
    api_key_id: str,
    current_user: TokenData = Depends(get_current_user)
) -> dict:
    """
    Delete an API key
    """
    success = await user_service.delete_api_key(api_key_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key deleted successfully"}


@router.patch("/api-keys/{api_key_id}/revoke", tags=["api-keys"])
async def revoke_api_key(
    api_key_id: str,
    current_user: TokenData = Depends(get_current_user)
) -> dict:
    """
    Revoke an API key (disable without deleting)
    """
    success = await user_service.revoke_api_key(api_key_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    return {"message": "API key revoked successfully"}


# System Status Endpoints
@router.get("/system/status", tags=["system"])
async def get_system_status(
    current_user: TokenData = Depends(require_permission(Permission.ADMIN_SYSTEM))
) -> dict:
    """
    Get system status (Admin only)
    """
    total_users = await user_service.get_user_count()
    active_users = await user_service.get_active_user_count()
    
    return {
        "status": "operational",
        "total_users": total_users,
        "active_users": active_users,
        "security_enabled": True,
        "rate_limiting_enabled": True
    }


# Password Validation Endpoint
@router.post("/validate-password", tags=["utilities"])
async def validate_password(
    password: str
) -> dict:
    """
    Validate password strength without authentication
    """
    is_valid, message = security_manager.validate_password_strength(password)
    
    return {
        "is_valid": is_valid,
        "message": message,
        "requirements": {
            "min_length": settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": settings.PASSWORD_REQUIRE_NUMBERS,
            "require_special": settings.PASSWORD_REQUIRE_SPECIAL
        }
    } 