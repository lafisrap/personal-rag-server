from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Personal RAG Server"
    
    # Security Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Password Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = False
    
    # API Key Settings
    API_KEY_PREFIX: str = "rag_"
    API_KEY_LENGTH: int = 32
    API_KEY_EXPIRE_DAYS: int = int(os.getenv("API_KEY_EXPIRE_DAYS", "90"))
    
    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_PERIOD: int = int(os.getenv("RATE_LIMIT_PERIOD", "60"))  # seconds
    RATE_LIMIT_BURST: int = int(os.getenv("RATE_LIMIT_BURST", "10"))
    
    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        origin.strip() 
        for origin in os.getenv("BACKEND_CORS_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
        if origin.strip()
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Security Headers
    ENABLE_SECURITY_HEADERS: bool = True
    
    # MongoDB Settings
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "rag_server")
    
    # Vector DB Settings (Pinecone)
    VECTOR_DB_TYPE: str = os.getenv("VECTOR_DB_TYPE", "pinecone")
    PINECONE_API_KEY: Optional[str] = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT: Optional[str] = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME: Optional[str] = os.getenv("PINECONE_INDEX_NAME", "rag-server")
    PINECONE_HOST: Optional[str] = os.getenv("PINECONE_HOST", "")
    
    # LLM Settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    DEFAULT_LLM_MODEL: str = os.getenv("DEFAULT_LLM_MODEL", "gpt-4o")
    
    # DeepSeek Settings
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_URL: str = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com")
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_PHILOSOPHY_MODEL: str = os.getenv("DEEPSEEK_PHILOSOPHY_MODEL", "deepseek-v3-0324")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openai")  # openai or deepseek
    
    # Embeddings Settings
    EMBEDDINGS_MODEL: str = os.getenv("EMBEDDINGS_MODEL", "text-embedding-3-large")
    EMBEDDINGS_DIMENSION: int = 3072  # Dimension for text-embedding-3-large
    
    # App Settings
    MAX_CATEGORIES: int = 20
    MAX_TAGS_PER_CATEGORY: int = 100
    
    # Admin User Settings (for initial setup)
    FIRST_SUPERUSER_USERNAME: str = os.getenv("FIRST_SUPERUSER_USERNAME", "admin")
    FIRST_SUPERUSER_EMAIL: str = os.getenv("FIRST_SUPERUSER_EMAIL", "admin@example.com")
    FIRST_SUPERUSER_PASSWORD: str = os.getenv("FIRST_SUPERUSER_PASSWORD", "changeme123")
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT.lower() == "development"
    

settings = Settings()
