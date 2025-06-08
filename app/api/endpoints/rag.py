from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.services.rag_service import rag_service
from app.api.deps import get_optional_user
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class RAGQueryRequest(BaseModel):
    messages: List[Message]
    filter: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    top_k: int = 5

class RAGQueryResponse(BaseModel):
    content: str
    model: Optional[str] = None
    retrieved_documents: List[Dict[str, Any]] = []

@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(
    request: RAGQueryRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Generate a response using RAG (Retrieval Augmented Generation).
    """
    try:
        # Convert Pydantic Message objects to dictionaries
        messages = [msg.dict() for msg in request.messages]
        
        # Call the RAG service
        response = rag_service.generate_rag_response(
            messages=messages,
            filter=request.filter,
            system_prompt=request.system_prompt,
            top_k=request.top_k
        )
        
        # Return the response
        return RAGQueryResponse(
            content=response["content"],
            model=response.get("model"),
            retrieved_documents=response.get("retrieved_documents", [])
        )
    except Exception as e:
        logger.error(f"Error in RAG query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")

class DocumentAddRequest(BaseModel):
    content: str
    metadata: Dict[str, Any]
    chunk_size: int = 1000
    chunk_overlap: int = 200

class DocumentAddResponse(BaseModel):
    document_id: str

@router.post("/documents", response_model=DocumentAddResponse)
async def add_document(
    request: DocumentAddRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Add a document to the RAG system.
    """
    try:
        # Add document to the RAG service
        doc_id = rag_service.add_document(
            content=request.content,
            metadata=request.metadata,
            chunk_size=request.chunk_size,
            chunk_overlap=request.chunk_overlap
        )
        
        return DocumentAddResponse(document_id=doc_id)
    except Exception as e:
        logger.error(f"Error adding document: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")

class SearchRequest(BaseModel):
    query: str
    filter: Optional[Dict[str, Any]] = None
    top_k: int = 5

@router.post("/search", response_model=List[Dict[str, Any]])
async def search_documents(
    request: SearchRequest,
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Search for documents using semantic search.
    """
    try:
        # Search for documents
        results = rag_service.query(
            query_text=request.query,
            filter=request.filter,
            top_k=request.top_k
        )
        
        return results
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") 