from sentence_transformers import SentenceTransformer
from app.core.config import settings
import logging
from typing import List, Dict, Any, Union, Optional
import numpy as np
import torch
import os
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using SentenceTransformers."""
    
    def __init__(self):
        self.model = None
        self.model_name = os.environ.get("EMBEDDINGS_MODEL", "T-Systems-onsite/cross-en-de-roberta-sentence-transformer")
        self.dimension = int(os.environ.get("EMBEDDINGS_DIMENSION", "768"))
        
        # Performance settings
        self.use_mps = settings.USE_MPS  # Use Apple Metal Performance Shaders if available
        self.use_half_precision = True  # Use half precision on supported hardware
        self.device = None
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.max_cache_size = 10000  # Maximum number of embeddings to cache
    
    def _detect_device(self):
        """Detect the best available device for inference."""
        if torch.backends.mps.is_available():
            # Use Apple Metal Performance Shaders (MPS) for M1/M2 GPU acceleration
            device = torch.device("mps")
            logger.info("Using Apple MPS (Metal Performance Shaders) for GPU acceleration")
        elif torch.cuda.is_available():
            # Fallback to CUDA if available (unlikely on M1 Mac)
            device = torch.device("cuda")
            logger.info("Using CUDA for GPU acceleration")
        else:
            # Fallback to CPU
            device = torch.device("cpu")
            logger.info("Using CPU for inference (no GPU acceleration available)")
        
        return device
    
    def load_model(self):
        """Load the GBERT-large model with optimizations for M1 Max."""
        try:
            if not self.model:
                start_time = time.time()
                logger.info(f"Loading embedding model: {self.model_name}")
                
                # Detect device
                self.device = self._detect_device()
                
                # Set environment variables for better performance
                os.environ["TOKENIZERS_PARALLELISM"] = "true"
                
                # Load the model with optimizations
                self.model = SentenceTransformer(
                    self.model_name,
                    device=str(self.device)
                )
                
                # Apply half-precision for better performance if on GPU
                if self.device.type != "cpu":
                    self.model.half()  # Convert to FP16 for faster inference
                
                load_time = time.time() - start_time
                logger.info(f"Embedding model loaded: {self.model_name} on {self.device} in {load_time:.2f} seconds")
                
                # Run a warm-up inference
                self._warmup()
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    
    def _warmup(self):
        """Warm up the model with a sample inference."""
        try:
            logger.info("Warming up the embedding model...")
            start_time = time.time()
            _ = self.model.encode(["Warm up text for better initial performance"])
            warmup_time = time.time() - start_time
            logger.info(f"Model warm-up completed in {warmup_time:.2f} seconds")
        except Exception as e:
            logger.warning(f"Model warm-up failed: {str(e)}")
    
    @lru_cache(maxsize=1024)  # Cache the most recent 1024 embeddings
    def _get_embedding_cached(self, text: str) -> np.ndarray:
        """Generate embedding for a single text with caching."""
        return self.model.encode(text, convert_to_numpy=True)
    
    def get_embeddings(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for a text or list of texts with batching and caching.
        
        Args:
            texts: A single text or list of texts to generate embeddings for
            batch_size: Batch size for processing multiple texts
            
        Returns:
            Numpy array of embeddings
        """
        if not self.model:
            self.load_model()
        
        try:
            # Handle single text input
            if isinstance(texts, str):
                # Use the cached version for single strings
                return self._get_embedding_cached(texts)
            
            # For lists, process in batches for better performance
            if len(texts) > batch_size:
                # Process in batches
                all_embeddings = []
                for i in range(0, len(texts), batch_size):
                    batch = texts[i:i + batch_size]
                    batch_embeddings = self.model.encode(
                        batch,
                        batch_size=batch_size,
                        show_progress_bar=len(batch) > 100,
                        convert_to_numpy=True
                    )
                    all_embeddings.append(batch_embeddings)
                return np.vstack(all_embeddings)
            else:
                # Small enough list to process at once
                return self.model.encode(
                    texts,
                    batch_size=batch_size,
                    convert_to_numpy=True
                )
                
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {str(e)}")
            raise
    
    def similarity_search(self, query: str, documents: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform similarity search between a query and a list of documents.
        
        Args:
            query: Query text
            documents: List of document texts to compare against
            top_k: Number of top results to return
            
        Returns:
            List of dictionaries with document index and similarity score
        """
        try:
            query_embedding = self.get_embeddings(query)
            doc_embeddings = self.get_embeddings(documents)
            
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
    
    def get_health_check(self) -> Dict[str, Any]:
        """Get health check information about the embedding service."""
        if not self.model:
            self.load_model()
        
        # Run a test embedding to measure performance
        test_text = "Dies ist ein Test für das deutsche Embedding-Modell."
        start_time = time.time()
        _ = self.get_embeddings(test_text)
        processing_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "model": self.model_name,
            "device": str(self.device),
            "embedding_dimension": self.dimension,
            "test_processing_time": processing_time,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses
            }
        }


# Create a singleton instance
embedding_service = EmbeddingService()
