from app.core.config import settings
from typing import Dict, Any, Optional
import os
import logging

logger = logging.getLogger(__name__)

class ProviderConfig:
    """Base class for provider configuration."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get configuration for the provider.
        
        Returns:
            Dictionary with provider configuration
        """
        raise NotImplementedError("Provider must implement get_config method")

class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider."""
    
    def __init__(self):
        super().__init__("openai")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get configuration for OpenAI.
        
        Returns:
            Dictionary with OpenAI configuration
        """
        return {
            "api_key": settings.OPENAI_API_KEY,
            "model": settings.DEFAULT_LLM_MODEL,
            "max_tokens": 4096,
            "supports_streaming": True,
            "supports_function_calling": True
        }

class DeepSeekConfig(ProviderConfig):
    """Configuration for DeepSeek provider."""
    
    def __init__(self):
        super().__init__("deepseek")
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get configuration for DeepSeek.
        
        Returns:
            Dictionary with DeepSeek configuration
        """
        return {
            "api_key": settings.DEEPSEEK_API_KEY,
            "api_url": settings.DEEPSEEK_API_URL,
            "model": settings.DEEPSEEK_MODEL,
            "philosophy_model": settings.DEEPSEEK_PHILOSOPHY_MODEL,
            "max_tokens": 4096,
            "supports_streaming": True,
            "supports_function_calling": True,
            "specialized_models": {
                "philosophy": settings.DEEPSEEK_PHILOSOPHY_MODEL
            }
        }

class ProviderConfigFactory:
    """Factory for creating provider configurations."""
    
    @staticmethod
    def create_provider_config(provider: str) -> ProviderConfig:
        """
        Create a provider configuration based on the specified provider.
        
        Args:
            provider: The name of the provider
            
        Returns:
            A ProviderConfig instance
            
        Raises:
            ValueError: If the provider is not supported
        """
        provider = provider.lower()
        
        if provider == "openai":
            return OpenAIConfig()
        elif provider == "deepseek":
            return DeepSeekConfig()
        else:
            raise ValueError(f"Unsupported provider: {provider}")
    
    @staticmethod
    def get_default_provider_config() -> ProviderConfig:
        """
        Get the default provider configuration based on the settings.
        
        Returns:
            A ProviderConfig instance
            
        Raises:
            ValueError: If the default provider is not supported
        """
        provider = settings.LLM_PROVIDER.lower()
        return ProviderConfigFactory.create_provider_config(provider)

def validate_provider_config(provider: str) -> bool:
    """
    Validate that the configuration for a provider is valid.
    
    Args:
        provider: The name of the provider
        
    Returns:
        True if configuration is valid, False otherwise
    """
    try:
        provider = provider.lower()
        
        if provider == "openai":
            return bool(settings.OPENAI_API_KEY)
        elif provider == "deepseek":
            return bool(settings.DEEPSEEK_API_KEY and settings.DEEPSEEK_API_URL)
        else:
            return False
    except Exception as e:
        logger.error(f"Error validating provider config for {provider}: {str(e)}")
        return False 