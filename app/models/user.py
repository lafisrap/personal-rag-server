from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class UserRole(str, Enum):
    """User roles for RBAC"""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"
    SERVICE = "service"


class Permission(str, Enum):
    """System permissions"""
    # RAG Operations
    READ_DOCUMENTS = "read:documents"
    WRITE_DOCUMENTS = "write:documents"
    DELETE_DOCUMENTS = "delete:documents"
    
    # Conversations
    READ_CONVERSATIONS = "read:conversations"
    WRITE_CONVERSATIONS = "write:conversations"
    DELETE_CONVERSATIONS = "delete:conversations"
    
    # Categories and Tags
    READ_CATEGORIES = "read:categories"
    WRITE_CATEGORIES = "write:categories"
    DELETE_CATEGORIES = "delete:categories"
    
    # User Management (Admin only)
    READ_USERS = "read:users"
    WRITE_USERS = "write:users"
    DELETE_USERS = "delete:users"
    
    # System Administration
    ADMIN_SYSTEM = "admin:system"


class RolePermissions(BaseModel):
    """Maps roles to their permissions"""
    role: UserRole
    permissions: List[Permission]


# Default role-permission mappings
DEFAULT_ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.READ_DOCUMENTS, Permission.WRITE_DOCUMENTS, Permission.DELETE_DOCUMENTS,
        Permission.READ_CONVERSATIONS, Permission.WRITE_CONVERSATIONS, Permission.DELETE_CONVERSATIONS,
        Permission.READ_CATEGORIES, Permission.WRITE_CATEGORIES, Permission.DELETE_CATEGORIES,
        Permission.READ_USERS, Permission.WRITE_USERS, Permission.DELETE_USERS,
        Permission.ADMIN_SYSTEM
    ],
    UserRole.USER: [
        Permission.READ_DOCUMENTS, Permission.WRITE_DOCUMENTS,
        Permission.READ_CONVERSATIONS, Permission.WRITE_CONVERSATIONS,
        Permission.READ_CATEGORIES, Permission.WRITE_CATEGORIES
    ],
    UserRole.GUEST: [
        Permission.READ_DOCUMENTS,
        Permission.READ_CONVERSATIONS,
        Permission.READ_CATEGORIES
    ],
    UserRole.SERVICE: [
        Permission.READ_DOCUMENTS, Permission.WRITE_DOCUMENTS,
        Permission.READ_CONVERSATIONS, Permission.WRITE_CONVERSATIONS
    ]
}


class UserBase(BaseModel):
    """Base user model"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    password: Optional[str] = Field(None, min_length=8)


class UserInDB(UserBase):
    """User model as stored in database"""
    id: str = Field(alias="_id")
    hashed_password: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_login: Optional[datetime] = None
    login_count: int = 0
    
    class Config:
        populate_by_name = True


class User(UserBase):
    """User model for API responses"""
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    login_count: int = 0


class APIKey(BaseModel):
    """API Key model for service-to-service authentication"""
    id: str = Field(alias="_id")
    name: str
    key_hash: str  # Hashed API key
    user_id: str
    permissions: List[Permission]
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_used: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    class Config:
        populate_by_name = True


class APIKeyCreate(BaseModel):
    """API Key creation model"""
    name: str = Field(..., min_length=3, max_length=100)
    permissions: List[Permission] = []
    expires_at: Optional[datetime] = None


class APIKeyResponse(BaseModel):
    """API Key response model"""
    id: str
    name: str
    key: str  # Only returned once on creation
    permissions: List[Permission]
    expires_at: Optional[datetime] = None
    created_at: datetime


class Token(BaseModel):
    """JWT Token response model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    """JWT Token payload data"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    permissions: List[Permission] = []


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class PasswordReset(BaseModel):
    """Password reset model"""
    token: str
    new_password: str = Field(..., min_length=8)


class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr 