from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union, Literal
from datetime import datetime
import uuid


class ContentBlock(BaseModel):
    """Base schema for message content blocks."""
    type: str


class TextContentBlock(ContentBlock):
    """Schema for text content blocks."""
    type: Literal["text"] = "text"
    text: str


class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    role: Literal["user", "assistant"] = Field(..., description="The role of the entity creating the message")
    content: str = Field(..., description="The content of the message")
    file_ids: Optional[List[str]] = Field(default_factory=list, description="File IDs attached to the message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the message")
    
    def to_content_blocks(self) -> List[Dict[str, Any]]:
        """Convert plain text content to content blocks."""
        return [{"type": "text", "text": self.content}]


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: str = Field(..., description="The message ID")
    object: str = Field(default="thread.message", description="The object type")
    created_at: int = Field(..., description="Creation timestamp")
    thread_id: str = Field(..., description="The thread ID")
    role: str = Field(..., description="The role of the entity creating the message")
    content: List[Dict[str, Any]] = Field(..., description="The content of the message in blocks")
    file_ids: List[str] = Field(default_factory=list, description="File IDs attached to the message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the message")
    
    @staticmethod
    def from_mongo(message_doc: Dict[str, Any]) -> "MessageResponse":
        """Create a MessageResponse from a MongoDB document."""
        return MessageResponse(
            id=message_doc.get("message_id", str(message_doc.get("_id"))),
            created_at=int(message_doc.get("created_at", datetime.now()).timestamp()),
            thread_id=message_doc.get("thread_id"),
            role=message_doc.get("role"),
            content=message_doc.get("content", []),
            file_ids=message_doc.get("file_ids", []),
            metadata=message_doc.get("metadata")
        )


class MessageList(BaseModel):
    """Schema for message list response."""
    object: str = Field(default="list", description="The object type")
    data: List[MessageResponse] = Field(default_factory=list, description="List of messages")
    first_id: Optional[str] = Field(default=None, description="ID of the first message in the list")
    last_id: Optional[str] = Field(default=None, description="ID of the last message in the list")
    has_more: bool = Field(default=False, description="Whether there are more messages")


class MessageUpdate(BaseModel):
    """Schema for updating a message."""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata for the message")


class MessageDelete(BaseModel):
    """Schema for message deletion response."""
    id: str = Field(..., description="The message ID")
    object: str = Field(default="thread.message.deleted", description="The object type")
    deleted: bool = Field(default=True, description="Whether the message was deleted")
