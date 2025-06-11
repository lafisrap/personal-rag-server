#!/usr/bin/env python3
"""
Pinecone Assistant Manager

This module provides functionality to create and manage actual Pinecone assistants
using the Pinecone Assistant API, based on the philosophical assistant configurations.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path

from pinecone import Pinecone
from pinecone_plugins.assistant.models.chat import Message

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PineconeAssistantManager:
    """Manager for Pinecone Assistant API integration."""
    
    def __init__(self, api_key: str = None):
        """Initialize the Pinecone Assistant Manager.
        
        Args:
            api_key: Pinecone API key
        """
        self.api_key = api_key or os.environ.get("PINECONE_API_KEY")
        if not self.api_key:
            raise ValueError("PINECONE_API_KEY must be provided or set as environment variable")
        
        self.pc = Pinecone(api_key=self.api_key)
        self.region = "us"  # Default region
        self.assistants = {}
        
    def create_philosophical_assistant(
        self, 
        name: str, 
        instructions: str, 
        worldview: str,
        model: str = None,
        timeout: int = 60
    ) -> Dict[str, Any]:
        """Create a Pinecone assistant for a philosophical worldview.
        
        Args:
            name: Assistant name
            instructions: Full instructions for the assistant
            worldview: Philosophical worldview (Idealismus, Materialismus, etc.)
            model: LLM model to use (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'deepseek-chat')
            timeout: Timeout for assistant creation
            
        Returns:
            Assistant information
        """
        try:
            # Prepare creation parameters
            create_params = {
                "assistant_name": name,
                "instructions": instructions,
                "region": self.region,
                "timeout": timeout
            }
            
            # Add model if specified
            if model:
                create_params["model"] = model
            
            # Create the assistant
            assistant = self.pc.assistant.create_assistant(**create_params)
            
            logger.info(f"Created Pinecone assistant: {name} with model: {model or 'default'}")
            
            # Store assistant info
            assistant_info = {
                "name": name,
                "worldview": worldview,
                "instructions": instructions,
                "model": model,
                "assistant": assistant,
                "created": True
            }
            
            self.assistants[worldview] = assistant_info
            
            return assistant_info
            
        except Exception as e:
            logger.error(f"Error creating assistant {name}: {e}")
            raise
    
    def get_or_create_assistant(self, name: str, worldview: str, instructions: str, model: str = None) -> Any:
        """Get existing assistant or create new one if it doesn't exist.
        
        Args:
            name: Assistant name
            worldview: Philosophical worldview
            instructions: Assistant instructions
            model: LLM model to use (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'deepseek-chat')
            
        Returns:
            Pinecone Assistant instance
        """
        try:
            # Check if assistant already exists
            assistants_list = self.pc.assistant.list_assistants()
            existing_assistant = None
            
            for assistant in assistants_list:
                if assistant.name == name:
                    existing_assistant = self.pc.assistant.Assistant(assistant_name=name)
                    logger.info(f"Found existing assistant: {name}")
                    break
            
            if existing_assistant:
                return existing_assistant
            else:
                # Create new assistant
                logger.info(f"Creating new assistant: {name} with model: {model or 'default'}")
                
                create_params = {
                    "assistant_name": name,
                    "instructions": instructions,
                    "region": self.region,
                    "timeout": 60
                }
                
                # Add model if specified
                if model:
                    create_params["model"] = model
                
                return self.pc.assistant.create_assistant(**create_params)
                
        except Exception as e:
            logger.error(f"Error getting/creating assistant {name}: {e}")
            raise
    
    def upload_documents_to_assistant(
        self, 
        assistant: Any, 
        documents: List[Dict[str, Any]],
        worldview: str
    ) -> List[Dict[str, Any]]:
        """Upload documents to a Pinecone assistant.
        
        Args:
            assistant: Pinecone Assistant instance
            documents: List of documents with path and metadata
            worldview: Philosophical worldview for metadata
            
        Returns:
            List of upload results
        """
        upload_results = []
        
        for doc in documents:
            try:
                # Add worldview to metadata
                metadata = doc.get("metadata", {})
                metadata["worldview"] = worldview
                
                response = assistant.upload_file(
                    file_path=doc["path"],
                    metadata=metadata,
                    timeout=None
                )
                
                upload_results.append({
                    "file": doc["path"],
                    "status": "success",
                    "response": response
                })
                
                logger.info(f"Uploaded {doc['path']} to {assistant.name}")
                
            except Exception as e:
                upload_results.append({
                    "file": doc["path"],
                    "status": "error",
                    "error": str(e)
                })
                logger.error(f"Error uploading {doc['path']}: {e}")
        
        return upload_results
    
    def chat_with_assistant(
        self, 
        assistant: Any, 
        message: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Chat with a Pinecone assistant.
        
        Args:
            assistant: Pinecone Assistant instance
            message: User message
            chat_history: Previous chat messages
            
        Returns:
            Chat response with citations
        """
        try:
            # Prepare messages
            messages = []
            
            # Add chat history if provided
            if chat_history:
                for msg in chat_history:
                    messages.append(Message(role=msg["role"], content=msg["content"]))
            
            # Add current message
            messages.append(Message(role="user", content=message))
            
            # Get response
            response = assistant.chat(messages=messages)
            
            return {
                "message": response.message.content,
                "citations": getattr(response, 'citations', []),
                "usage": getattr(response, 'usage', {}),
                "model": getattr(response, 'model', 'unknown')
            }
            
        except Exception as e:
            logger.error(f"Error chatting with assistant: {e}")
            raise
    
    def query_with_context(
        self, 
        assistant: Any, 
        query: str,
        metadata_filter: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Query assistant and get context snippets.
        
        Args:
            assistant: Pinecone Assistant instance
            query: Query text
            metadata_filter: Optional metadata filter
            
        Returns:
            Context response with snippets
        """
        try:
            response = assistant.context(
                query=query,
                filter=metadata_filter
            )
            
            return {
                "query": query,
                "snippets": [
                    {
                        "content": snippet.content,
                        "score": snippet.score,
                        "metadata": getattr(snippet, 'metadata', {})
                    }
                    for snippet in response.snippets
                ]
            }
            
        except Exception as e:
            logger.error(f"Error querying context: {e}")
            raise
    
    def create_all_philosophical_assistants(self, config_dir: str = "assistants/config") -> Dict[str, Any]:
        """Create all philosophical assistants from configuration files.
        
        Args:
            config_dir: Directory containing assistant configuration files
            
        Returns:
            Dictionary of created assistants
        """
        config_path = Path(config_dir)
        if not config_path.exists():
            raise ValueError(f"Configuration directory not found: {config_dir}")
        
        worldviews = ["idealismus", "materialismus", "realismus", "spiritualismus"]
        created_assistants = {}
        
        for worldview in worldviews:
            config_file = config_path / f"{worldview}.json"
            
            if not config_file.exists():
                logger.warning(f"Configuration file not found: {config_file}")
                continue
            
            try:
                # Load configuration
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                name = config.get("name", f"{worldview.title()}_Assistant")
                instructions = config.get("instructions", "")
                worldview_title = worldview.title()
                
                # Create assistant
                assistant = self.get_or_create_assistant(
                    name=name,
                    worldview=worldview_title,
                    instructions=instructions
                )
                
                created_assistants[worldview_title] = {
                    "name": name,
                    "worldview": worldview_title,
                    "assistant": assistant,
                    "config": config
                }
                
                logger.info(f"Processed {worldview_title} assistant")
                
            except Exception as e:
                logger.error(f"Error processing {worldview} configuration: {e}")
                created_assistants[worldview.title()] = {
                    "error": str(e)
                }
        
        return created_assistants
    
    def create_from_openai_config(self, openai_config: Dict[str, Any], model: str = None) -> Any:
        """Create Pinecone assistant from OpenAI assistant configuration.
        
        Args:
            openai_config: OpenAI assistant configuration
            model: LLM model to use (e.g., 'gpt-4o', 'claude-3-5-sonnet', 'deepseek-chat')
            
        Returns:
            Pinecone Assistant instance
        """
        try:
            name = openai_config.get("name", "Unknown_Assistant")
            instructions = openai_config.get("instructions", "")
            
            # Clean the assistant name for Pinecone (lowercase with hyphens)
            clean_name = name.replace(" ", "-").replace(".", "-").lower()
            
            assistant = self.get_or_create_assistant(
                name=clean_name,
                worldview=name,  # Use original name as worldview
                instructions=instructions,
                model=model
            )
            
            logger.info(f"Created Pinecone assistant from OpenAI config: {name} with model: {model or 'default'}")
            return assistant
            
        except Exception as e:
            logger.error(f"Error creating assistant from OpenAI config: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available LLM models for Pinecone Assistant.
        
        Returns:
            List of available model names
        """
        # Based on Pinecone documentation, these are the commonly supported models
        # deepseek-reasoner is the default for philosophical reasoning
        return [
            "deepseek-reasoner",  # DeepSeek Reasoner (default for philosophy)
            "deepseek-chat",      # DeepSeek Chat model
            "claude-3-5-sonnet",  # Anthropic Claude 3.5 Sonnet
            "gpt-4o",             # OpenAI GPT-4o
            "gpt-4o-mini",        # OpenAI GPT-4o Mini
        ]
    
    def list_assistants(self) -> List[Dict[str, Any]]:
        """List all Pinecone assistants.
        
        Returns:
            List of assistant information
        """
        try:
            assistants_list = self.pc.assistant.list_assistants()
            return [
                {
                    "name": assistant.name,
                    "created_on": getattr(assistant, 'created_on', 'unknown'),
                    "status": getattr(assistant, 'status', 'unknown'),
                    "model": getattr(assistant, 'model', 'unknown')
                }
                for assistant in assistants_list
            ]
        except Exception as e:
            logger.error(f"Error listing assistants: {e}")
            raise
    
    def delete_assistant(self, assistant_name: str) -> bool:
        """Delete a Pinecone assistant.
        
        Args:
            assistant_name: Name of the assistant to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.pc.assistant.delete_assistant(assistant_name=assistant_name)
            logger.info(f"Deleted assistant: {assistant_name}")
            return True
        except Exception as e:
            logger.error(f"Error deleting assistant {assistant_name}: {e}")
            return False

# Example usage and testing
async def main():
    """Main function for testing Pinecone Assistant functionality."""
    try:
        # Initialize manager
        manager = PineconeAssistantManager()
        
        # List existing assistants
        assistants = manager.list_assistants()
        print(f"Existing assistants: {len(assistants)}")
        for assistant in assistants:
            print(f"- {assistant['name']} (Status: {assistant['status']})")
        
        # Create philosophical assistants from config
        print("\nCreating philosophical assistants...")
        created = manager.create_all_philosophical_assistants()
        
        for worldview, info in created.items():
            if "error" in info:
                print(f"❌ {worldview}: {info['error']}")
            else:
                print(f"✅ {worldview}: {info['name']}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 