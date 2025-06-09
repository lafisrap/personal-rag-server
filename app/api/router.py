from fastapi import APIRouter
from app.api.endpoints import embeddings, search, health

# Import from the new structure
from assistants.api_extensions import router as assistants_router

api_router = APIRouter()

api_router.include_router(embeddings.router, prefix="/embeddings", tags=["embeddings"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(assistants_router)  # Already has prefix "/api/v1/assistants" 