# Personal RAG Server

## Project Overview

The Personal RAG Server is a specialized Retrieval Augmented Generation system designed for private and efficient knowledge management, with particular focus on philosophical texts in German and English. It provides secure REST API access to interact with your document collection, enhanced with advanced semantic search capabilities.

### Key Features

-   **Hybrid Search Technology**: Combines dense and sparse vector representations for superior retrieval performance
-   **German Language Optimization**: Specialized embedding models for German philosophical texts
-   **Philosophical Question Detection**: Automatically routes philosophical queries to specialized models
-   **Category-Based Organization**: Organizes documents by philosophical worldviews and categories
-   **Document Management**: Comprehensive tools for uploading, updating, and managing documents
-   **Advanced Metadata**: Enhanced document metadata with philosophical concept tagging
-   **Command-Line Interface**: Unified CLI for all RAG management operations
-   **Diagnostic Tools**: Comprehensive system diagnostics and query performance analysis

### Core Technologies

-   **Vector Database**: Pinecone for efficient semantic search
-   **Embedding Models**: Specialized models for German philosophical texts
-   **LLM Integration**: DeepSeek for high-quality response generation
-   **API Framework**: FastAPI for modern, async Python REST API
-   **Storage**: MongoDB for document metadata and system data

## System Architecture

The Personal RAG Server follows a modular architecture with clear separation of concerns to ensure maintainability and extensibility.

### Components

1. **API Layer**: FastAPI endpoints handle HTTP requests and provide OpenAPI documentation
2. **Service Layer**: Core business logic components include:

    - **RAG Service**: Orchestrates the RAG pipeline
    - **Embedding Service**: Generates vector embeddings using specialized models
    - **LLM Service**: Interfaces with DeepSeek for response generation
    - **Vector Store Manager**: Handles Pinecone vector database operations
    - **File Processor**: Processes and chunks documents
    - **Knowledge Base Scanner**: Scans and catalogs documents

3. **Database Layer**:

    - **MongoDB**: Stores metadata, conversations, and system data
    - **Pinecone**: Vector database for semantic search with hybrid vector support

4. **CLI Layer**:
    - **RAG CLI**: Command-line interface for system management
    - **Diagnostic Tools**: Query testing and system analysis tools

### Data Flow

1. **Document Processing**:

    - Documents are uploaded via CLI or API
    - Text is processed, chunked, and enhanced with metadata
    - Both dense and sparse vectors are generated
    - Vectors and metadata are stored in Pinecone

2. **Query Processing**:
    - User query is analyzed for philosophical content
    - Query is converted to dense and sparse vectors
    - Hybrid search retrieves relevant document chunks
    - Retrieved context is passed to LLM with the query
    - LLM generates response based on context and query

### Directory Structure

```
app/
├── api/                # REST API endpoints
├── core/               # Core configuration and utilities
├── db/                 # Database connections and operations
├── models/             # Pydantic data models
├── services/           # Business logic services
└── utils/              # Utility functions

scripts/
├── data_import/        # Data import utilities
├── phase2/             # Hybrid search implementation
├── rag-cli/            # CLI tools for RAG management
└── testing/            # Testing and diagnostic tools
```

## Installation & Setup

### Requirements

-   **Python**: 3.9+ (3.11 recommended)
-   **MongoDB**: Running instance (local or remote)
-   **Pinecone**: Account with API key
-   **DeepSeek**: API key for LLM access
-   **Hardware**: Apple Silicon Mac recommended for optimized embedding generation

### Installation Steps

1. Clone the repository:

    ```
    git clone https://github.com/yourusername/personal-rag-server.git
    cd personal-rag-server
    ```

2. Install dependencies:

    ```
    pip install -r requirements.txt
    ```

3. Create a `.env` file with your configuration:

    ```
    python fix_env.py
    ```

4. Edit the `.env` file with your API keys and settings.

### Configuration

Create a `.env` file in the project root with the following settings:

```
# MongoDB Settings
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=rag_server

# Pinecone Settings
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_ENVIRONMENT=your_pinecone_region
PINECONE_INDEX_NAME=rag-server-hybrid

# DeepSeek Settings
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_PHILOSOPHY_MODEL=deepseek-reasoner

# Embedding Service Settings
LOCAL_EMBEDDING_SERVICE_URL=http://localhost:8001
EMBEDDINGS_DIMENSION=1024
EMBEDDINGS_MODEL=multilingual-e5-large
```

