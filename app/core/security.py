import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import re

from app.core.config import settings
from app.models.user import UserInDB, TokenData, Permission, UserRole, DEFAULT_ROLE_PERMISSIONS


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Security
security = HTTPBearer()

# API Key Security
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)


class SecurityManager:
    """Central security management class"""
    
    def __init__(self):
        self.pwd_context = pwd_context
        self.algorithm = settings.ALGORITHM
        self.secret_key = settings.SECRET_KEY
    
    # Password Management
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def validate_password_strength(self, password: str) -> tuple[bool, str]:
        """Validate password strength according to policy"""
        errors = []
        
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters long")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if settings.PASSWORD_REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        is_valid = len(errors) == 0
        message = "; ".join(errors) if errors else "Password is valid"
        
        return is_valid, message
    
    # JWT Token Management
    def create_access_token(
        self,
        data: dict,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            permissions: List[str] = payload.get("permissions", [])
            
            if user_id is None:
                return None
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                permissions=[Permission(p) for p in permissions if p in [perm.value for perm in Permission]]
            )
            return token_data
        except JWTError:
            return None
    
    # API Key Management
    def generate_api_key(self) -> str:
        """Generate a new API key"""
        key = secrets.token_urlsafe(settings.API_KEY_LENGTH)
        return f"{settings.API_KEY_PREFIX}{key}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify an API key against its hash"""
        return hashlib.sha256(api_key.encode()).hexdigest() == hashed_key
    
    # Permission Management
    def get_role_permissions(self, role: UserRole) -> List[Permission]:
        """Get permissions for a given role"""
        return DEFAULT_ROLE_PERMISSIONS.get(role, [])
    
    def user_has_permission(self, user_permissions: List[Permission], required_permission: Permission) -> bool:
        """Check if user has a specific permission"""
        return required_permission in user_permissions
    
    def user_has_any_permission(self, user_permissions: List[Permission], required_permissions: List[Permission]) -> bool:
        """Check if user has any of the required permissions"""
        return any(perm in user_permissions for perm in required_permissions)
    
    def user_has_all_permissions(self, user_permissions: List[Permission], required_permissions: List[Permission]) -> bool:
        """Check if user has all required permissions"""
        return all(perm in user_permissions for perm in required_permissions)


# Global security manager instance
security_manager = SecurityManager()


# Authentication Dependencies
async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """Get current user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token_data = security_manager.verify_token(credentials.credentials)
        if token_data is None:
            raise credentials_exception
        return token_data
    except Exception:
        raise credentials_exception


async def get_current_user_from_api_key(
    request: Request,
    api_key: Optional[str] = Depends(api_key_header)
) -> Optional[TokenData]:
    """Get current user from API key"""
    if not api_key:
        return None
    
    try:
        # Import here to avoid circular import
        from app.services.user_service import user_service
        
        # Verify API key
        api_key_obj = await user_service.verify_api_key(api_key)
        if not api_key_obj:
            return None
        
        # Get user associated with API key
        user = await user_service.get_user_by_id(api_key_obj.user_id)
        if not user or not user.is_active:
            return None
        
        # Create token data from API key permissions
        return TokenData(
            user_id=user.id,
            username=user.username,
            permissions=api_key_obj.permissions
        )
    
    except Exception:
        return None


async def get_current_user(
    token_user: Optional[TokenData] = Depends(get_current_user_from_token),
    api_key_user: Optional[TokenData] = Depends(get_current_user_from_api_key)
) -> TokenData:
    """Get current user from either JWT token or API key"""
    # Try JWT token first
    try:
        if token_user:
            return token_user
    except HTTPException:
        pass  # JWT failed, try API key
    
    # Try API key
    if api_key_user:
        return api_key_user
    
    # Neither worked
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide either Bearer token or X-API-Key header."
    )


# Authorization Dependencies
def require_permission(permission: Permission):
    """Dependency factory for requiring specific permissions"""
    def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not security_manager.user_has_permission(current_user.permissions, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission.value}"
            )
        return current_user
    return permission_checker


def require_any_permission(permissions: List[Permission]):
    """Dependency factory for requiring any of the specified permissions"""
    def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not security_manager.user_has_any_permission(current_user.permissions, permissions):
            permission_names = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these permissions required: {', '.join(permission_names)}"
            )
        return current_user
    return permission_checker


def require_all_permissions(permissions: List[Permission]):
    """Dependency factory for requiring all specified permissions"""
    def permission_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not security_manager.user_has_all_permissions(current_user.permissions, permissions):
            permission_names = [p.value for p in permissions]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"All of these permissions required: {', '.join(permission_names)}"
            )
        return current_user
    return permission_checker


def require_role(role: UserRole):
    """Dependency factory for requiring a specific role"""
    def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        # This assumes we store role information in the token
        # You might need to modify TokenData to include role information
        role_permissions = security_manager.get_role_permissions(role)
        if not security_manager.user_has_all_permissions(current_user.permissions, role_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role required: {role.value}"
            )
        return current_user
    return role_checker


# Rate Limiting Helpers
def rate_limit_by_user():
    """Rate limiting based on user ID"""
    def get_user_id(request: Request):
        # Extract user ID from token if available
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            token_data = security_manager.verify_token(token)
            if token_data:
                return token_data.user_id
        return get_remote_address(request)
    
    return get_user_id


# Security Headers Middleware
def get_security_headers() -> dict:
    """Get security headers for responses"""
    headers = {}
    
    if settings.ENABLE_SECURITY_HEADERS:
        headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
        })
    
    return headers


# Utility Functions
def create_user_token_data(user: UserInDB) -> dict:
    """Create token data for a user"""
    permissions = security_manager.get_role_permissions(user.role)
    return {
        "sub": user.id,
        "username": user.username,
        "permissions": [p.value for p in permissions],
        "role": user.role.value
    }


def is_password_expired(user: UserInDB, max_age_days: int = 90) -> bool:
    """Check if user's password is expired"""
    if not hasattr(user, 'password_changed_at') or user.password_changed_at is None:
        return False
    
    expiry_date = user.password_changed_at + timedelta(days=max_age_days)
    return datetime.now(timezone.utc) > expiry_date


def generate_secure_random_string(length: int = 32) -> str:
    """Generate a cryptographically secure random string"""
    return secrets.token_urlsafe(length)


# Exception Handlers
def create_security_exception_handlers():
    """Create security-related exception handlers"""
    return {
        RateLimitExceeded: _rate_limit_exceeded_handler,
    }
