import requests
import json
from app.core.config import settings
import logging
import re
import os
from typing import List, Dict, Any, Optional
from app.services.llm_service_base import BaseLLMService

logger = logging.getLogger(__name__)

class DeepSeekService(BaseLLMService):
    """Service for interacting with DeepSeek Language Models."""
    
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model_name = settings.DEEPSEEK_MODEL
        self.philosophy_model_name = os.environ.get("DEEPSEEK_PHILOSOPHY_MODEL", "deepseek-reasoner")
        self.headers = None
        
        # If philosophy model isn't set, default to reasoner
        if self.philosophy_model_name == "deepseek-v3-0324":
            self.philosophy_model_name = "deepseek-reasoner"
            logger.info(f"Updated philosophy model to {self.philosophy_model_name}")
    
    def initialize_model(self, **kwargs):
        """Initialize the DeepSeek client."""
        try:
            model_name = kwargs.get("model_name", self.model_name)
            
            self.headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            logger.info(f"Initialized DeepSeek client for model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize DeepSeek client: {str(e)}")
            raise
    
    def _is_philosophical_question(self, messages: List[Dict[str, str]]) -> bool:
        """
        Determine if the question is philosophical in nature.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            
        Returns:
            Boolean indicating if the question is philosophical
        """
        # Get the last user message
        last_user_msg = None
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break
        
        if not last_user_msg:
            return False
        
        # Define patterns for philosophical questions
        philosophical_patterns = [
            r'\b(meaning|purpose)\s+of\s+life',
            r'\b(ethics|moral|ethical|morality)',
            r'\b(consciousness|self-awareness)',
            r'\b(free\s+will|determinism)',
            r'\b(existence|existential)',
            r'\b(epistemology|knowledge|knowing)',
            r'\b(metaphysics|reality|nature\s+of\s+reality)',
            r'\b(ontology|being)',
            r'\b(good\s+life|happiness|eudaimonia)',
            r'\b(aesthetics|beauty|art)',
            r'\b(justice|fairness)',
            r'\b(truth|falsehood)',
            r'\b(paradox|contradiction)',
            r'\bphilosophy',
            r'\b(aristotle|plato|socrates|kant|nietzsche|hume|descartes|heidegger|sartre|wittgenstein)'
        ]
        
        # Check if the message contains any philosophical patterns
        for pattern in philosophical_patterns:
            if re.search(pattern, last_user_msg, re.IGNORECASE):
                logger.info(f"Detected philosophical question: {last_user_msg[:100]}...")
                return True
        
        return False
    
    def get_llm_response(self, 
                         messages: List[Dict[str, str]], 
                         system_prompt: Optional[str] = None,
                         temperature: float = 0.7,
                         streaming: bool = False) -> Dict[str, Any]:
        """
        Get a response from the DeepSeek model.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt to override default
            temperature: Temperature parameter for response generation
            streaming: Whether to stream the response
            
        Returns:
            Dictionary with LLM response and metadata
        """
        if not self.headers:
            self.initialize_model()
        
        try:
            # Check if this is a philosophical question and use the appropriate model
            is_philosophical = self._is_philosophical_question(messages)
            model_to_use = self.philosophy_model_name if is_philosophical else self.model_name
            
            if is_philosophical:
                logger.info(f"Using philosophy-specific model: {model_to_use}")
                
                # If it's a philosophical question, adjust the temperature for better reasoning
                # Use a slightly lower temperature for more coherent philosophical responses
                temperature = min(temperature, 0.5)
            
            # Prepare the messages for DeepSeek format
            deepseek_messages = []
            
            # Add system prompt if provided
            if system_prompt:
                deepseek_messages.append({"role": "system", "content": system_prompt})
            
            # Add conversation messages
            for msg in messages:
                deepseek_messages.append(msg)
            
            # Prepare the request payload
            payload = {
                "model": model_to_use,
                "messages": deepseek_messages,
                "temperature": temperature,
                "stream": streaming
            }
            
            # Get response from model
            if streaming:
                # In streaming mode, we would handle this differently in the actual API endpoint
                # For compatibility with our interface, we're collecting all chunks here
                response = requests.post(
                    f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json=payload,
                    stream=True
                )
                response.raise_for_status()
                
                content = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            if line == 'data: [DONE]':
                                break
                            try:
                                chunk = json.loads(line[6:])  # Remove 'data: ' prefix
                                if chunk.get('choices') and chunk['choices'][0].get('delta') and chunk['choices'][0]['delta'].get('content'):
                                    content += chunk['choices'][0]['delta']['content']
                            except json.JSONDecodeError:
                                logger.warning(f"Could not parse streaming response: {line}")
                
                return {
                    "role": "assistant",
                    "content": content,
                    "model": model_to_use
                }
            else:
                response = requests.post(
                    f"{self.api_url}/chat/completions",
                    headers=self.headers,
                    json=payload
                )
                response.raise_for_status()
                response_data = response.json()
                
                return {
                    "role": "assistant",
                    "content": response_data['choices'][0]['message']['content'],
                    "model": model_to_use
                }
                
        except Exception as e:
            logger.error(f"Failed to get DeepSeek response: {str(e)}")
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
        if not self.headers:
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
            logger.error(f"Failed to generate DeepSeek RAG response: {str(e)}")
            raise 