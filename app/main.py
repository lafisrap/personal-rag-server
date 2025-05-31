from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import logging
from contextlib import asynccontextmanager

from app.api.endpoints import threads, messages, assistants
from app.core.config import settings
from app.db.mongodb import mongodb

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
    
    yield
    
    # Shutdown: close database connections
    logger.info("Closing MongoDB connection...")
    await mongodb.close_mongo_connection()
    logger.info("MongoDB connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Personal RAG Server with FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Create API router
api_router = APIRouter(prefix=settings.API_V1_STR)

# Include sub-routers
api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])
api_router.include_router(threads.router, prefix="/threads", tags=["threads"])
# Special case for messages - needs thread_id from path
api_router.include_router(
    messages.router, 
    prefix="/threads/{thread_id}/messages", 
    tags=["messages"]
)

# Include API router in app
app.include_router(api_router)


@app.get("/", tags=["status"])
async def root():
    """Root endpoint for health check."""
    return {"status": "ok", "message": "Personal RAG Server is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
