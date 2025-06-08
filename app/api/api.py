from fastapi import APIRouter
from app.api.endpoints import auth, health, assistants, messages, threads, rag

api_router = APIRouter()

# Include various endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(threads.router, prefix="/threads", tags=["threads"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"]) 