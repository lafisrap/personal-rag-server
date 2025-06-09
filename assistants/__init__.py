"""
Philosophical Assistants Package

This package provides integration of philosophical assistants with the RAG system.
Each assistant represents a distinct philosophical worldview:
1. Idealismus - Represented by Aurelian I. Schelling
2. Materialismus - Represented by Aloys I. Freud
3. Realismus - Represented by Arvid I. Steiner
4. Spiritualismus - Represented by Amara I. Steiner
"""

from .pinecone_integration import AssistantManager, PineconeClient, EmbeddingClient
from .template_processor import TemplateProcessor
from .api_extensions import register_router
from .common_instructions import compose_instructions, extract_worldview_instructions, update_assistant_config

__all__ = [
    'AssistantManager',
    'PineconeClient',
    'EmbeddingClient',
    'TemplateProcessor',
    'register_router',
    'compose_instructions',
    'extract_worldview_instructions',
    'update_assistant_config'
] 