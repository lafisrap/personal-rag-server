from fastapi import APIRouter, Depends
from app.services.embedding_service import embedding_service
from typing import Dict, Any

router = APIRouter()

@router.get("", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint that includes embedding model status."""
    # Get embedding service health
    embedding_health = embedding_service.get_health_check()
    
    return {
        "status": "healthy",
        "api_version": "v1",
        "embedding_service": embedding_health
    } 