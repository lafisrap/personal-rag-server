from app.core.config import settings
from app.services.llm_service_base import BaseLLMService
from app.services.openai_service import OpenAIService
from app.services.deepseek_service import DeepSeekService
import logging

logger = logging.getLogger(__name__)

class LLMServiceFactory:
    """Factory for creating LLM service instances."""
    
    @staticmethod
    def create_llm_service() -> BaseLLMService:
        """
        Create an LLM service based on the configured provider.
        
        Returns:
            An instance of a BaseLLMService implementation
        """
        provider = settings.LLM_PROVIDER.lower()
        
        logger.info(f"Creating LLM service for provider: {provider}")
        
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            return OpenAIService()
        elif provider == "deepseek":
            if not settings.DEEPSEEK_API_KEY:
                raise ValueError("DeepSeek API key not configured")
            return DeepSeekService()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

# Create a default service based on configuration
def get_default_llm_service() -> BaseLLMService:
    """
    Get the default LLM service based on configuration.
    
    Returns:
        An instance of a BaseLLMService implementation
    """
    try:
        return LLMServiceFactory.create_llm_service()
    except Exception as e:
        logger.error(f"Failed to create default LLM service: {str(e)}")
        raise

# Create a singleton instance
llm_service = get_default_llm_service() 