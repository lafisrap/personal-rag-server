from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import time

# Import Pinecone Assistant Manager (same as CLI uses)
from assistants.pinecone_assistant_manager import PineconeAssistantManager
from assistants.template_processor import TemplateProcessor
from app.models.user import TokenData
from app.core.security import get_current_user
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()

# OpenAI-compatible response models
class AssistantCapabilities(BaseModel):
    """Assistant capabilities model."""
    templates: List[str] = Field(default=["resolve", "reformulate", "glossary"])
    max_context_length: int = Field(default=8192)
    supported_languages: List[str] = Field(default=["de", "en"])

class AssistantData(BaseModel):
    """Individual assistant data model."""
    id: str
    object: str = Field(default="assistant")
    name: str
    description: Optional[str] = None
    model: str
    instructions: Optional[str] = None
    weltanschauung: Optional[str] = None
    status: str
    created_at: str
    metadata: Optional[Dict[str, Any]] = None
    capabilities: Optional[AssistantCapabilities] = None

class AssistantListResponse(BaseModel):
    """OpenAI-compatible assistant list response."""
    object: str = Field(default="list")
    data: List[AssistantData]
    first_id: Optional[str] = None
    last_id: Optional[str] = None
    has_more: bool = Field(default=False)

# Template endpoint models
class ResolveRequest(BaseModel):
    """Request model for resolving philosophical mistakes."""
    gedanke_in_weltanschauung: str = Field(..., description="Philosophical thought to correct")
    aspekte: Optional[str] = Field(None, description="Additional aspects to consider")

class ResolveResponse(BaseModel):
    """Response model for resolved philosophical mistakes."""
    gedanke: str = Field(..., description="Corrected philosophical thought")
    gedanke_zusammenfassung: str = Field(..., description="Summary of the correction")
    gedanke_kind: str = Field(..., description="Child-friendly explanation")
    assistant_id: str = Field(..., description="ID of the assistant")
    weltanschauung: str = Field(..., description="Philosophical worldview")
    processing_time: float = Field(..., description="Processing time in seconds")

class ReformulateRequest(BaseModel):
    """Request model for reformulating thoughts."""
    gedanke: str = Field(..., description="Thought to reformulate")
    stichwort: str = Field(..., description="Keywords to incorporate")

class ReformulateResponse(BaseModel):
    """Response model for reformulated thoughts."""
    gedanken_in_weltanschauung: List[str] = Field(..., description="Three reformulated variations")
    gedanke: str = Field(..., description="Original thought")
    assistant_id: str = Field(..., description="ID of the assistant")
    weltanschauung: str = Field(..., description="Philosophical worldview")
    processing_time: float = Field(..., description="Processing time in seconds")

class GlossaryTerm(BaseModel):
    """Individual glossary term."""
    begriff: str = Field(..., description="Term")
    beschreibung: str = Field(..., description="Description")

class GlossaryRequest(BaseModel):
    """Request model for generating glossary."""
    korrektur: Optional[str] = Field(None, description="Text to extract concepts from")
    begriffe: Optional[List[str]] = Field(None, description="Specific concepts to define")

class GlossaryResponse(BaseModel):
    """Response model for philosophical glossary."""
    glossar: List[GlossaryTerm] = Field(..., description="Glossary terms and definitions")
    assistant_id: str = Field(..., description="ID of the assistant")
    weltanschauung: str = Field(..., description="Philosophical worldview")
    processing_time: float = Field(..., description="Processing time in seconds")

# Helper functions
def map_assistant_to_worldview(assistant_name: str) -> str:
    """Map assistant name to philosophical worldview."""
    worldview_mapping = {
        "aurelian-i--schelling": "Idealismus",
        "aloys-i--freud": "Materialismus", 
        "arvid-i--steiner": "Realismus",
        "amara-i--steiner": "Spiritualismus"
    }
    return worldview_mapping.get(assistant_name, "Unknown")

def get_assistant_description(worldview: str) -> str:
    """Get description for philosophical worldview."""
    descriptions = {
        "Idealismus": "Philosophical assistant for Idealism worldview - focuses on ideas as primary reality",
        "Materialismus": "Philosophical assistant for Materialism worldview - emphasizes material reality and biological processes",
        "Realismus": "Philosophical assistant for Realism worldview - balances spiritual and material perspectives",
        "Spiritualismus": "Philosophical assistant for Spiritualism worldview - emphasizes spiritual hierarchies and development",
        "Unknown": "Philosophical assistant with unknown worldview"
    }
    return descriptions.get(worldview, "Philosophical assistant")

