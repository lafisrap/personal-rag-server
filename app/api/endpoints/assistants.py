from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.assistant import (
    AssistantCreate,
    AssistantResponse,
    AssistantList,
    AssistantUpdate,
    AssistantDelete
)
from app.models.user import TokenData, Permission
from app.core.security import require_permission, get_current_user
from app.db.mongodb import mongodb
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()


@router.post("", response_model=AssistantResponse)
async def create_assistant(
    assistant: AssistantCreate,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_CONVERSATIONS))
):
    """Create a new assistant."""
    try:
        assistant_id = str(uuid.uuid4())
        now = datetime.now()
        
        assistant_doc = {
            "assistant_id": assistant_id,
            "name": assistant.name,
            "description": assistant.description,
            "instructions": assistant.instructions,
            "model": assistant.model,
            "tools": assistant.tools,
            "metadata": assistant.metadata,
            "created_by": current_user.user_id,
            "created_at": now,
            "modified_at": now
        }
        
        await mongodb.get_assistants_collection().insert_one(assistant_doc)
        
        return AssistantResponse.from_mongo(assistant_doc)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create assistant: {str(e)}")


@router.get("", response_model=AssistantList)
async def list_assistants(
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
    after: Optional[str] = Query(None),
    before: Optional[str] = Query(None),
    current_user: TokenData = Depends(require_permission(Permission.READ_CONVERSATIONS))
):
    """List assistants."""
    try:
        # Build query - users can only see their own assistants unless they're admin
        query = {}
        if Permission.ADMIN_SYSTEM not in current_user.permissions:
            query["created_by"] = current_user.user_id
            
        if after:
            query["assistant_id"] = {"$gt": after} if order == "asc" else {"$lt": after}
        elif before:
            query["assistant_id"] = {"$lt": before} if order == "asc" else {"$gt": before}
        
        # Set sort order
        sort_order = 1 if order == "asc" else -1
        
        # Query database
        cursor = mongodb.get_assistants_collection().find(query).sort("created_at", sort_order).limit(limit)
        
        # Convert to list
        assistants = await cursor.to_list(length=limit)
        
        # Check if there are more assistants
        has_more = len(assistants) == limit
        
        # Create response
        assistant_list = AssistantList(
            data=[AssistantResponse.from_mongo(assistant) for assistant in assistants],
            has_more=has_more
        )
        
        if assistants:
            assistant_list.first_id = assistants[0]["assistant_id"]
            assistant_list.last_id = assistants[-1]["assistant_id"]
        
        return assistant_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list assistants: {str(e)}")


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(
    assistant_id: str,
    current_user: TokenData = Depends(require_permission(Permission.READ_CONVERSATIONS))
):
    """Get an assistant by ID."""
    try:
        # Build query to ensure user can only access their own assistants (unless admin)
        query = {"assistant_id": assistant_id}
        if Permission.ADMIN_SYSTEM not in current_user.permissions:
            query["created_by"] = current_user.user_id
            
        assistant = await mongodb.get_assistants_collection().find_one(query)
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        return AssistantResponse.from_mongo(assistant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get assistant: {str(e)}")


@router.post("/{assistant_id}", response_model=AssistantResponse)
async def update_assistant(
    assistant_id: str, 
    assistant_update: AssistantUpdate,
    current_user: TokenData = Depends(require_permission(Permission.WRITE_CONVERSATIONS))
):
    """Update an assistant."""
    try:
        # Build query to ensure user can only update their own assistants (unless admin)
        query = {"assistant_id": assistant_id}
        if Permission.ADMIN_SYSTEM not in current_user.permissions:
            query["created_by"] = current_user.user_id
            
        assistant = await mongodb.get_assistants_collection().find_one(query)
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # Update fields
        update_data = {
            "modified_at": datetime.now(),
            "modified_by": current_user.user_id
        }
        
        if assistant_update.name is not None:
            update_data["name"] = assistant_update.name
        
        if assistant_update.description is not None:
            update_data["description"] = assistant_update.description
        
        if assistant_update.instructions is not None:
            update_data["instructions"] = assistant_update.instructions
        
        if assistant_update.model is not None:
            update_data["model"] = assistant_update.model
        
        if assistant_update.tools is not None:
            update_data["tools"] = assistant_update.tools
        
        if assistant_update.metadata is not None:
            update_data["metadata"] = assistant_update.metadata
        
        # Update in database
        await mongodb.get_assistants_collection().update_one(
            {"assistant_id": assistant_id},
            {"$set": update_data}
        )
        
        # Get updated assistant
        updated_assistant = await mongodb.get_assistants_collection().find_one({"assistant_id": assistant_id})
        
        return AssistantResponse.from_mongo(updated_assistant)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update assistant: {str(e)}")


@router.delete("/{assistant_id}", response_model=AssistantDelete)
async def delete_assistant(
    assistant_id: str,
    current_user: TokenData = Depends(require_permission(Permission.DELETE_CONVERSATIONS))
):
    """Delete an assistant."""
    try:
        # Build query to ensure user can only delete their own assistants (unless admin)
        query = {"assistant_id": assistant_id}
        if Permission.ADMIN_SYSTEM not in current_user.permissions:
            query["created_by"] = current_user.user_id
            
        # Check if assistant exists
        assistant = await mongodb.get_assistants_collection().find_one(query)
        
        if not assistant:
            raise HTTPException(status_code=404, detail="Assistant not found")
        
        # Delete assistant
        await mongodb.get_assistants_collection().delete_one({"assistant_id": assistant_id})
        
        return AssistantDelete(id=assistant_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete assistant: {str(e)}")
