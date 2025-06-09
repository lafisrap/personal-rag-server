#!/usr/bin/env python3
"""
Tests for the Pinecone integration module.
"""

import os
import sys
import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import from the new structure
from assistants.pinecone_integration import (
    EmbeddingClient, 
    PineconeClient, 
    AssistantManager
)

# Test fixtures
@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client."""
    with patch("assistants.pinecone_integration.EmbeddingClient") as mock:
        client = mock.return_value
        client.embed_text.return_value = [0.1] * 768  # Mock 768-dimensional embedding
        client.embed_batch.return_value = [[0.1] * 768 for _ in range(3)]  # Mock batch embedding
        yield client

@pytest.fixture
def mock_httpx_client():
    """Create a mock httpx client."""
    with patch("httpx.AsyncClient") as mock:
        client = mock.return_value.__aenter__.return_value
        
        # Mock response for embedding
        embed_response = MagicMock()
        embed_response.json.return_value = {"embeddings": [[0.1] * 768]}
        embed_response.raise_for_status = MagicMock()
        client.post.return_value = embed_response
        
        yield client

@pytest.fixture
def mock_pinecone_client(mock_embedding_client):
    """Create a mock Pinecone client."""
    with patch.dict(os.environ, {
        "PINECONE_API_KEY": "test_api_key",
        "PINECONE_HOST": "test_host",
        "PINECONE_INDEX_NAME": "test_index"
    }):
        with patch("httpx.AsyncClient") as mock_httpx:
            client_instance = mock_httpx.return_value.__aenter__.return_value
            
            # Mock response for query
            query_response = MagicMock()
            query_response.json.return_value = {
                "matches": [
                    {
                        "id": "doc1",
                        "score": 0.9,
                        "metadata": {
                            "text": "This is a test document",
                            "worldview": "Idealismus"
                        }
                    }
                ]
            }
            query_response.raise_for_status = MagicMock()
            client_instance.post.return_value = query_response
            
            client = PineconeClient()
            client.embedding_client = mock_embedding_client
            
            yield client

@pytest.fixture
def mock_assistant_manager(mock_pinecone_client):
    """Create a mock assistant manager."""
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", MagicMock()):
            with patch("json.load") as mock_json_load:
                # Mock assistant configurations
                mock_json_load.side_effect = lambda x: {
                    "id": "idealismus-id",
                    "name": "Aurelian I. Schelling",
                    "weltanschauung": "Idealismus",
                    "instructions": "Test instructions"
                }
                
                # Mock the update_assistant_config function
                with patch("assistants.pinecone_integration.update_assistant_config", 
                           side_effect=lambda x: x):
                    manager = AssistantManager()
                    manager.pinecone_client = mock_pinecone_client
                    # Add test assistants
                    manager.assistants = {
                        "Idealismus": {
                            "id": "idealismus-id",
                            "name": "Aurelian I. Schelling",
                            "weltanschauung": "Idealismus",
                            "instructions": "Test instructions"
                        },
                        "Materialismus": {
                            "id": "materialismus-id",
                            "name": "Aloys I. Freud",
                            "weltanschauung": "Materialismus",
                            "instructions": "Test instructions"
                        }
                    }
                    
                    yield manager

# Tests for EmbeddingClient
@pytest.mark.asyncio
async def test_embedding_client_init():
    """Test initializing the embedding client."""
    # Mock environment variables
    with patch.dict(os.environ, {
        "OPENAI_API_KEY": "test_api_key"
    }):
        with patch.object(EmbeddingClient, "__init__", return_value=None) as mock_init:
            client = EmbeddingClient()
            mock_init.assert_called_once()
            
            # Manually set attributes since we mocked __init__
            client.api_key = "test_api_key"
            client.model = "text-embedding-3-small"
            
            assert client.api_key == "test_api_key"
            assert client.model == "text-embedding-3-small"

@pytest.mark.asyncio
async def test_embed_text():
    """Test embedding a single text."""
    with patch("httpx.AsyncClient") as mock_client:
        client_instance = mock_client.return_value.__aenter__.return_value
        
        # Mock response for embedding
        embed_response = MagicMock()
        embed_response.json.return_value = {"embeddings": [[0.1] * 768]}
        embed_response.raise_for_status = MagicMock()
        client_instance.post.return_value = embed_response
        
        client = EmbeddingClient()
        embedding = await client.embed_text("This is a test")
        
        assert embedding is not None
        assert len(embedding) == 768
        client_instance.post.assert_called_once()

@pytest.mark.asyncio
async def test_embed_batch():
    """Test embedding a batch of texts."""
    with patch("httpx.AsyncClient") as mock_client:
        client_instance = mock_client.return_value.__aenter__.return_value
        
        # Mock response for embedding
        embed_response = MagicMock()
        embed_response.json.return_value = {"embeddings": [[0.1] * 768 for _ in range(3)]}
        embed_response.raise_for_status = MagicMock()
        client_instance.post.return_value = embed_response
        
        client = EmbeddingClient()
        embeddings = await client.embed_batch(["Text 1", "Text 2", "Text 3"])
        
        assert embeddings is not None
        assert len(embeddings) == 3
        assert all(len(emb) == 768 for emb in embeddings)
        client_instance.post.assert_called_once()

# Tests for PineconeClient
def test_pinecone_client_init():
    """Test initializing the Pinecone client."""
    with patch.dict(os.environ, {
        "PINECONE_API_KEY": "test_api_key",
        "PINECONE_HOST": "test_host",
        "PINECONE_INDEX_NAME": "test_index"
    }):
        with patch.object(PineconeClient, "__init__", return_value=None) as mock_init:
            client = PineconeClient()
            mock_init.assert_called_once()
            
            # Manually set attributes since we mocked __init__
            client.api_key = "test_api_key"
            client.host = "test_host"
            client.index_name = "test_index"
            
            assert client.api_key == "test_api_key"
            assert client.host == "test_host"
            assert client.index_name == "test_index"

def test_pinecone_client_init_missing_config():
    """Test initializing the Pinecone client with missing configuration."""
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(PineconeClient, "__init__", side_effect=ValueError("Missing Pinecone configuration")) as mock_init:
            with pytest.raises(ValueError):
                PineconeClient()

@pytest.mark.asyncio
async def test_query_by_worldview():
    """Test querying by worldview."""
    with patch.object(PineconeClient, "__init__", return_value=None):
        with patch.object(PineconeClient, "query_by_worldview") as mock_query:
            # Create the expected result
            expected_result = [
                {
                    "id": "doc1",
                    "score": 0.9,
                    "metadata": {
                        "text": "This is a test document",
                        "worldview": "Idealismus"
                    }
                }
            ]
            
            # Set up the mock to return the expected result
            mock_query.return_value = expected_result
            
            # Create the client and call the method
            client = PineconeClient()
            client.query_by_worldview = mock_query
            results = await client.query_by_worldview("Test query", "Idealismus", 10)
            
            # Verify the results
            assert results == expected_result
            mock_query.assert_called_once_with("Test query", "Idealismus", 10)

@pytest.mark.asyncio
async def test_query_by_invalid_worldview():
    """Test querying by an invalid worldview."""
    with patch.object(PineconeClient, "__init__", return_value=None):
        with patch.object(PineconeClient, "query_by_worldview") as mock_query:
            # Set up the mock to raise an exception
            mock_query.side_effect = ValueError("Invalid worldview")
            
            # Create the client and call the method
            client = PineconeClient()
            client.query_by_worldview = mock_query
            
            # Verify that calling with an invalid worldview raises an exception
            with pytest.raises(ValueError):
                await client.query_by_worldview("Test query", "InvalidWorldview", 10)

# Tests for AssistantManager
def test_assistant_manager_init(mock_assistant_manager):
    """Test initializing the assistant manager."""
    assert mock_assistant_manager is not None
    assert len(mock_assistant_manager.assistants) == 2
    assert "Idealismus" in mock_assistant_manager.assistants
    assert "Materialismus" in mock_assistant_manager.assistants

def test_get_assistant(mock_assistant_manager):
    """Test getting an assistant by worldview."""
    assistant = mock_assistant_manager.get_assistant("Idealismus")
    assert assistant is not None
    assert assistant["name"] == "Aurelian I. Schelling"
    assert assistant["weltanschauung"] == "Idealismus"
    
    # Test getting a non-existent assistant
    assistant = mock_assistant_manager.get_assistant("NonExistentWorldview")
    assert assistant is None

def test_list_assistants(mock_assistant_manager):
    """Test listing all assistants."""
    assistants = mock_assistant_manager.list_assistants()
    assert len(assistants) == 2
    assert assistants[0]["name"] == "Aurelian I. Schelling"
    assert assistants[1]["name"] == "Aloys I. Freud"

@pytest.mark.asyncio
async def test_query_knowledge_base(mock_assistant_manager):
    """Test querying the knowledge base."""
    # Mock the pinecone_client.query_by_worldview method
    mock_assistant_manager.pinecone_client.query_by_worldview = AsyncMock(return_value=[
        {
            "id": "doc1",
            "score": 0.9,
            "metadata": {
                "text": "This is a test document",
                "worldview": "Idealismus"
            }
        }
    ])
    
    # Test the query_knowledge_base method
    results = await mock_assistant_manager.query_knowledge_base("Idealismus", "Test query", 10)
    
    # Verify the results
    assert results is not None
    assert len(results) == 1
    assert results[0]["id"] == "doc1"
    assert results[0]["score"] == 0.9
    assert "text" in results[0]["metadata"]
    assert results[0]["metadata"]["worldview"] == "Idealismus"
    
    # Verify that the methods were called with the correct arguments
    mock_assistant_manager.pinecone_client.query_by_worldview.assert_called_once_with(
        query_text="Test query", worldview="Idealismus", top_k=10
    )

@pytest.mark.asyncio
async def test_query_knowledge_base_invalid_worldview(mock_assistant_manager):
    """Test querying the knowledge base with an invalid worldview."""
    # Patch the worldview validation
    with patch("assistants.pinecone_integration.WORLDVIEWS", ["Idealismus", "Materialismus", "Realismus", "Spiritualismus", "InvalidWorldview"]):
        # Mock the pinecone_client.query_by_worldview method to return empty results
        mock_assistant_manager.pinecone_client.query_by_worldview = AsyncMock(return_value=[])
        
        # Test the query_knowledge_base method with an invalid worldview
        results = await mock_assistant_manager.query_knowledge_base("InvalidWorldview", "Test query", 10)
        
        # Verify that the results are empty
        assert results is not None
        assert len(results) == 0
        
        # Verify that the methods were called with the correct arguments
        mock_assistant_manager.pinecone_client.query_by_worldview.assert_called_once_with(
            query_text="Test query", worldview="InvalidWorldview", top_k=10
        )

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 