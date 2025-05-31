from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Literal
from datetime import datetime


class AssistantCreate(BaseModel):
    """Schema for creating a new assistant."""
    name: Optional[str] = Field(default=None, description="The name of the assistant")
    description: Optional[str] = Field(default=None, description="The description of the assistant")
    instructions: str = Field(..., description="The instructions for the assistant")
    model: str = Field(..., description="The model to use for the assistant")
    tools: Optional[List[Dict[str, Any]]] = Field(default_factory=list, description="The tools the assistant can use")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the assistant")


class AssistantResponse(BaseModel):
    """Schema for assistant response."""
    id: str = Field(..., description="The assistant ID")
    object: str = Field(default="assistant", description="The object type")
    created_at: int = Field(..., description="Creation timestamp")
    name: Optional[str] = Field(default=None, description="The name of the assistant")
    description: Optional[str] = Field(default=None, description="The description of the assistant")
    instructions: str = Field(..., description="The instructions for the assistant")
    model: str = Field(..., description="The model used by the assistant")
    tools: List[Dict[str, Any]] = Field(default_factory=list, description="The tools the assistant can use")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the assistant")
    
    @staticmethod
    def from_mongo(assistant_doc: Dict[str, Any]) -> "AssistantResponse":
        """Create an AssistantResponse from a MongoDB document."""
        return AssistantResponse(
            id=assistant_doc.get("assistant_id", str(assistant_doc.get("_id"))),
            created_at=int(assistant_doc.get("created_at", datetime.now()).timestamp()),
            name=assistant_doc.get("name"),
            description=assistant_doc.get("description"),
            instructions=assistant_doc.get("instructions"),
            model=assistant_doc.get("model"),
            tools=assistant_doc.get("tools", []),
            metadata=assistant_doc.get("metadata")
        )


class AssistantList(BaseModel):
    """Schema for assistant list response."""
    object: str = Field(default="list", description="The object type")
    data: List[AssistantResponse] = Field(default_factory=list, description="List of assistants")
    first_id: Optional[str] = Field(default=None, description="ID of the first assistant in the list")
    last_id: Optional[str] = Field(default=None, description="ID of the last assistant in the list")
    has_more: bool = Field(default=False, description="Whether there are more assistants")


class AssistantUpdate(BaseModel):
    """Schema for updating an assistant."""
    name: Optional[str] = Field(default=None, description="The name of the assistant")
    description: Optional[str] = Field(default=None, description="The description of the assistant")
    instructions: Optional[str] = Field(default=None, description="The instructions for the assistant")
    model: Optional[str] = Field(default=None, description="The model to use for the assistant")
    tools: Optional[List[Dict[str, Any]]] = Field(default=None, description="The tools the assistant can use")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the assistant")


class AssistantDelete(BaseModel):
    """Schema for assistant deletion response."""
    id: str = Field(..., description="The assistant ID")
    object: str = Field(default="assistant.deleted", description="The object type")
    deleted: bool = Field(default=True, description="Whether the assistant was deleted")
