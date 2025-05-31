from openai import OpenAI
from app.core.config import settings
import logging
from typing import List, Dict, Any, Optional
from app.services.llm_service_base import BaseLLMService

logger = logging.getLogger(__name__)

class OpenAIService(BaseLLMService):
    """Service for interacting with OpenAI Language Models."""
    
    def __init__(self):
        self.client = None
        self.model_name = settings.DEFAULT_LLM_MODEL
    
    def initialize_model(self, **kwargs):
        """Initialize the OpenAI client."""
        try:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info(f"Initialized OpenAI client for model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    def get_llm_response(self, 
                         messages: List[Dict[str, str]], 
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         streaming: bool = False) -> Dict[str, Any]:
        """
        Get a response from the OpenAI model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to override default
            temperature: Temperature parameter for response generation
            streaming: Whether to stream the response
            
        Returns:
            Dictionary with LLM response and metadata
        """
        if not self.client:
            self.initialize_model()
        
        try:
            # Prepare the messages for OpenAI format
            openai_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                openai_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation messages
            for msg in messages:
                openai_messages.append(msg)
            
            # Get response from model
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=openai_messages,
                temperature=temperature,
                stream=streaming
            )
            
            if streaming:
                # In streaming mode, we would handle this differently in the actual API endpoint
                # Here we're just collecting all chunks for compatibility with the interface
                content = ""
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                
                return {
                    "role": "assistant",
                    "content": content,
                    "model": self.model_name
                }
            else:
                return {
                    "role": "assistant",
                    "content": response.choices[0].message.content,
                    "model": self.model_name
                }
                
        except Exception as e:
            logger.error(f"Failed to get OpenAI response: {str(e)}")
            raise
    
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
        if not self.client:
            self.initialize_model()
        
        try:
            # Create a context string from retrieved documents
            context_str = "\n\n".join([f"Document {i+1}: {doc}" for i, doc in enumerate(context)])
            
            # Create a new set of messages with context injected
            rag_messages = messages.copy()
            
            # Get the last user message
            last_user_msg_idx = None
            for i in range(len(rag_messages) - 1, -1, -1):
                if rag_messages[i]["role"] == "user":
                    last_user_msg_idx = i
                    break
            
            if last_user_msg_idx is not None:
                # Modify the last user message to include the context
                augmented_content = (
                    f"Context information:\n{context_str}\n\n"
                    f"User question: {rag_messages[last_user_msg_idx]['content']}\n\n"
                    "Please answer based on the context information provided."
                )
                rag_messages[last_user_msg_idx]["content"] = augmented_content
            
            # Use default response if we couldn't inject context
            return self.get_llm_response(
                messages=rag_messages,
                system_prompt=system_prompt or "You are a helpful assistant that answers questions based on the provided context.",
                temperature=0.5
            )
        except Exception as e:
            logger.error(f"Failed to generate OpenAI RAG response: {str(e)}")
            raise 