from fastapi import FastAPI, APIRouter, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
import logging
from contextlib import asynccontextmanager

from app.api.endpoints import threads, messages, assistants, auth, health, rag
from app.core.config import settings
from app.core.security import limiter, get_security_headers, create_security_exception_handlers
from app.db.mongodb import mongodb
from app.services.user_service import user_service
from app.db.vector_db import vector_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect to databases
    logger.info("Connecting to MongoDB...")
    await mongodb.connect_to_mongo()
    logger.info("Connected to MongoDB")
    
    # Initialize Pinecone
    logger.info("Initializing Pinecone vector database...")
    vector_db.init_pinecone()
    logger.info("Pinecone initialized")
    
    # Check for existing users
    logger.info("Checking for existing users...")
    user_count = await user_service.get_user_count()
    logger.info(f"Found {user_count} existing users")
    
    yield
    
    # Shutdown: close database connections
    logger.info("Closing MongoDB connection...")
    await mongodb.close_mongo_connection()
    logger.info("MongoDB connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal RAG Server with FastAPI - Secure and Production Ready",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security exception handlers
security_handlers = create_security_exception_handlers()
for exc_type, handler in security_handlers.items():
    app.add_exception_handler(exc_type, handler)

# Security Middleware
if settings.ENABLE_SECURITY_HEADERS:
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        security_headers = get_security_headers()
        for header_name, header_value in security_headers.items():
            response.headers[header_name] = header_value
        
        return response

# Trusted Host Middleware (only in production)
if settings.is_production:
    allowed_hosts = settings.BACKEND_CORS_ORIGINS + ["localhost", "127.0.0.1"]
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )

# CORS Middleware (enhanced security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Total-Count", "X-Request-ID"],
)

# Request ID Middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response

# Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = __import__("time").time()
    
    response = await call_next(request)
    
    process_time = __import__("time").time() - start_time
    
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s - "
        f"Request ID: {getattr(request.state, 'request_id', 'unknown')}"
    )
    
    return response

# Create API router
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include authentication router first (no prefix for auth endpoints)
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])

# Include existing routers with authentication
api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])
api_router.include_router(threads.router, prefix="/threads", tags=["threads"])

# Special case for messages - needs thread_id from path
api_router.include_router(
    messages.router, 
    prefix="/threads/{thread_id}/messages", 
    tags=["messages"]
)

# Include RAG endpoints
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])

# Health check endpoint
api_router.include_router(health.router, prefix="/health", tags=["health"])

# Include API router in app
app.include_router(api_router)


@app.get("/", tags=["status"])
async def root():
    """Root endpoint for health check."""
    return {
        "status": "ok", 
        "message": "Personal RAG Server is running",
        "version": "1.0.0",
        "security_enabled": True,
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["status"])
async def health_check():
    """Detailed health check endpoint."""
    try:
        # Test MongoDB connection
        mongodb_status = "healthy"
        try:
            await mongodb.db.command("ping")
        except Exception as e:
            mongodb_status = f"unhealthy: {str(e)}"
        
        # Get user statistics
        total_users = await user_service.get_user_count()
        active_users = await user_service.get_active_user_count()
        
        return {
            "status": "healthy",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "dependencies": {
                "mongodb": mongodb_status,
                "rate_limiting": "enabled" if limiter else "disabled",
                "security_headers": "enabled" if settings.ENABLE_SECURITY_HEADERS else "disabled"
            },
            "statistics": {
                "total_users": total_users,
                "active_users": active_users
            }
        }
    
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "error": str(e)
        }


@app.get("/info", tags=["status"])
async def app_info():
    """Application information endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "security": {
            "authentication": "JWT + API Keys",
            "authorization": "RBAC",
            "rate_limiting": "Enabled",
            "cors": "Configured",
            "security_headers": settings.ENABLE_SECURITY_HEADERS
        },
        "features": {
            "rag_system": "Enabled",
            "vector_db": settings.VECTOR_DB_TYPE,
            "llm_provider": settings.LLM_PROVIDER,
            "embeddings_model": settings.EMBEDDINGS_MODEL,
            "user_management": "Enabled",
            "api_keys": "Enabled"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.is_development,
        log_level="info"
    )
