# Embeddings Service Plan: Self-Hosted multilingual-e5-large (Fresh Start)

## Overview

This document outlines the implementation strategy for self-hosted Microsoft multilingual-e5-large embeddings in the Personal RAG Server. Since this is a fresh start with no existing data, we can implement a clean, optimized solution without migration complexity.

## Current State Analysis

**Starting Fresh:**

-   No existing data to migrate
-   Can implement optimal architecture from the start
-   No need for hybrid approaches or fallback mechanisms
-   Clean implementation without legacy constraints

**Cost Benefits:**

-   Zero ongoing embedding costs vs OpenAI API fees
-   One-time setup cost only
-   Full control over embedding generation

## Proposed Solution: Clean Architecture

**Recommendation: Separate Service Approach**

Create a standalone embedding service optimized for multilingual-e5-large from the start:

1. **Simplicity**: No migration complexity
2. **Performance**: Optimized for single embedding model
3. **Cost**: Zero operational embedding costs
4. **Scalability**: Can serve multiple projects
5. **Maintainability**: Clean, focused service

## Technical Implementation Plan

### Phase 1: Local Embedding Service Setup

#### 1.1 Create Separate Project Structure

```
personal-embeddings-service/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── app/
│   ├── main.py
│   ├── config.py
│   ├── models/
│   │   └── embedding_model.py
│   ├── services/
│   │   ├── embedding_service.py
│   │   └── batch_service.py
│   └── api/
│       ├── endpoints/
│       │   ├── embeddings.py
│       │   └── health.py
│       └── router.py
├── tests/
└── scripts/
    ├── download_model.py
    └── benchmark.py
```

#### 1.2 Model Specifications

-   **Model**: `intfloat/multilingual-e5-large`
-   **Dimensions**: 1024 (consistent throughout)
-   **Max Sequence Length**: 512 tokens
-   **Framework**: Sentence Transformers
-   **Memory**: ~2.5GB VRAM/RAM

#### 1.3 Hardware Requirements

**Minimum:**

-   CPU: 4+ cores
-   RAM: 8GB
-   Storage: 10GB free space

**Recommended:**

-   GPU: RTX 3060 or better (8GB+ VRAM)
-   CPU: 8+ cores
-   RAM: 16GB
-   SSD storage

### Phase 2: Pinecone Configuration (Clean Setup)

#### 2.1 Single Index Configuration

```python
# Clean index configuration for e5-large
index_config = {
    "name": "rag-server-e5-large",
    "dimension": 1024,
    "metric": "cosine",
    "spec": ServerlessSpec(
        cloud="aws",
        region="us-west-2"
    )
}
```

#### 2.2 Simplified Vector Database

```python
# app/db/vector_db.py - Clean implementation
class VectorDatabase:
    def __init__(self):
        self.initialized = False
        self.pc = None
        self.index = None
        self.dimension = 1024  # Fixed for e5-large

    def init_pinecone(self):
        """Initialize Pinecone with e5-large dimensions."""
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)

            existing_indexes = self.pc.list_indexes().names()

            if settings.PINECONE_INDEX_NAME not in existing_indexes:
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=1024,  # e5-large dimension
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT or "us-west-2"
                    )
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")

            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            self.initialized = True
            logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise
```

### Phase 3: Simplified Integration

#### 3.1 Clean Embedding Service

```python
# app/services/embedding_service.py - Simplified for local only
import httpx
import logging
from typing import List, Union
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using local e5-large model."""

    def __init__(self):
        self.local_service_url = settings.LOCAL_EMBEDDING_SERVICE_URL
        self.dimension = 1024  # e5-large dimension
        self.model_name = "multilingual-e5-large"

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    async def get_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings using local e5-large service.

        Args:
            texts: A single text or list of texts to generate embeddings for

        Returns:
            Numpy array of embeddings
        """
        try:
            # Handle single text input
            if isinstance(texts, str):
                input_texts = [texts]
                single_input = True
            else:
                input_texts = texts
                single_input = False

            # Call local embedding service
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.local_service_url}/api/v1/embeddings",
                    json={"texts": input_texts}
                )
                response.raise_for_status()

                result = response.json()
                embeddings = np.array(result["embeddings"])

                # Return single embedding or array of embeddings
                if single_input:
                    return embeddings[0]
                return embeddings

        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise

    async def similarity_search(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Perform similarity search using local embeddings."""
        try:
            query_embedding = await self.get_embeddings(query)
            doc_embeddings = await self.get_embeddings(documents)

            # Calculate cosine similarity
            similarities = np.dot(doc_embeddings, query_embedding) / (
                np.linalg.norm(doc_embeddings, axis=1) * np.linalg.norm(query_embedding)
            )

            # Get top_k indices
            top_indices = np.argsort(similarities)[::-1][:top_k]

            # Format results
            results = []
            for idx in top_indices:
                results.append({
                    "index": int(idx),
                    "document": documents[idx],
                    "score": float(similarities[idx])
                })

            return results
        except Exception as e:
            logger.error(f"Failed to perform similarity search: {str(e)}")
            raise

# Create a singleton instance
embedding_service = EmbeddingService()
```