### Starting the Server

1. Start the local embeddings service (if using):

    ```
    cd personal-embeddings-service
    docker-compose up -d
    ```

2. Start the FastAPI server:

    ```
    uvicorn app.main:app --reload
    ```

3. Run the integration tests to verify setup:

    ```
    python -m scripts.testing.integration_tests
    ```

## Core Functionality

### RAG CLI Usage

The RAG CLI provides a unified interface for managing the RAG system. All commands are run using the `scripts/rag-cli.sh` script.

```bash
# Get general help
./scripts/rag-cli.sh --help

# Get help for a specific command group
./scripts/rag-cli.sh kb --help
```

### Document Management

#### Uploading Documents

Upload documents from a directory to the vector database:

```bash
./scripts/rag-cli.sh kb upload --source /path/to/knowledge_base
```

You can specify categories to upload:

```bash
./scripts/rag-cli.sh kb upload --source /path/to/knowledge_base --categories Materialismus,Idealismus
```

#### Updating Documents

Update existing documents in the database:

```bash
./scripts/rag-cli.sh kb update --source /path/to/knowledge_base --categories Materialismus --delete-existing
```

#### Deleting Documents

Delete documents by category:

```bash
./scripts/rag-cli.sh kb delete --categories Materialismus,Idealismus
```

#### Viewing Statistics

Get statistics about the indexed content:

```bash
./scripts/rag-cli.sh kb stats
```

View statistics for specific categories:

```bash
./scripts/rag-cli.sh kb stats --categories Materialismus,Idealismus
```

### Querying the System

You can query the system through the API or test queries via the CLI:

```bash
./scripts/rag-cli.sh search query "What is the concept of consciousness?" --category Materialismus
```

Search without category filter:

```bash
./scripts/rag-cli.sh search query "Compare consciousness in materialism and idealism"
```

### Testing the System

Run integration tests to verify system functionality:

```bash
python -m scripts.testing.integration_tests --verbose
```

Test a specific query:

```bash
python -m scripts.testing.integration_tests --query "What is the meaning of life?"
```

Test if a question is philosophical:

```bash
python -m scripts.testing.integration_tests --test-philosophical "Does free will exist?"
```

## Advanced Features

### Hybrid Search Capabilities

The system implements hybrid search combining both dense and sparse vector representations:

#### Dense Vectors (Semantic Search)

-   Capture meaning and context regardless of exact word usage
-   Use specialized German embedding models for better understanding of philosophical texts
-   Handle nuanced concepts and relationships between ideas

#### Sparse Vectors (Keyword Search)

-   Capture exact word matches and lexical information
-   Implement BM25 algorithm optimized for German philosophical texts
-   Address variations in number formats (e.g., "12" vs "zwölf")

#### Configurable Hybrid Search

```bash
# Use hybrid search with custom alpha value (dense vs sparse weighting)
./scripts/rag-cli.sh search query "Welches sind die 12 Weltanschauungen?" --alpha 0.6
```

The alpha parameter controls the weight balance between dense and sparse vectors:

-   `alpha=1.0`: 100% dense vectors (pure semantic search)
-   `alpha=0.0`: 100% sparse vectors (pure lexical search)
-   `alpha=0.5`: Equal weight to both (default)

### Philosophical Question Detection

The system automatically detects philosophical questions and routes them to specialized LLM models:

```bash
# Test if a question is philosophical
./scripts/rag-cli.sh diagnostics test-philosophical "What is the meaning of life?"
```

Philosophical detection is based on:

-   Content analysis of the question
-   Presence of philosophical terms and concepts
-   Question structure and complexity

When a philosophical question is detected, the system uses the DeepSeek Reasoner model, which is optimized for philosophical reasoning.

### Metadata Enhancement

Documents are automatically enhanced with rich metadata to improve search and filtering:

#### Philosophical Concept Tagging

-   Automatic detection of philosophical concepts mentioned in documents
-   Tagging with standardized terminology
-   Cross-referencing between related concepts