# API Endpoints
@router.get("", response_model=AssistantListResponse)
async def list_assistants(
    weltanschauung: Optional[str] = Query(None, description="Filter by philosophical worldview"),
    status: Optional[str] = Query(None, description="Filter by status"),
    include_capabilities: bool = Query(False, description="Include template capabilities"),
    current_user: TokenData = Depends(get_current_user)
):
    """List all Pinecone assistants with filtering support."""
    try:
        # Initialize Pinecone Assistant Manager
        manager = PineconeAssistantManager()
        
        # Get all assistants from Pinecone
        pinecone_assistants = manager.list_assistants()
        
        # Convert to API format with filtering
        assistant_data = []
        for assistant in pinecone_assistants:
            assistant_name = assistant.get("name", "")
            assistant_worldview = map_assistant_to_worldview(assistant_name)
            
            # Apply weltanschauung filter
            if weltanschauung and assistant_worldview != weltanschauung:
                continue
            
            # Apply status filter (Pinecone assistants are typically "Ready")
            assistant_status = "Ready"
            if status and assistant_status != status:
                continue
            
            # Build assistant data with safe defaults
            model = assistant.get("model") or "deepseek-reasoner"
            created_at = assistant.get("created_on") or "2024-01-15T10:30:00Z"
            
            assistant_item = AssistantData(
                id=assistant_name,
                name=assistant_name,
                description=get_assistant_description(assistant_worldview),
                model=model,
                instructions="Philosophical assistant with specialized worldview knowledge",
                weltanschauung=assistant_worldview,
                status=assistant_status,
                created_at=created_at,
                metadata={
                    "worldview": assistant_worldview,
                    "created_by": "pinecone-assistant-api"
                }
            )
            
            # Add capabilities if requested
            if include_capabilities:
                assistant_item.capabilities = AssistantCapabilities()
            
            assistant_data.append(assistant_item)
        
        # Build response
        response = AssistantListResponse(data=assistant_data)
        
        if assistant_data:
            response.first_id = assistant_data[0].id
            response.last_id = assistant_data[-1].id
        
        return response
        
    except Exception as e:
        logger.error(f"Error listing assistants: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing assistants: {str(e)}")