#### 3.2 Simplified Configuration

```python
# app/core/config.py - Clean configuration
class Settings(BaseSettings):
    # ... existing settings ...

    # Local Embedding Service (only option)
    LOCAL_EMBEDDING_SERVICE_URL: str = os.getenv("LOCAL_EMBEDDING_SERVICE_URL", "http://localhost:8001")

    # Fixed dimensions for e5-large
    EMBEDDINGS_DIMENSION: int = 1024
    EMBEDDINGS_MODEL: str = "multilingual-e5-large"

    # Pinecone Settings
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "rag-server-e5-large")
```

### Phase 4: Local Embedding Service Implementation

#### 4.1 Core Service (FastAPI)

```python
# personal-embeddings-service/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.services.embedding_service import embedding_service
from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await embedding_service.load_model()
    yield
    # Shutdown - cleanup if needed

app = FastAPI(
    title="Personal Embeddings Service",
    description="Self-hosted multilingual-e5-large embedding service",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Personal Embeddings Service", "model": "multilingual-e5-large"}
```

#### 4.2 Optimized Embedding Service

```python
# personal-embeddings-service/app/services/embedding_service.py
import torch
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

class LocalEmbeddingService:
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def load_model(self):
        """Load the e5-large model asynchronously."""
        def _load_model():
            model = SentenceTransformer('intfloat/multilingual-e5-large')
            model.to(self.device)
            # Optimize for inference
            if self.device == "cuda":
                model.half()  # Use float16 for GPU
            return model

        logger.info(f"Loading multilingual-e5-large model on {self.device}")
        self.model = await asyncio.get_event_loop().run_in_executor(
            self.executor, _load_model
        )
        logger.info("Model loaded successfully")

    async def encode_texts(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Encode texts to embeddings asynchronously."""
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")

        def _encode(texts_list):
            # Add e5 instruction prefix for better performance
            prefixed_texts = [f"passage: {text}" for text in texts_list]

            embeddings = self.model.encode(
                prefixed_texts,
                convert_to_numpy=True,
                normalize_embeddings=True,
                batch_size=32,
                show_progress_bar=False
            )
            return embeddings

        if isinstance(texts, str):
            texts_list = [texts]
        else:
            texts_list = texts

        # Run encoding in thread pool to avoid blocking
        embeddings = await asyncio.get_event_loop().run_in_executor(
            self.executor, _encode, texts_list
        )

        return embeddings

# Singleton instance
embedding_service = LocalEmbeddingService()
```

#### 4.3 Clean API Endpoints

```python
# personal-embeddings-service/app/api/endpoints/embeddings.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Union
import time
from app.services.embedding_service import embedding_service

router = APIRouter()

class EmbeddingRequest(BaseModel):
    texts: Union[str, List[str]] = Field(..., description="Text or list of texts to embed")

class EmbeddingResponse(BaseModel):
    embeddings: List[List[float]]
    dimensions: int
    model: str
    processing_time: float

@router.post("/embeddings", response_model=EmbeddingResponse)
async def create_embeddings(request: EmbeddingRequest):
    """Generate embeddings for provided texts."""
    start_time = time.time()

    try:
        embeddings = await embedding_service.encode_texts(request.texts)
        processing_time = time.time() - start_time

        return EmbeddingResponse(
            embeddings=embeddings.tolist(),
            dimensions=embeddings.shape[1],
            model="multilingual-e5-large",
            processing_time=processing_time
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {str(e)}")

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if embedding_service.model is None:
            return {"status": "unhealthy", "error": "Model not loaded"}

        # Quick test
        test_embedding = await embedding_service.encode_texts("test")

        return {
            "status": "healthy",
            "model": "multilingual-e5-large",
            "device": embedding_service.device,
            "embedding_dimension": len(test_embedding[0])
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### Phase 5: Deployment Strategy

#### 5.1 Docker Setup

```dockerfile
# personal-embeddings-service/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Create model cache directory
RUN mkdir -p /app/models