#### Author Attribution

-   Automatic extraction of author information from filenames
-   Linking to author metadata and background information
-   Grouping works by author

#### Number Format Handling

-   Detection and normalization of number formats (digits and spelled-out)
-   Creation of search-optimized fields for both formats
-   Support for German number variations

### Category Management

Organize your document collection by philosophical worldviews and other categories:

```bash
# List all categories
./scripts/rag-cli.sh kb list-categories

# View documents in a category
./scripts/rag-cli.sh kb list-documents --category Idealismus
```

Categories can be nested and documents can belong to multiple categories, enabling flexible organization of complex philosophical texts.

## Troubleshooting

### Common Issues and Solutions

#### Document Not Found in Search Results

If a document isn't appearing in search results:

```bash
# Check if the document exists in the database
./scripts/rag-cli.sh diagnostics check-document --document-id "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]" --expected-category "Realismus"
```

**Solutions**:

-   Verify the document was uploaded with correct metadata
-   Try searching with alternative query formulations
-   Adjust the alpha parameter for hybrid search
-   Use the improved document check command:

```bash
./scripts/rag-cli.sh diagnostics check-document-improved --document-id "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]" --expected-category "Realismus" --query-match
```

#### Number Format Issues

If queries with different number formats (e.g., "12" vs "zwölf") yield different results:

**Solutions**:

-   Ensure hybrid search is enabled (alpha between 0.3-0.7)
-   Run the optimization tool to find optimal alpha:

```bash
python -m scripts.phase2.phase2_optimization_tuning --vectorizer bm25_vectorizer.pkl --output-dir optimization_results
```

#### Configuration Problems

If you encounter configuration issues:

```bash
# Run the integration tests to verify configuration
python -m scripts.testing.integration_tests
```

**Solutions**:

-   Verify environment variables in .env file
-   Check API keys for Pinecone and DeepSeek
-   Ensure the Pinecone index has the correct dimension (1024)

### Diagnostic Tools

The system includes comprehensive diagnostic tools:

#### RAG Diagnosis

Run a full diagnostic on the RAG system:

```bash
./scripts/rag-cli.sh diagnostics diagnose-retrieval
```

This checks:

-   Document existence and retrieval
-   Query performance with variations
-   Category filter effectiveness
-   LLM response quality

#### Performance Analysis

Analyze search performance with different configurations:

```bash
python -m scripts.phase2.TODO_phase2_hybrid_test --vectorizer bm25_vectorizer.pkl --category Realismus_Test --output evaluation_report.md
```

### Performance Optimization Tips

1. **Adjust Hybrid Search Parameters**:

    - For philosophical terminology: alpha = 0.4
    - For general questions: alpha = 0.7
    - For queries with numbers: alpha = 0.5

2. **Optimize Chunk Size**:

    - Smaller chunks (500-800 chars) for precise retrieval
    - Larger chunks (1000-1500 chars) for more context
    - Adjust overlap (200-300 chars) to maintain context

3. **Batch Processing**:
    - Use larger batch sizes for document uploads
    - Process large collections with the parallel option:

```bash
./scripts/rag-cli.sh kb upload --source /path/to/knowledge_base --parallel --workers 4
```

4. **Pinecone Optimization**:
    - Increase `top_k` parameter for recall-focused applications
    - Use namespace-based organization for cleaner separation
    - Implement metadata filtering to narrow results

## Reference

### Command Reference

#### Knowledge Base Management Commands

| Command              | Description                           | Example                                                                         |
| -------------------- | ------------------------------------- | ------------------------------------------------------------------------------- |
| `kb upload`          | Upload documents to vector store      | `./scripts/rag-cli.sh kb upload --source /path/to/docs`                         |
| `kb update`          | Update existing documents             | `./scripts/rag-cli.sh kb update --source /path/to/docs --categories Philosophy` |
| `kb delete`          | Delete documents by category          | `./scripts/rag-cli.sh kb delete --categories Materialismus`                     |
| `kb stats`           | View statistics about indexed content | `./scripts/rag-cli.sh kb stats`                                                 |
| `kb list-categories` | List available categories             | `./scripts/rag-cli.sh kb list-categories`                                       |
| `kb list-documents`  | List documents in a category          | `./scripts/rag-cli.sh kb list-documents --category Idealismus`                  |

