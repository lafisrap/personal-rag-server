from app.db.vector_db import vector_db
from app.services.embedding_service import embedding_service
from app.services.llm_service import llm_service
from app.core.config import settings
import logging
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)

class RAGService:
    """Service for Retrieval Augmented Generation."""
    
    def __init__(self):
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        self.llm_service = llm_service
    
    def add_document(self, 
                     content: str, 
                     metadata: Dict[str, Any],
                     chunk_size: int = 1000,
                     chunk_overlap: int = 200) -> str:
        """
        Add a document to the vector database.
        
        Args:
            content: Document content
            metadata: Document metadata including categories and tags
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks in characters
            
        Returns:
            Document ID
        """
        try:
            # Generate a unique ID for the document
            doc_id = str(uuid.uuid4())
            
            # Validate metadata
            if "categories" in metadata:
                if len(metadata["categories"]) > settings.MAX_CATEGORIES:
                    raise ValueError(f"Maximum of {settings.MAX_CATEGORIES} categories allowed")
                
                for category, tags in metadata["categories"].items():
                    if len(tags) > settings.MAX_TAGS_PER_CATEGORY:
                        raise ValueError(f"Maximum of {settings.MAX_TAGS_PER_CATEGORY} tags per category allowed")
            
            # Simple text chunking - in a real implementation, you might want more sophisticated chunking
            chunks = []
            for i in range(0, len(content), chunk_size - chunk_overlap):
                chunk = content[i:i + chunk_size]
                if chunk:
                    chunks.append(chunk)
            
            # Generate embeddings for each chunk
            chunk_embeddings = self.embedding_service.get_embeddings(chunks)
            
            # Prepare vectors for upsert
            vectors = []
            for i, (chunk, embedding) in enumerate(zip(chunks, chunk_embeddings)):
                chunk_id = f"{doc_id}_{i}"
                vectors.append({
                    "id": chunk_id,
                    "values": embedding.tolist(),
                    "metadata": {
                        "text": chunk,
                        "document_id": doc_id,
                        "chunk_index": i,
                        **metadata
                    }
                })
            
            # Upsert vectors to the database
            self.vector_db.upsert_vectors(vectors)
            
            return doc_id
        except Exception as e:
            logger.error(f"Failed to add document: {str(e)}")
            raise
    
    def query(self, 
              query_text: str, 
              filter: Optional[Dict[str, Any]] = None,
              top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the vector database with semantic search.
        
        Args:
            query_text: Query text
            filter: Metadata filter
            top_k: Number of results to return
            
        Returns:
            List of matching documents with metadata
        """
        try:
            # Generate embeddings for the query
            query_embedding = self.embedding_service.get_embeddings(query_text)
            
            # Query the vector database
            query_result = self.vector_db.query_vectors(
                query_vector=query_embedding.tolist(),
                top_k=top_k,
                filter=filter
            )
            
            # Format the results
            results = []
            for match in query_result.matches:
                results.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "metadata": {k: v for k, v in match.metadata.items() if k != "text"}
                })
            
            return results
        except Exception as e:
            logger.error(f"Failed to query vector database: {str(e)}")
            raise
    
    def generate_rag_response(self,
                             messages: List[Dict[str, str]],
                             filter: Optional[Dict[str, Any]] = None,
                             system_prompt: Optional[str] = None,
                             top_k: int = 5) -> Dict[str, Any]:
        """
        Generate a RAG response for a user query.
        
        Args:
            messages: Conversation messages
            filter: Metadata filter for retrieval
            system_prompt: Optional system prompt
            top_k: Number of documents to retrieve
            
        Returns:
            RAG response with context and metadata
        """
        try:
            # Get the last user message
            last_user_msg = None
            for msg in reversed(messages):
                if msg["role"] == "user":
                    last_user_msg = msg["content"]
                    break
            
            if not last_user_msg:
                raise ValueError("No user message found in the conversation")
            
            # Retrieve relevant documents
            retrieved_docs = self.query(last_user_msg, filter=filter, top_k=top_k)
            
            # Extract text from retrieved documents
            context = [doc["text"] for doc in retrieved_docs]
            
            # Generate response with RAG
            response = self.llm_service.generate_with_rag(
                messages=messages,
                context=context,
                system_prompt=system_prompt
            )
            
            # Add metadata about retrieved documents
            response["retrieved_documents"] = retrieved_docs
            
            return response
        except Exception as e:
            logger.error(f"Failed to generate RAG response: {str(e)}")
            raise


# Create a singleton instance
rag_service = RAGService()
