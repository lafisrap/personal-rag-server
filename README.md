# Personal RAG Server

A fast and secure REST API server for a personal Retrieval Augmented Generation (RAG) system, using Pinecone as the vector database and supporting multiple LLM providers.

## Features

-   **FastAPI REST API**: Fast, modern API with automatic OpenAPI documentation
-   **Multi-Provider LLM Integration**: Support for both OpenAI and DeepSeek as LLM providers
-   **Specialized Domain Models**: Automatic routing to specialized models for philosophical questions
-   **Pinecone Vector Database**: Efficient semantic search with metadata filtering
-   **Async Architecture**: Fully asynchronous design for high performance
-   **Type Safety**: Comprehensive type annotations with Pydantic
-   **RAG Capabilities**: Retrieval-augmented generation for improved responses
-   **Modular Design**: Clean separation of concerns with service-oriented architecture

## LLM Provider Integration

The system supports multiple LLM providers through an abstract interface and factory pattern. Currently supported providers:

-   **OpenAI**: Using the OpenAI API with models like GPT-4o
-   **DeepSeek**: Using the DeepSeek API with multiple models:
    -   **DeepSeek-Chat**: General-purpose model for everyday questions
    -   **DeepSeek-V3-0324**: Specialized model for philosophical questions with enhanced reasoning capabilities

See [Multi-Provider LLM Integration](docs/multi_provider_llm.md) for detailed documentation.

## Installation

1. Clone the repository:

    ```
    git clone https://github.com/yourusername/personal-rag-server.git
    cd personal-rag-server
    ```

2. Create a virtual environment and install dependencies:

    ```
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. Create a `.env` file with your configuration:

    ```
    # API Settings
    API_V1_STR=/api/v1
    PROJECT_NAME="Personal RAG Server"

    # MongoDB Settings
    MONGODB_URI=mongodb://localhost:27017
    MONGODB_DB_NAME=rag_server

    # Vector DB Settings (Pinecone)
    VECTOR_DB_TYPE=pinecone
    PINECONE_API_KEY=your-pinecone-api-key
    PINECONE_ENVIRONMENT=your-pinecone-environment
    PINECONE_INDEX_NAME=your-pinecone-index

    # LLM Provider Settings
    LLM_PROVIDER=deepseek  # or openai

    # OpenAI Settings (if using OpenAI)
    OPENAI_API_KEY=your-openai-api-key
    DEFAULT_LLM_MODEL=gpt-4o

    # DeepSeek Settings (if using DeepSeek)
    DEEPSEEK_API_KEY=your-deepseek-api-key
    DEEPSEEK_API_URL=https://api.deepseek.com
    DEEPSEEK_MODEL=deepseek-chat
    DEEPSEEK_PHILOSOPHY_MODEL=deepseek-v3-0324

    # Embeddings Settings
    EMBEDDINGS_MODEL=text-embedding-3-large
    ```

## Usage

1. Start the API server:

    ```
    uvicorn app.main:app --reload
    ```

2. Access the API documentation at `http://localhost:8000/docs`

3. Use the API endpoints to interact with the RAG system:
    - Create threads and assistants
    - Send messages
    - Manage categories and documents
    - Perform vector searches

## API Endpoints

-   **Assistants**: Create and manage AI assistants
-   **Threads**: Create conversation threads
-   **Messages**: Send and receive messages in threads
-   **Categories**: Organize documents into categories (coming soon)
-   **Files**: Upload and manage documents (coming soon)
-   **Tags**: Add metadata tags to documents (coming soon)

## Architecture

The application follows a clean architecture with proper separation of concerns:

-   **API Layer**: FastAPI routes and endpoints
-   **Service Layer**: Business logic for LLM interactions, RAG, etc.
-   **Database Layer**: MongoDB for metadata, Pinecone for vector storage
-   **Model Layer**: Pydantic models for data validation

## Development

### Running Tests

```
python -m pytest
```

### Code Style

The project follows PEP 8 guidelines with some modifications. Use tools like `black` and `flake8` for formatting and linting.

## License

MIT

## Credits

-   FastAPI: https://fastapi.tiangolo.com/
-   Pinecone: https://www.pinecone.io/
-   OpenAI: https://openai.com/
-   DeepSeek: https://deepseek.com/
