# Multi-Provider LLM Integration

This document describes the multi-provider LLM integration implemented in the Personal RAG Server. The implementation allows switching between different LLM providers (currently OpenAI and DeepSeek) with minimal changes to the application code.

## Architecture

The multi-provider LLM integration follows these design patterns:

1. **Abstract Base Class**: A base LLM service interface defines the contract that all LLM providers must implement
2. **Factory Pattern**: A factory creates the appropriate LLM service based on configuration
3. **Strategy Pattern**: Different LLM provider implementations can be swapped at runtime
4. **Singleton Pattern**: A single LLM service instance is used throughout the application

### Class Diagram

```
BaseLLMService (abstract)
    ↑
    |---- OpenAIService
    |---- DeepSeekService

LLMServiceFactory --creates--> BaseLLMService

ProviderConfig (abstract)
    ↑
    |---- OpenAIConfig
    |---- DeepSeekConfig

ProviderConfigFactory --creates--> ProviderConfig
```

## Implementation

The implementation consists of the following components:

### BaseLLMService

An abstract base class that defines the interface for all LLM services:

```python
class BaseLLMService(ABC):
    @abstractmethod
    def initialize_model(self, **kwargs):
        pass

    @abstractmethod
    def get_llm_response(self, messages, system_prompt=None, temperature=0.7, streaming=False):
        pass

    @abstractmethod
    def generate_with_rag(self, messages, context, system_prompt=None):
        pass
```

### Provider-Specific Implementations

#### OpenAIService

Implementation of the BaseLLMService for OpenAI:

```python
class OpenAIService(BaseLLMService):
    def __init__(self):
        self.client = None
        self.model_name = settings.DEFAULT_LLM_MODEL

    def initialize_model(self, **kwargs):
        # Initialize OpenAI client

    def get_llm_response(self, messages, system_prompt=None, temperature=0.7, streaming=False):
        # Get response from OpenAI

    def generate_with_rag(self, messages, context, system_prompt=None):
        # Generate RAG response with OpenAI
```

#### DeepSeekService

Implementation of the BaseLLMService for DeepSeek:

```python
class DeepSeekService(BaseLLMService):
    def __init__(self):
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model_name = settings.DEEPSEEK_MODEL
        self.philosophy_model_name = settings.DEEPSEEK_PHILOSOPHY_MODEL
        self.headers = None

    def initialize_model(self, **kwargs):
        # Initialize DeepSeek headers

    def get_llm_response(self, messages, system_prompt=None, temperature=0.7, streaming=False):
        # Get response from DeepSeek

    def generate_with_rag(self, messages, context, system_prompt=None):
        # Generate RAG response with DeepSeek
```

### Specialized Models for Different Question Types

The DeepSeek implementation includes logic to automatically detect question types and route them to the most appropriate model. For example, philosophical questions are automatically routed to the DeepSeek-V3-0324 model, which performs better on complex reasoning tasks.

#### Philosophical Question Detection

The service includes pattern matching to identify philosophical topics:

```python
def _is_philosophical_question(self, messages):
    # Get the last user message
    last_user_msg = None
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    # Define patterns for philosophical questions
    philosophical_patterns = [
        r'\b(meaning|purpose)\s+of\s+life',
        r'\b(ethics|moral|ethical|morality)',
        r'\b(consciousness|self-awareness)',
        r'\b(free\s+will|determinism)',
        r'\b(existence|existential)',
        # More patterns...
    ]

    # Check if the message contains any philosophical patterns
    for pattern in philosophical_patterns:
        if re.search(pattern, last_user_msg, re.IGNORECASE):
            return True

    return False
```

When a philosophical question is detected, the service automatically:

1. Switches to the specialized DeepSeek-V3-0324 model
2. Adjusts the temperature parameter for more coherent reasoning
3. Logs the model selection for monitoring and debugging

### LLMServiceFactory

A factory for creating LLM service instances:

```python
class LLMServiceFactory:
    @staticmethod
    def create_llm_service() -> BaseLLMService:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "openai":
            return OpenAIService()
        elif provider == "deepseek":
            return DeepSeekService()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

# Create a singleton instance
llm_service = get_default_llm_service()
```

### Provider Configuration

Provider-specific configuration is managed through the ProviderConfig classes:

```python
class ProviderConfig:
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    def get_config(self) -> Dict[str, Any]:
        raise NotImplementedError()

class OpenAIConfig(ProviderConfig):
    def get_config(self) -> Dict[str, Any]:
        return {
            "api_key": settings.OPENAI_API_KEY,
            "model": settings.DEFAULT_LLM_MODEL,
            # Other OpenAI-specific configuration
        }

class DeepSeekConfig(ProviderConfig):
    def get_config(self) -> Dict[str, Any]:
        return {
            "api_key": settings.DEEPSEEK_API_KEY,
            "api_url": settings.DEEPSEEK_API_URL,
            "model": settings.DEEPSEEK_MODEL,
            "philosophy_model": settings.DEEPSEEK_PHILOSOPHY_MODEL,
            # Other DeepSeek-specific configuration
        }
```

## Configuration

To configure the LLM provider, set the following in your environment variables or .env file:

```
# Common configuration
LLM_PROVIDER=openai  # or deepseek

# OpenAI configuration
OPENAI_API_KEY=your-openai-api-key
DEFAULT_LLM_MODEL=gpt-4o

# DeepSeek configuration
DEEPSEEK_API_KEY=your-deepseek-api-key
DEEPSEEK_API_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_PHILOSOPHY_MODEL=deepseek-v3-0324
```

## Usage

The multi-provider LLM service is used in the application through the singleton instance:

```python
from app.services.llm_service import llm_service

# Get a response from the default LLM provider
response = llm_service.get_llm_response(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)

# For philosophical questions, the DeepSeek service will automatically
# switch to the DeepSeek-V3-0324 model
philosophical_response = llm_service.get_llm_response(
    messages=[{"role": "user", "content": "What is the meaning of life?"}],
    temperature=0.7
)

# Generate a RAG response
rag_response = llm_service.generate_with_rag(
    messages=[{"role": "user", "content": "What is RAG?"}],
    context=["RAG stands for Retrieval Augmented Generation"],
    system_prompt="You are a helpful assistant."
)
```

## Adding New Providers

To add a new LLM provider:

1. Create a new class that implements the BaseLLMService interface
2. Add the provider configuration to the ProviderConfigFactory
3. Update the LLMServiceFactory to create instances of the new provider
4. Add the provider's configuration to the settings module

Example for a new provider:

```python
class NewProviderService(BaseLLMService):
    def initialize_model(self, **kwargs):
        # Implementation

    def get_llm_response(self, messages, system_prompt=None, temperature=0.7, streaming=False):
        # Implementation

    def generate_with_rag(self, messages, context, system_prompt=None):
        # Implementation

# Add to LLMServiceFactory
@staticmethod
def create_llm_service() -> BaseLLMService:
    provider = settings.LLM_PROVIDER.lower()

    if provider == "openai":
        return OpenAIService()
    elif provider == "deepseek":
        return DeepSeekService()
    elif provider == "new_provider":
        return NewProviderService()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
```

## Testing

Each LLM provider implementation includes unit tests to ensure correct functionality:

-   Testing the initialization of the LLM model
-   Testing the get_llm_response method
-   Testing the generate_with_rag method
-   Testing the factory for creating the correct implementation based on configuration

Tests use mocking to simulate the external LLM API responses.