@router.get("/{assistant_id}", response_model=AssistantData)
async def get_assistant(
    assistant_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get a specific assistant by ID."""
    try:
        # Initialize Pinecone Assistant Manager
        manager = PineconeAssistantManager()
        
        # Get all assistants and find the requested one
        assistants = manager.list_assistants()
        assistant = None
        for a in assistants:
            if a.get("name") == assistant_id:
                assistant = a
                break
        
        if not assistant:
            raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
        
        # Map to worldview
        worldview = map_assistant_to_worldview(assistant_id)
        
        # Build response with safe defaults
        model = assistant.get("model") or "deepseek-reasoner"
        created_at = assistant.get("created_on") or "2024-01-15T10:30:00Z"
        
        return AssistantData(
            id=assistant_id,
            name=assistant_id,
            description=get_assistant_description(worldview),
            model=model,
            instructions="Philosophical assistant with specialized worldview knowledge",
            weltanschauung=worldview,
            status="Ready",
            created_at=created_at,
            metadata={
                "worldview": worldview,
                "created_by": "pinecone-assistant-api"
            },
            capabilities=AssistantCapabilities()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting assistant: {str(e)}")

@router.delete("/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Delete a Pinecone assistant."""
    try:
        # Initialize Pinecone Assistant Manager
        manager = PineconeAssistantManager()
        
        # Delete the assistant
        success = manager.delete_assistant(assistant_id)
        
        if not success:
            raise HTTPException(status_code=404, detail=f"Failed to delete assistant {assistant_id}")
        
        return {
            "id": assistant_id,
            "object": "assistant.deleted",
            "deleted": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting assistant {assistant_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting assistant: {str(e)}")

# Additional endpoints for Pinecone-specific functionality
@router.get("/{assistant_id}/models")
async def get_available_models(
    assistant_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """Get available models for Pinecone assistants."""
    try:
        manager = PineconeAssistantManager()
        models = manager.get_available_models()
        
        return {
            "object": "list",
            "data": [
                {
                    "id": model,
                    "object": "model",
                    "created": int(datetime.now().timestamp()),
                    "owned_by": "pinecone"
                }
                for model in models
            ]
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

# Template endpoints
@router.post("/{assistant_id}/resolve", response_model=ResolveResponse)
async def resolve_philosophical_mistake(
    assistant_id: str,
    request: ResolveRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Correct philosophical misconceptions from assistant's worldview."""
    start_time = time.time()
    
    try:
        # Initialize managers
        assistant_manager = PineconeAssistantManager()
        template_processor = TemplateProcessor()
        
        # Verify assistant exists and get worldview
        assistants = assistant_manager.list_assistants()
        assistant = None
        for a in assistants:
            if a.get("name") == assistant_id:
                assistant = a
                break
        
        if not assistant:
            raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
        
        worldview = map_assistant_to_worldview(assistant_id)
        if worldview == "Unknown":
            raise HTTPException(status_code=400, detail=f"Unknown worldview for assistant {assistant_id}")
        
        # Generate template prompt
        prompt = template_processor.process_gedankenfehler_template(
            worldview=worldview,
            gedanke_in_weltanschauung=request.gedanke_in_weltanschauung,
            aspekte=request.aspekte
        )
        
        # Get the assistant object
        assistant_obj = assistant_manager.pc.assistant.Assistant(assistant_name=assistant_id)
        
        # Send to assistant via Pinecone
        chat_response = assistant_manager.chat_with_assistant(
            assistant=assistant_obj,
            message=prompt
        )
        
        # Extract the message content
        response = chat_response.get("message", "")
        
        # Parse the JSON response
        parsed_response = template_processor.parse_template_response(response)
        
        processing_time = time.time() - start_time
        
        return ResolveResponse(
            gedanke=parsed_response.get("gedanke", ""),
            gedanke_zusammenfassung=parsed_response.get("gedanke_zusammenfassung", ""),
            gedanke_kind=parsed_response.get("gedanke_kind", ""),
            assistant_id=assistant_id,
            weltanschauung=worldview,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in resolve endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing resolve request: {str(e)}")

@router.post("/{assistant_id}/reformulate", response_model=ReformulateResponse)
async def reformulate_philosophical_thought(
    assistant_id: str,
    request: ReformulateRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Reformulate thoughts from assistant's worldview perspective."""
    start_time = time.time()
    
    try:
        # Initialize managers
        assistant_manager = PineconeAssistantManager()
        template_processor = TemplateProcessor()
        
        # Verify assistant exists and get worldview
        assistants = assistant_manager.list_assistants()
        assistant = None
        for a in assistants:
            if a.get("name") == assistant_id:
                assistant = a
                break
        
        if not assistant:
            raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
        
        worldview = map_assistant_to_worldview(assistant_id)
        if worldview == "Unknown":
            raise HTTPException(status_code=400, detail=f"Unknown worldview for assistant {assistant_id}")
        
        # Generate template prompt
        prompt = template_processor.process_wiederholen_template(
            worldview=worldview,
            gedanke=request.gedanke,
            stichwort=request.stichwort
        )
        
        # Get the assistant object
        assistant_obj = assistant_manager.pc.assistant.Assistant(assistant_name=assistant_id)
        
        # Send to assistant via Pinecone
        chat_response = assistant_manager.chat_with_assistant(
            assistant=assistant_obj,
            message=prompt
        )
        
        # Extract the message content
        response = chat_response.get("message", "")
        
        # Parse the JSON response
        parsed_response = template_processor.parse_template_response(response)
        
        processing_time = time.time() - start_time
        
        return ReformulateResponse(
            gedanken_in_weltanschauung=parsed_response.get("gedanken_in_weltanschauung", []),
            gedanke=parsed_response.get("gedanke", request.gedanke),
            assistant_id=assistant_id,
            weltanschauung=worldview,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in reformulate endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing reformulate request: {str(e)}")

@router.post("/{assistant_id}/glossary", response_model=GlossaryResponse)
async def generate_philosophical_glossary(
    assistant_id: str,
    request: GlossaryRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Generate philosophical glossary from text or concepts."""
    start_time = time.time()
    
    try:
        # Validate request
        if not request.korrektur and not request.begriffe:
            raise HTTPException(
                status_code=400, 
                detail="Either 'korrektur' or 'begriffe' must be provided"
            )
        
        # Initialize managers
        assistant_manager = PineconeAssistantManager()
        template_processor = TemplateProcessor()
        
        # Verify assistant exists and get worldview
        assistants = assistant_manager.list_assistants()
        assistant = None
        for a in assistants:
            if a.get("name") == assistant_id:
                assistant = a
                break
        
        if not assistant:
            raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
        
        worldview = map_assistant_to_worldview(assistant_id)
        if worldview == "Unknown":
            raise HTTPException(status_code=400, detail=f"Unknown worldview for assistant {assistant_id}")
        
        # Generate template prompt
        if request.korrektur:
            # Use text to extract concepts
            prompt = template_processor.process_glossar_template(
                worldview=worldview,
                korrektur=request.korrektur
            )
        else:
            # Create a mock correction text from provided concepts
            korrektur_text = f"Key philosophical concepts: {', '.join(request.begriffe)}"
            prompt = template_processor.process_glossar_template(
                worldview=worldview,
                korrektur=korrektur_text
            )
        
        # Get the assistant object
        assistant_obj = assistant_manager.pc.assistant.Assistant(assistant_name=assistant_id)
        
        # Send to assistant via Pinecone
        chat_response = assistant_manager.chat_with_assistant(
            assistant=assistant_obj,
            message=prompt
        )
        
        # Extract the message content
        response = chat_response.get("message", "")
        
        # Parse the JSON response
        parsed_response = template_processor.parse_template_response(response)
        
        # Convert glossary to proper format
        glossary_terms = []
        for term_data in parsed_response.get("glossar", []):
            glossary_terms.append(GlossaryTerm(
                begriff=term_data.get("begriff", ""),
                beschreibung=term_data.get("beschreibung", "")
            ))
        
        processing_time = time.time() - start_time
        
        return GlossaryResponse(
            glossar=glossary_terms,
            assistant_id=assistant_id,
            weltanschauung=worldview,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in glossary endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing glossary request: {str(e)}")

@router.get("/weltanschauungen/list")
async def list_weltanschauungen(
    current_user: TokenData = Depends(get_current_user)
):
    """List available philosophical worldviews with their associated assistants."""
    try:
        # Initialize Pinecone Assistant Manager
        manager = PineconeAssistantManager()
        
        # Get all assistants from Pinecone
        pinecone_assistants = manager.list_assistants()
        
        # Group assistants by worldview
        assistants_by_worldview = {}
        for assistant in pinecone_assistants:
            assistant_name = assistant.get("name", "")
            worldview = map_assistant_to_worldview(assistant_name)
            
            if worldview != "Unknown":
                if worldview not in assistants_by_worldview:
                    assistants_by_worldview[worldview] = []
                
                model = assistant.get("model") or "deepseek-reasoner"
                created_at = assistant.get("created_on") or "2024-01-15T10:30:00Z"
                
                assistants_by_worldview[worldview].append({
                    "id": assistant_name,
                    "name": assistant_name,
                    "model": model,
                    "status": "Ready",
                    "created_at": created_at
                })
        
        # Build worldviews with their assistants
        worldviews = [
            {
                "id": "Idealismus",
                "name": "Idealismus", 
                "description": "Focuses on ideas as primary reality",
                "assistants": assistants_by_worldview.get("Idealismus", [])
            },
            {
                "id": "Materialismus",
                "name": "Materialismus",
                "description": "Emphasizes material reality and biological processes",
                "assistants": assistants_by_worldview.get("Materialismus", [])
            },
            {
                "id": "Realismus", 
                "name": "Realismus",
                "description": "Balances spiritual and material perspectives",
                "assistants": assistants_by_worldview.get("Realismus", [])
            },
            {
                "id": "Spiritualismus",
                "name": "Spiritualismus", 
                "description": "Emphasizes spiritual hierarchies and development",
                "assistants": assistants_by_worldview.get("Spiritualismus", [])
            }
        ]
        
        return {
            "object": "list",
            "data": worldviews
        }
        
    except Exception as e:
        logger.error(f"Error listing weltanschauungen: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing weltanschauungen: {str(e)}")
