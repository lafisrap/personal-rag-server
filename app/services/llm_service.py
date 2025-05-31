from langchain_openai import ChatOpenAI
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.schema import HumanMessage, AIMessage, SystemMessage, BaseMessage
from app.core.config import settings
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class LLMService:
    """Service for interacting with Language Models."""
    
    def __init__(self):
        self.model = None
        self.model_name = settings.DEFAULT_LLM_MODEL
    
    def initialize_model(self, streaming: bool = False):
        """Initialize the LLM model."""
        try:
            callback_manager = None
            if streaming:
                callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
            
            self.model = ChatOpenAI(
                model_name=self.model_name,
                temperature=0.7,
                callback_manager=callback_manager,
                streaming=streaming,
                verbose=True
            )
            logger.info(f"Initialized LLM model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM model: {str(e)}")
            raise
    
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
        if not self.model:
            self.initialize_model(streaming=streaming)
        
        try:
            # Convert messages to LangChain format
            langchain_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                langchain_messages.append(SystemMessage(content=system_prompt))
            
            # Add conversation messages
            for msg in messages:
                if msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["role"] == "assistant":
                    langchain_messages.append(AIMessage(content=msg["content"]))
                elif msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
            
            # Get response from model
            response = self.model.invoke(langchain_messages)
            
            return {
                "role": "assistant",
                "content": response.content,
                "model": self.model_name
            }
        except Exception as e:
            logger.error(f"Failed to get LLM response: {str(e)}")
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
        if not self.model:
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
            logger.error(f"Failed to generate RAG response: {str(e)}")
            raise


# Create a singleton instance
llm_service = LLMService()
