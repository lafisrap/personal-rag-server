from openai import OpenAI
from app.core.config import settings
import logging
from typing import List, Dict, Any, Union
import numpy as np
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings using OpenAI API."""
    
    def __init__(self):
        self.client = None
        self.model_name = settings.EMBEDDINGS_MODEL
        self.dimension = 3072  # Dimension for text-embedding-3-large
    
    def initialize_client(self):
        """Initialize the OpenAI client."""
        try:
            if not self.client:
                logger.info(f"Initializing OpenAI client")
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info(f"OpenAI client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def get_embeddings(self, texts: Union[str, List[str]]) -> np.ndarray:
        """
        Generate embeddings for a text or list of texts.
        
        Args:
            texts: A single text or list of texts to generate embeddings for
            
        Returns:
            Numpy array of embeddings
        """
        if not self.client:
            self.initialize_client()
        
        try:
            # Handle single text input
            if isinstance(texts, str):
                input_texts = [texts]
            else:
                input_texts = texts
            
            # Call OpenAI API to get embeddings
            response = self.client.embeddings.create(
                model=self.model_name,
                input=input_texts
            )
            
            # Extract embeddings from response
            embeddings = [item.embedding for item in response.data]
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings)
            
            # Return single embedding or array of embeddings
            if isinstance(texts, str):
                return embeddings_array[0]
            return embeddings_array
            
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


# Create a singleton instance
embedding_service = EmbeddingService()
