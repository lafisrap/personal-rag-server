from fastapi import APIRouter, HTTPException, Depends, Query
from app.models.thread import (
    ThreadCreate,
    ThreadResponse,
    ThreadList,
    ThreadUpdate,
    ThreadDelete
)
from app.db.mongodb import mongodb
from typing import Optional, List
from datetime import datetime
import uuid

router = APIRouter()


@router.post("", response_model=ThreadResponse)
async def create_thread(thread: ThreadCreate):
    """Create a new thread."""
    try:
        thread_id = str(uuid.uuid4())
        now = datetime.now()
        
        thread_doc = {
            "thread_id": thread_id,
            "metadata": thread.metadata,
            "created_at": now,
            "modified_at": now
        }
        
        await mongodb.get_threads_collection().insert_one(thread_doc)
        
        return ThreadResponse(
            id=thread_id,
            created_at=int(now.timestamp()),
            metadata=thread.metadata
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


@router.get("", response_model=ThreadList)
async def list_threads(
    limit: int = Query(20, ge=1, le=100),
    order: str = Query("desc", regex="^(asc|desc)$"),
    after: Optional[str] = Query(None),
    before: Optional[str] = Query(None)
):
    """List threads."""
    try:
        # Build query
        query = {}
        if after:
            query["thread_id"] = {"$gt": after} if order == "asc" else {"$lt": after}
        elif before:
            query["thread_id"] = {"$lt": before} if order == "asc" else {"$gt": before}
        
        # Set sort order
        sort_order = 1 if order == "asc" else -1
        
        # Query database
        cursor = mongodb.get_threads_collection().find(query).sort("created_at", sort_order).limit(limit)
        
        # Convert to list
        threads = await cursor.to_list(length=limit)
        
        # Check if there are more threads
        has_more = len(threads) == limit
        
        # Create response
        thread_list = ThreadList(
            data=[ThreadResponse.from_mongo(thread) for thread in threads],
            has_more=has_more
        )
        
        if threads:
            thread_list.first_id = threads[0]["thread_id"]
            thread_list.last_id = threads[-1]["thread_id"]
        
        return thread_list
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list threads: {str(e)}")


@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(thread_id: str):
    """Get a thread by ID."""
    try:
        thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return ThreadResponse.from_mongo(thread)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")


@router.post("/{thread_id}", response_model=ThreadResponse)
async def update_thread(thread_id: str, thread_update: ThreadUpdate):
    """Update a thread."""
    try:
        thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Update fields
        update_data = {
            "modified_at": datetime.now()
        }
        
        if thread_update.metadata is not None:
            update_data["metadata"] = thread_update.metadata
        
        # Update in database
        await mongodb.get_threads_collection().update_one(
            {"thread_id": thread_id},
            {"$set": update_data}
        )
        
        # Get updated thread
        updated_thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        return ThreadResponse.from_mongo(updated_thread)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thread: {str(e)}")


@router.delete("/{thread_id}", response_model=ThreadDelete)
async def delete_thread(thread_id: str):
    """Delete a thread."""
    try:
        # Check if thread exists
        thread = await mongodb.get_threads_collection().find_one({"thread_id": thread_id})
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        # Delete thread
        await mongodb.get_threads_collection().delete_one({"thread_id": thread_id})
        
        # Delete all messages in thread
        await mongodb.get_messages_collection().delete_many({"thread_id": thread_id})
        
        return ThreadDelete(id=thread_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")