# Pre-download model (optional - can also download at runtime)
# RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-large')"

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

#### 5.2 Requirements File

```txt
# personal-embeddings-service/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sentence-transformers==2.2.2
torch>=2.0.0
numpy==1.24.3
pydantic==2.5.0
httpx==0.25.2
```

#### 5.3 Docker Compose Integration

```yaml
# docker-compose.yml
version: '3.8'
services:
    embeddings-service:
        build: ./personal-embeddings-service
        ports:
            - '8001:8001'
        environment:
            - CUDA_VISIBLE_DEVICES=0 # If using GPU
        volumes:
            - ./models:/app/models # For model caching
        restart: unless-stopped
        deploy:
            resources:
                reservations:
                    devices:
                        - driver: nvidia
                          count: 1
                          capabilities: [gpu]

    rag-server:
        # ... existing config ...
        environment:
            - LOCAL_EMBEDDING_SERVICE_URL=http://embeddings-service:8001
            - PINECONE_INDEX_NAME=rag-server-e5-large
        depends_on:
            - embeddings-service
        restart: unless-stopped
```

### Phase 6: Testing & Validation

#### 6.1 Basic Testing Script

```python
# scripts/test_embeddings.py
import asyncio
import httpx
import numpy as np

async def test_embedding_service():
    """Test the local embedding service."""
    base_url = "http://localhost:8001"

    async with httpx.AsyncClient() as client:
        # Health check
        health = await client.get(f"{base_url}/api/v1/health")
        print(f"Health check: {health.json()}")

        # Test single embedding
        response = await client.post(
            f"{base_url}/api/v1/embeddings",
            json={"texts": "This is a test sentence."}
        )
        result = response.json()
        print(f"Single embedding dimensions: {result['dimensions']}")
        print(f"Processing time: {result['processing_time']:.3f}s")

        # Test batch embeddings
        response = await client.post(
            f"{base_url}/api/v1/embeddings",
            json={"texts": ["First sentence.", "Second sentence.", "Third sentence."]}
        )
        result = response.json()
        print(f"Batch embeddings count: {len(result['embeddings'])}")
        print(f"Batch processing time: {result['processing_time']:.3f}s")

if __name__ == "__main__":
    asyncio.run(test_embedding_service())
```

### Phase 7: Performance Optimization

#### 7.1 Model Optimization

```python
# personal-embeddings-service/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Model settings
    model_name: str = "intfloat/multilingual-e5-large"
    max_seq_length: int = 512
    batch_size: int = 32

    # Performance settings
    use_half_precision: bool = True  # Use float16 on GPU
    max_workers: int = 4
    cache_dir: str = "/app/models"

    # Service settings
    host: str = "0.0.0.0"
    port: int = 8001

settings = Settings()
```

#### 7.2 Caching Strategy

```python
# personal-embeddings-service/app/services/cache_service.py
from functools import lru_cache
import hashlib
import pickle
import os

class EmbeddingCache:
    def __init__(self, cache_dir: str = "/app/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()

    def get(self, text: str):
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")

        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None

    def set(self, text: str, embedding):
        cache_key = self._get_cache_key(text)
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")

        with open(cache_file, 'wb') as f:
            pickle.dump(embedding, f)

# In-memory cache for frequently used embeddings
@lru_cache(maxsize=1000)
def cached_embed_single(text: str):
    # This would be called by the embedding service
    pass
```

## Simplified Timeline (Fresh Start)

### Week 1: Development & Setup

-   Create embedding service project
-   Implement FastAPI service with e5-large
-   Create Docker configuration
-   Basic testing and optimization

### Week 2: Integration & Deployment

-   Update RAG server to use local embeddings
-   Create new Pinecone index
-   Docker deployment setup
-   End-to-end testing

### Week 3: Production Ready

-   Performance optimization
-   Monitoring and health checks
-   Documentation
-   Production deployment

## Success Metrics

1. **Cost**: Zero ongoing embedding costs
2. **Performance**: Embedding generation under 200ms for single documents
3. **Reliability**: 99.9% uptime for embedding service
4. **Quality**: Effective semantic search results
5. **Scalability**: Handle your expected document volume

## Conclusion

Starting fresh eliminates all migration complexity and allows for a clean, optimized implementation. The separate embedding service provides cost savings, better performance, and full control over the embedding process while maintaining a simple, maintainable architecture.
