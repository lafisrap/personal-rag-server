"""
Philosophical Assistants Module

This module provides functionality for managing philosophical assistants
across different worldviews using various backends including custom implementations
and Pinecone Assistant API.
"""

# Existing custom assistant functionality
from .common_instructions import compose_instructions, extract_worldview_instructions
from .pinecone_integration import AssistantManager, PineconeClient, EmbeddingClient
from .template_processor import TemplateProcessor

# New Pinecone Assistant API functionality
from .pinecone_assistant_manager import PineconeAssistantManager

__all__ = [
    # Common instructions
    "compose_instructions",
    "extract_worldview_instructions",
    
    # Custom assistant system
    "AssistantManager", 
    "PineconeClient", 
    "EmbeddingClient",
    "TemplateProcessor",
    
    # Pinecone Assistant API
    "PineconeAssistantManager"
] 