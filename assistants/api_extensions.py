#!/usr/bin/env python3
"""
API Extensions for Philosophical Assistants

This script extends the API with endpoints for managing philosophical assistants
and querying them with templates.
"""

import os
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Query, Path
from pydantic import BaseModel, Field

# Import local modules
# These would be imported from your actual application
from .pinecone_integration import AssistantManager, PineconeClient
from .template_processor import TemplateProcessor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/assistants", tags=["assistants"])

# Initialize managers
assistant_manager = AssistantManager()
template_processor = TemplateProcessor()
pinecone_client = PineconeClient()

# Models
class AssistantBase(BaseModel):
    """Base model for assistant data."""
    name: str = Field(..., description="Name of the assistant")
    description: Optional[str] = Field(None, description="Description of the assistant")
    instructions: str = Field(..., description="Instructions for the assistant")
    weltanschauung: str = Field(..., description="Philosophical worldview")
    model: str = Field("o1", description="Model to use for the assistant")
    temperature: float = Field(1.0, description="Temperature for generation")
    top_p: float = Field(1.0, description="Top-p for generation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class AssistantCreate(AssistantBase):
    """Model for creating a new assistant."""
    pass

class AssistantUpdate(BaseModel):
    """Model for updating an assistant."""
    name: Optional[str] = Field(None, description="Name of the assistant")
    description: Optional[str] = Field(None, description="Description of the assistant")
    instructions: Optional[str] = Field(None, description="Instructions for the assistant")
    weltanschauung: Optional[str] = Field(None, description="Philosophical worldview")
    model: Optional[str] = Field(None, description="Model to use for the assistant")
    temperature: Optional[float] = Field(None, description="Temperature for generation")
    top_p: Optional[float] = Field(None, description="Top-p for generation")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class Assistant(AssistantBase):
    """Model for assistant data with ID."""
    id: str = Field(..., description="Unique ID of the assistant")

class TemplateVariables(BaseModel):
    """Model for template variables."""
    gedanke_in_weltanschauung: Optional[str] = Field(None, description="Philosophical thought to correct")
    aspekte: Optional[str] = Field(None, description="Aspects to consider")
    korrektur: Optional[str] = Field(None, description="Corrected philosophical thought")
    gedanke: Optional[str] = Field(None, description="Philosophical thought to repeat")
    stichwort: Optional[str] = Field(None, description="Keywords to include")

class AssistantQuery(BaseModel):
    """Model for querying an assistant."""
    query: str = Field(..., description="Query text")
    template: Optional[str] = Field(None, description="Template to use")
    template_variables: Optional[TemplateVariables] = Field(None, description="Template variables")
    top_k: int = Field(5, description="Number of results to return")

class AssistantResponse(BaseModel):
    """Model for assistant response."""
    response: Any = Field(..., description="Assistant response")
    retrieved_documents: Optional[List[Dict[str, Any]]] = Field(None, description="Retrieved documents")

# Helper functions
def get_assistant_by_id(assistant_id: str) -> Dict[str, Any]:
    """Get assistant by ID."""
    for worldview, assistant in assistant_manager.assistants.items():
        if assistant.get("id") == assistant_id:
            return assistant
    
    raise HTTPException(status_code=404, detail=f"Assistant with ID {assistant_id} not found")

def save_assistant_config(assistant: Dict[str, Any]) -> None:
    """Save assistant configuration to file."""
    try:
        worldview = assistant["weltanschauung"]
        config_dir = assistant_manager.config_dir
        os.makedirs(config_dir, exist_ok=True)
        
        config_path = os.path.join(config_dir, f"{worldview.lower()}.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(assistant, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved configuration for {worldview} assistant")
    except Exception as e:
        logger.error(f"Error saving assistant configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving assistant configuration: {str(e)}")

# Endpoints
@router.get("/", response_model=List[Assistant])
async def list_assistants():
    """List all assistants."""
    try:
        assistants = assistant_manager.list_assistants()
        return assistants
    except Exception as e:
        logger.error(f"Error listing assistants: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing assistants: {str(e)}")

@router.post("/", response_model=Assistant, status_code=201)
async def create_assistant(assistant: AssistantCreate):
    """Create a new assistant."""
    try:
        # Generate ID
        assistant_id = str(uuid.uuid4())
        
        # Create assistant dict
        assistant_dict = assistant.dict()
        assistant_dict["id"] = assistant_id
        
        # Add metadata if not provided
        if not assistant_dict.get("metadata"):
            assistant_dict["metadata"] = {
                "created_by": "personal-rag-server",
                "version": "1.0"
            }
        
        # Save assistant configuration
        save_assistant_config(assistant_dict)
        
        # Reload assistants
        assistant_manager._load_assistants()
        
        return assistant_dict
    except Exception as e:
        logger.error(f"Error creating assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating assistant: {str(e)}")

@router.get("/{assistant_id}", response_model=Assistant)
async def get_assistant(assistant_id: str):
    """Get assistant by ID."""
    try:
        assistant = get_assistant_by_id(assistant_id)
        return assistant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting assistant: {str(e)}")

@router.put("/{assistant_id}", response_model=Assistant)
async def update_assistant(assistant_id: str, update_data: AssistantUpdate):
    """Update an assistant."""
    try:
        # Get existing assistant
        assistant = get_assistant_by_id(assistant_id)
        
        # Update fields
        update_dict = update_data.dict(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                assistant[key] = value
        
        # Save assistant configuration
        save_assistant_config(assistant)
        
        # Reload assistants
        assistant_manager._load_assistants()
        
        return assistant
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating assistant: {str(e)}")

@router.delete("/{assistant_id}")
async def delete_assistant(assistant_id: str):
    """Delete an assistant."""
    try:
        # Get existing assistant
        assistant = get_assistant_by_id(assistant_id)
        worldview = assistant["weltanschauung"]
        
        # Delete configuration file
        config_path = os.path.join(assistant_manager.config_dir, f"{worldview.lower()}.json")
        if os.path.exists(config_path):
            os.remove(config_path)
        
        # Reload assistants
        assistant_manager._load_assistants()
        
        return {"message": f"Assistant {assistant_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting assistant: {str(e)}")

@router.post("/{assistant_id}/query", response_model=AssistantResponse)
async def query_assistant(assistant_id: str, query: AssistantQuery):
    """Query an assistant."""
    try:
        # Get assistant
        assistant = get_assistant_by_id(assistant_id)
        worldview = assistant["weltanschauung"]
        
        # Process template if provided
        prompt = query.query
        if query.template:
            template_vars = query.template_variables.dict(exclude_unset=True) if query.template_variables else {}
            
            if query.template == "gedankenfehler-formulieren":
                prompt = template_processor.process_gedankenfehler_template(
                    worldview=worldview,
                    gedanke_in_weltanschauung=template_vars.get("gedanke_in_weltanschauung", ""),
                    aspekte=template_vars.get("aspekte")
                )
            elif query.template == "gedankenfehler-glossar":
                prompt = template_processor.process_glossar_template(
                    worldview=worldview,
                    korrektur=template_vars.get("korrektur", "")
                )
            elif query.template == "gedankenfehler-wiederholen":
                prompt = template_processor.process_wiederholen_template(
                    worldview=worldview,
                    gedanke=template_vars.get("gedanke", ""),
                    stichwort=template_vars.get("stichwort", "")
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unknown template: {query.template}")
        
        # Query knowledge base
        results = await assistant_manager.query_knowledge_base(
            worldview=worldview,
            query_text=prompt if not query.template else query.query,
            top_k=query.top_k
        )
        
        # Extract retrieved documents
        retrieved_documents = []
        for match in results.get("matches", []):
            if "metadata" in match and "text" in match["metadata"]:
                retrieved_documents.append({
                    "text": match["metadata"]["text"],
                    "score": match.get("score", 0),
                    "metadata": {k: v for k, v in match["metadata"].items() if k != "text"}
                })
        
        # In a real implementation, you would call an LLM here with the prompt and retrieved documents
        # For now, we'll just return the prompt and documents
        
        # Parse template response if needed
        response = prompt
        if query.template:
            # In a real implementation, this would be the LLM's response
            # For now, we'll just return a placeholder
            response = {
                "message": "This is a placeholder for the LLM response.",
                "template_used": query.template,
                "worldview": worldview
            }
        
        return {
            "response": response,
            "retrieved_documents": retrieved_documents
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying assistant: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying assistant: {str(e)}")

def register_router(app):
    """Register the router with the FastAPI app."""
    app.include_router(router)
    logger.info("Registered assistants API router") 