#### Search Commands

| Command           | Description                | Example                                                           |
| ----------------- | -------------------------- | ----------------------------------------------------------------- |
| `search query`    | Search for documents       | `./scripts/rag-cli.sh search query "What is consciousness?"`      |
| `search optimize` | Optimize search parameters | `./scripts/rag-cli.sh search optimize --query-type philosophical` |

#### Diagnostic Commands

| Command                          | Description                  | Example                                                                  |
| -------------------------------- | ---------------------------- | ------------------------------------------------------------------------ |
| `diagnostics diagnose-retrieval` | Run full system diagnosis    | `./scripts/rag-cli.sh diagnostics diagnose-retrieval`                    |
| `diagnostics check-document`     | Check document existence     | `./scripts/rag-cli.sh diagnostics check-document --document-id "doc_id"` |
| `diagnostics test-philosophical` | Test philosophical detection | `./scripts/rag-cli.sh diagnostics test-philosophical "What is truth?"`   |

### API Endpoints

#### RAG Endpoints

| Endpoint                              | Method | Description                       |
| ------------------------------------- | ------ | --------------------------------- |
| `/api/v1/rag/query`                   | POST   | Generate RAG response for a query |
| `/api/v1/rag/search`                  | POST   | Search for documents              |
| `/api/v1/rag/documents`               | POST   | Add documents to the system       |
| `/api/v1/rag/documents/{document_id}` | DELETE | Delete a document                 |

#### Assistants API (OpenAI-compatible)

| Endpoint                               | Method         | Description                 |
| -------------------------------------- | -------------- | --------------------------- |
| `/api/v1/assistants`                   | GET/POST       | List/create assistants      |
| `/api/v1/assistants/{assistant_id}`    | GET/PUT/DELETE | Get/update/delete assistant |
| `/api/v1/threads`                      | GET/POST       | List/create threads         |
| `/api/v1/threads/{thread_id}/messages` | GET/POST       | List/create messages        |
| `/api/v1/threads/{thread_id}/runs`     | POST           | Run assistant on thread     |

#### System Endpoints

| Endpoint             | Method | Description              |
| -------------------- | ------ | ------------------------ |
| `/api/v1/health`     | GET    | System health check      |
| `/api/v1/auth/token` | POST   | Get authentication token |
| `/docs`              | GET    | OpenAPI documentation    |

### Configuration Options

#### Environment Variables

| Variable                      | Description                     | Default                       |
| ----------------------------- | ------------------------------- | ----------------------------- |
| `MONGODB_URL`                 | MongoDB connection string       | `mongodb://localhost:27017`   |
| `MONGODB_DB_NAME`             | MongoDB database name           | `rag_server`                  |
| `PINECONE_API_KEY`            | Pinecone API key                | -                             |
| `PINECONE_ENVIRONMENT`        | Pinecone environment            | -                             |
| `PINECONE_INDEX_NAME`         | Pinecone index name             | `rag-server-hybrid`           |
| `DEEPSEEK_API_KEY`            | DeepSeek API key                | -                             |
| `DEEPSEEK_API_URL`            | DeepSeek API URL                | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL`              | Default DeepSeek model          | `deepseek-chat`               |
| `DEEPSEEK_PHILOSOPHY_MODEL`   | Model for philosophical queries | `deepseek-reasoner`           |
| `LOCAL_EMBEDDING_SERVICE_URL` | Local embedding service URL     | `http://localhost:8001`       |
| `EMBEDDINGS_DIMENSION`        | Embedding vector dimension      | `1024`                        |
| `EMBEDDINGS_MODEL`            | Embedding model name            | `multilingual-e5-large`       |

#### Hybrid Search Parameters

| Parameter       | Description                   | Recommended Values       |
| --------------- | ----------------------------- | ------------------------ |
| `alpha`         | Dense vs sparse weight        | 0.3-0.7 (default: 0.5)   |
| `top_k`         | Number of results to retrieve | 10-30 (default: 15)      |
| `chunk_size`    | Document chunk size           | 500-1500 (default: 1000) |
| `chunk_overlap` | Overlap between chunks        | 100-300 (default: 200)   |
