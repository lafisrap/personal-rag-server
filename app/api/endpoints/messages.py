from fastapi import APIRouter, HTTPException, Depends, Query, Path
from app.models.message import (
    MessageCreate,
    MessageResponse,
    MessageList,
    MessageUpdate,
    MessageDelete
)
from app.db.mongodb import mongodb
from app.services.rag_service import rag_service
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

router = APIRouter()


@router.post("", response_model=MessageResponse)
async def create_message(thread_id: str, message: MessageCreate):
    """Create a new message in a thread."""
    try:
        # Check if thread exists
        thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        message_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Convert content to blocks
        content_blocks = message.to_content_blocks()
        
        message_doc = {
            "message_id": message_id,
            "thread_id": thread_id,
            "role": message.role,
            "content": content_blocks,
            "file_ids": message.file_ids or [],
            "metadata": message.metadata,
            "created_at": now
        }
        
        # Insert message into database
        await mongodb.get_messages_collection().insert_one(message_doc)
        
        # Update thread's modified_at timestamp
        await mongodb.get_threads_collection().update_one(
            {"thread_id": thread_id},
            {"$set": {"modified_at": now}}
        )
        
        # If this is a user message, generate an assistant response with RAG
        if message.role == "user":
            # Get all messages in the thread
            messages_cursor = mongodb.get_messages_collection().find(
                {"thread_id": thread_id}
            ).sort("created_at", 1)
            
            thread_messages = await messages_cursor.to_list(length=100)
            
            # Format messages for RAG
            formatted_messages = [
                {"role": msg["role"], "content": msg["content"][0]["text"] if msg["content"] else ""}
                for msg in thread_messages
            ]
            
            # Get thread metadata for filtering
            thread_metadata = thread.get("metadata", {})
            
            # Get assistant ID from thread metadata
            assistant_id = thread_metadata.get("assistant_id")
            
            if assistant_id:
                # Get assistant from database
                assistant = await mongodb.get_assistants_collection().find_one({"assistant_id": assistant_id})
                
                if assistant:
                    # Use assistant instructions as system prompt
                    system_prompt = assistant.get("instructions")
                    
                    # Generate RAG response
                    rag_response = rag_service.generate_rag_response(
                        messages=formatted_messages,
                        system_prompt=system_prompt
                    )
                    
                    # Create assistant message
                    assistant_message_id = str(uuid.uuid4())
                    
                    assistant_message_doc = {
                        "message_id": assistant_message_id,
                        "thread_id": thread_id,
                        "role": "assistant",
                        "content": [{"type": "text", "text": rag_response["content"]}],
                        "file_ids": [],
                        "metadata": {
                            "retrieved_documents": rag_response.get("retrieved_documents", []),
                            "model": rag_response.get("model")
                        },
                        "created_at": datetime.now()
                    }
                    
                    # Insert assistant message into database
                    await mongodb.get_messages_collection().insert_one(assistant_message_doc)
        
        return MessageResponse.from_mongo(message_doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create message: {str(e)}")


@router.get("", response_model=MessageList)
async def list_messages(
    thread_id: str,
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
    after: Optional[str] = Query(None),
    before: Optional[str] = Query(None)
):
    """List messages in a thread."""
    try:
        # Check if thread exists
        thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Build query
        query = {"thread_id": thread_id}
        if after:
            query["message_id"] = {"$gt": after} if order == "asc" else {"$lt": after}
        elif before:
            query["message_id"] = {"$lt": before} if order == "asc" else {"$gt": before}
        
        # Set sort order
        sort_order = 1 if order == "asc" else -1
        
        # Query database
        cursor = mongodb.get_messages_collection().find(query).sort("created_at", sort_order).limit(limit)
        
        # Convert to list
        messages = await cursor.to_list(length=limit)
        
        # Check if there are more messages
        has_more = len(messages) == limit
        
        # Create response
        message_list = MessageList(
            data=[MessageResponse.from_mongo(message) for message in messages],
            has_more=has_more
        )
        
        if messages:
            message_list.first_id = messages[0]["message_id"]
            message_list.last_id = messages[-1]["message_id"]
        
        return message_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list messages: {str(e)}")


@router.get("/{message_id}", response_model=MessageResponse)
async def get_message(thread_id: str, message_id: str):
    """Get a message by ID."""
    try:
        message = await mongodb.get_messages_collection().find_one(
            {"thread_id": thread_id, "message_id": message_id}
        )
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        return MessageResponse.from_mongo(message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get message: {str(e)}")


@router.post("/{message_id}", response_model=MessageResponse)
async def update_message(thread_id: str, message_id: str, message_update: MessageUpdate):
    """Update a message."""
    try:
        message = await mongodb.get_messages_collection().find_one(
            {"thread_id": thread_id, "message_id": message_id}
        )
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Update fields
        update_data = {}
        
        if message_update.metadata is not None:
            update_data["metadata"] = message_update.metadata
        
        # Update in database
        if update_data:
            await mongodb.get_messages_collection().update_one(
                {"thread_id": thread_id, "message_id": message_id},
                {"$set": update_data}
            )
        
        # Get updated message
        updated_message = await mongodb.get_messages_collection().find_one(
            {"thread_id": thread_id, "message_id": message_id}
        )
        
        return MessageResponse.from_mongo(updated_message)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update message: {str(e)}")


@router.delete("/{message_id}", response_model=MessageDelete)
async def delete_message(thread_id: str, message_id: str):
    """Delete a message."""
    try:
        # Check if message exists
        message = await mongodb.get_messages_collection().find_one(
            {"thread_id": thread_id, "message_id": message_id}
        )
        
        if not message:
            raise HTTPException(status_code=404, detail="Message not found")
        
        # Delete message
        await mongodb.get_messages_collection().delete_one(
            {"thread_id": thread_id, "message_id": message_id}
        )
        
        return MessageDelete(id=message_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete message: {str(e)}")
