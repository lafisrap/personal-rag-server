from datetime import datetime, timezone, timedelta
from typing import Optional, List
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import DuplicateKeyError
from bson import ObjectId
import secrets

from app.core.config import settings
from app.core.security import security_manager, create_user_token_data
from app.db.mongodb import mongodb
from app.models.user import (
    User, UserCreate, UserUpdate, UserInDB, 
    APIKey, APIKeyCreate, APIKeyResponse,
    Token, LoginRequest, UserRole, Permission
)


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        self.security_manager = security_manager
    
    @property
    def users_collection(self) -> AsyncIOMotorCollection:
        """Get users collection from MongoDB"""
        return mongodb.db.users
    
    @property
    def api_keys_collection(self) -> AsyncIOMotorCollection:
        """Get API keys collection from MongoDB"""
        return mongodb.db.api_keys
    
    # User Management
    async def create_user(self, user_create: UserCreate) -> UserInDB:
        """Create a new user"""
        # Validate password strength
        is_valid, message = self.security_manager.validate_password_strength(user_create.password)
        if not is_valid:
            raise ValueError(f"Password validation failed: {message}")
        
        # Check if username or email already exists
        existing_user = await self.users_collection.find_one({
            "$or": [
                {"username": user_create.username},
                {"email": user_create.email}
            ]
        })
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Hash password
        hashed_password = self.security_manager.get_password_hash(user_create.password)
        
        # Create user document
        user_dict = user_create.model_dump(exclude={"password"})
        user_dict.update({
            "_id": str(ObjectId()),
            "hashed_password": hashed_password,
            "created_at": datetime.now(timezone.utc),
            "last_login": None,
            "login_count": 0
        })
        
        try:
            await self.users_collection.insert_one(user_dict)
            return UserInDB(**user_dict)
        except DuplicateKeyError:
            raise ValueError("Username or email already exists")
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        """Get user by ID"""
        user_doc = await self.users_collection.find_one({"_id": user_id})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    async def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        """Get user by username"""
        user_doc = await self.users_collection.find_one({"username": username})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        """Get user by email"""
        user_doc = await self.users_collection.find_one({"email": email})
        if user_doc:
            return UserInDB(**user_doc)
        return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserInDB]:
        """Update user"""
        update_dict = user_update.model_dump(exclude_unset=True)
        
        # Handle password update
        if "password" in update_dict:
            # Validate password strength
            is_valid, message = self.security_manager.validate_password_strength(update_dict["password"])
            if not is_valid:
                raise ValueError(f"Password validation failed: {message}")
            
            # Hash new password
            update_dict["hashed_password"] = self.security_manager.get_password_hash(update_dict["password"])
            update_dict["password_changed_at"] = datetime.now(timezone.utc)
            del update_dict["password"]
        
        if not update_dict:
            return await self.get_user_by_id(user_id)
        
        result = await self.users_collection.update_one(
            {"_id": user_id},
            {"$set": update_dict}
        )
        
        if result.modified_count:
            return await self.get_user_by_id(user_id)
        return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        # Also delete associated API keys
        await self.api_keys_collection.delete_many({"user_id": user_id})
        
        result = await self.users_collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    
    async def list_users(
        self, 
        skip: int = 0, 
        limit: int = 100,
        role_filter: Optional[UserRole] = None,
        active_only: bool = True
    ) -> List[User]:
        """List users with pagination and filtering"""
        query = {}
        
        if role_filter:
            query["role"] = role_filter
        
        if active_only:
            query["is_active"] = True
        
        cursor = self.users_collection.find(query).skip(skip).limit(limit)
        users = []
        
        async for user_doc in cursor:
            # Convert to User model (excluding sensitive fields)
            user_dict = {k: v for k, v in user_doc.items() if k not in ["hashed_password"]}
            user_dict["id"] = user_dict.pop("_id")
            users.append(User(**user_dict))
        
        return users
    
    async def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp and increment login count"""
        await self.users_collection.update_one(
            {"_id": user_id},
            {
                "$set": {"last_login": datetime.now(timezone.utc)},
                "$inc": {"login_count": 1}
            }
        )
    
    # Authentication
    async def authenticate_user(self, username: str, password: str) -> Optional[UserInDB]:
        """Authenticate user with username/password"""
        user = await self.get_user_by_username(username)
        
        if not user:
            return None
        
        if not user.is_active:
            return None
        
        if not self.security_manager.verify_password(password, user.hashed_password):
            return None
        
        # Update last login
        await self.update_last_login(user.id)
        
        return user
    
    async def create_access_token(self, user: UserInDB) -> Token:
        """Create access token for user"""
        token_data = create_user_token_data(user)
        
        access_token = self.security_manager.create_access_token(token_data)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    # API Key Management
    async def create_api_key(self, user_id: str, api_key_create: APIKeyCreate) -> APIKeyResponse:
        """Create a new API key for a user"""
        # Generate API key
        api_key = self.security_manager.generate_api_key()
        key_hash = self.security_manager.hash_api_key(api_key)
        
        # Create API key document
        api_key_dict = {
            "_id": str(ObjectId()),
            "name": api_key_create.name,
            "key_hash": key_hash,
            "user_id": user_id,
            "permissions": api_key_create.permissions,
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "last_used": None,
            "expires_at": api_key_create.expires_at
        }
        
        await self.api_keys_collection.insert_one(api_key_dict)
        
        return APIKeyResponse(
            id=api_key_dict["_id"],
            name=api_key_dict["name"],
            key=api_key,  # Only returned once
            permissions=api_key_dict["permissions"],
            expires_at=api_key_dict["expires_at"],
            created_at=api_key_dict["created_at"]
        )
    
    async def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify an API key and return associated data"""
        key_hash = self.security_manager.hash_api_key(api_key)
        
        api_key_doc = await self.api_keys_collection.find_one({
            "key_hash": key_hash,
            "is_active": True
        })
        
        if not api_key_doc:
            return None
        
        # Check if key is expired
        if api_key_doc.get("expires_at") and api_key_doc["expires_at"] < datetime.now(timezone.utc):
            return None
        
        # Update last used timestamp
        await self.api_keys_collection.update_one(
            {"_id": api_key_doc["_id"]},
            {"$set": {"last_used": datetime.now(timezone.utc)}}
        )
        
        return APIKey(**api_key_doc)
    
    async def list_user_api_keys(self, user_id: str) -> List[APIKey]:
        """List API keys for a user"""
        cursor = self.api_keys_collection.find({"user_id": user_id})
        api_keys = []
        
        async for key_doc in cursor:
            api_keys.append(APIKey(**key_doc))
        
        return api_keys
    
    async def revoke_api_key(self, api_key_id: str, user_id: str) -> bool:
        """Revoke an API key"""
        result = await self.api_keys_collection.update_one(
            {"_id": api_key_id, "user_id": user_id},
            {"$set": {"is_active": False}}
        )
        
        return result.modified_count > 0
    
    async def delete_api_key(self, api_key_id: str, user_id: str) -> bool:
        """Delete an API key"""
        result = await self.api_keys_collection.delete_one({
            "_id": api_key_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0
    
    # Admin Functions
    async def create_first_superuser(self) -> Optional[UserInDB]:
        """Create the first superuser if no users exist"""
        # Check if any users exist
        user_count = await self.users_collection.count_documents({})
        
        if user_count > 0:
            return None
        
        # Create superuser
        superuser_data = UserCreate(
            username=settings.FIRST_SUPERUSER_USERNAME,
            email=settings.FIRST_SUPERUSER_EMAIL,
            password=settings.FIRST_SUPERUSER_PASSWORD,
            full_name="System Administrator",
            role=UserRole.ADMIN
        )
        
        return await self.create_user(superuser_data)
    
    async def get_user_count(self) -> int:
        """Get total number of users"""
        return await self.users_collection.count_documents({})
    
    async def get_active_user_count(self) -> int:
        """Get number of active users"""
        return await self.users_collection.count_documents({"is_active": True})


# Global user service instance
user_service = UserService() 