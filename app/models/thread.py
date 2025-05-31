from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid


class ThreadCreate(BaseModel):
    """Schema for creating a new thread."""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the thread")


class ThreadResponse(BaseModel):
    """Schema for thread response."""
    id: str = Field(..., description="The thread ID")
    object: str = Field(default="thread", description="The object type")
    created_at: int = Field(..., description="Creation timestamp")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the thread")
    
    @staticmethod
    def from_mongo(thread_doc: Dict[str, Any]) -> "ThreadResponse":
        """Create a ThreadResponse from a MongoDB document."""
        return ThreadResponse(
            id=thread_doc.get("thread_id", str(thread_doc.get("_id"))),
            created_at=int(thread_doc.get("created_at", datetime.now()).timestamp()),
            metadata=thread_doc.get("metadata")
        )


class ThreadList(BaseModel):
    """Schema for thread list response."""
    object: str = Field(default="list", description="The object type")
    data: List[ThreadResponse] = Field(default_factory=list, description="List of threads")
    first_id: Optional[str] = Field(default=None, description="ID of the first thread in the list")
    last_id: Optional[str] = Field(default=None, description="ID of the last thread in the list")
    has_more: bool = Field(default=False, description="Whether there are more threads")


class ThreadUpdate(BaseModel):
    """Schema for updating a thread."""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the thread")


class ThreadDelete(BaseModel):
    """Schema for thread deletion response."""
    id: str = Field(..., description="The thread ID")
    object: str = Field(default="thread.deleted", description="The object type")
    deleted: bool = Field(default=True, description="Whether the thread was deleted")
