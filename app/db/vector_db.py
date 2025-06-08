from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class VectorDatabase:
    """Vector Database client for storing and retrieving vectors."""
    
    def __init__(self):
        self.initialized = False
        self.pc = None
        self.index = None
    
    def init_pinecone(self):
        """Initialize Pinecone index."""
        try:
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            
            # Check if index exists, if not create it
            existing_indexes = self.pc.list_indexes().names()
            
            if settings.PINECONE_INDEX_NAME not in existing_indexes:
                # Create index with appropriate dimension for the embedding model
                dimension = settings.EMBEDDINGS_DIMENSION
                
                # Create the index with ServerlessSpec
                self.pc.create_index(
                    name=settings.PINECONE_INDEX_NAME,
                    dimension=dimension,
                    metric="cosine",
                    spec=ServerlessSpec(
                        cloud="aws",
                        region=settings.PINECONE_ENVIRONMENT or "us-east-1"
                    )
                )
                logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX_NAME}")
            
            # Connect to the index
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            self.initialized = True
            logger.info(f"Connected to Pinecone index: {settings.PINECONE_INDEX_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize Pinecone: {str(e)}")
            raise
    
    def upsert_vectors(self, vectors: List[Dict[str, Any]]):
        """
        Upsert vectors to the index.
        
        Args:
            vectors: List of dictionaries with 'id', 'values', and 'metadata'
        """
        if not self.initialized:
            self.init_pinecone()
        
        try:
            return self.index.upsert(vectors=vectors)
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {str(e)}")
            raise
    
    def query_vectors(self, 
                      query_vector: List[float], 
                      top_k: int = 5, 
                      filter: Optional[Dict[str, Any]] = None):
        """
        Query the vector database.
        
        Args:
            query_vector: The query embedding vector
            top_k: Number of results to return
            filter: Metadata filter to apply
            
        Returns:
            Query results
        """
        if not self.initialized:
            self.init_pinecone()
        
        try:
            return self.index.query(
                vector=query_vector,
                top_k=top_k,
                include_values=False,
                include_metadata=True,
                filter=filter
            )
        except Exception as e:
            logger.error(f"Failed to query vectors: {str(e)}")
            raise
    
    def delete_vectors(self, ids: List[str]):
        """
        Delete vectors by ID.
        
        Args:
            ids: List of vector IDs to delete
        """
        if not self.initialized:
            self.init_pinecone()
        
        try:
            return self.index.delete(ids=ids)
        except Exception as e:
            logger.error(f"Failed to delete vectors: {str(e)}")
            raise


# Create a singleton instance
vector_db = VectorDatabase()
