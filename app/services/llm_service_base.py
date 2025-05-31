from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class BaseLLMService(ABC):
    """Abstract base class for LLM services."""
    
    @abstractmethod
    def initialize_model(self, **kwargs):
        """Initialize the LLM model."""
        pass
    
    @abstractmethod
    def get_llm_response(self, 
                          messages: List[Dict[str, str]], 
                          system_prompt: Optional[str] = None,
                          temperature: float = 0.7,
                          streaming: bool = False) -> Dict[str, Any]:
        """
        Get a response from the LLM model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to override default
            temperature: Temperature parameter for response generation
            streaming: Whether to stream the response
            
        Returns:
            Dictionary with LLM response and metadata
        """
        pass
    
    @abstractmethod
    def generate_with_rag(self, 
                           messages: List[Dict[str, str]], 
                           context: List[str],
                           system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate a response with RAG (Retrieval Augmented Generation).
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            context: List of context documents from retrieval
            system_prompt: Optional system prompt to override default
            
        Returns:
            Dictionary with LLM response and metadata
        """
        pass 