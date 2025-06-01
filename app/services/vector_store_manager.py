import logging
from typing import Dict, List, Any, Optional, Tuple
import uuid
import time
from app.db.vector_db import vector_db
from app.services.embedding_service import embedding_service
import json

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Service for managing vector data in Pinecone."""
    
    def __init__(self):
        self.vector_db = vector_db
        self.embedding_service = embedding_service
        # Make sure the vector DB is initialized
        if not self.vector_db.initialized:
            self.vector_db.init_pinecone()
    
    def upsert_document(self, 
                        document: Dict[str, Any], 
                        category: str,
                        namespace: Optional[str] = None) -> str:
        """
        Upsert a document to Pinecone.
        
        Args:
            document: Processed document with chunks
            category: The worldview category
            namespace: Optional namespace override (defaults to category)
            
        Returns:
            Document ID
        """
        if document["type"] != "text" or "chunks" not in document:
            logger.warning(f"Cannot upsert non-text document: {document.get('filename')}")
            return ""
        
        # Use category as namespace if not specified
        ns = namespace or category
        
        try:
            # Generate a document ID if not present
            doc_id = document.get("document_id", str(uuid.uuid4()))
            
            # Prepare metadata
            base_metadata = {
                "document_id": doc_id,
                "filename": document.get("filename", ""),
                "category": category,
                "author": document.get("author"),
                "title": document.get("title"),
            }
            
            # Add word stats if available (limit to top 10 to reduce metadata size)
            if "word_stats" in document:
                # Take top 10 word stats to keep metadata size reasonable
                top_words = document["word_stats"][:10] if document["word_stats"] else []
                if top_words:
                    if isinstance(top_words[0], tuple):
                        base_metadata["top_words"] = [item[0] for item in top_words]
                    elif isinstance(top_words[0], dict) and "word" in top_words[0]:
                        base_metadata["top_words"] = [item["word"] for item in top_words]
            
            # Generate embeddings for chunks
            chunks = document["chunks"]
            logger.info(f"Generating embeddings for {len(chunks)} chunks from {document.get('filename')}")
            
            # Process in smaller batches to avoid API limits and memory issues
            embedding_batch_size = 10
            all_vectors = []
            
            for i in range(0, len(chunks), embedding_batch_size):
                batch_chunks = chunks[i:i+embedding_batch_size]
                
                # Generate embeddings
                try:
                    batch_embeddings = self.embedding_service.get_embeddings(batch_chunks)
                    
                    # Create vectors for the batch
                    for j, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
                        chunk_idx = i + j
                        chunk_id = f"{doc_id}_{chunk_idx}"
                        
                        # Create metadata for this chunk (keep it minimal)
                        chunk_metadata = {
                            **base_metadata,
                            "text": chunk[:2000],  # Limit text in metadata to 2000 chars to reduce size
                            "chunk_index": chunk_idx,
                        }
                        
                        all_vectors.append({
                            "id": chunk_id,
                            "values": embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                            "metadata": chunk_metadata
                        })
                    
                    # Add small delay to avoid rate limits
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.error(f"Error generating embeddings for batch: {str(e)}")
                    continue
            
            # Upsert vectors in smaller batches to avoid Pinecone payload size limits
            # Pinecone limit is ~4MB, so we'll use smaller batches
            upsert_batch_size = 50  # Smaller batch size for upsert
            total_upserted = 0
            
            for i in range(0, len(all_vectors), upsert_batch_size):
                batch_vectors = all_vectors[i:i+upsert_batch_size]
                
                if batch_vectors:
                    try:
                        logger.info(f"Upserting batch {i//upsert_batch_size + 1} with {len(batch_vectors)} vectors")
                        response = self.vector_db.upsert_vectors(batch_vectors)
                        total_upserted += len(batch_vectors)
                        logger.debug(f"Batch upsert response: {response}")
                        
                        # Add delay between batches to avoid rate limits
                        time.sleep(0.5)
                        
                    except Exception as e:
                        logger.error(f"Error upserting batch {i//upsert_batch_size + 1}: {str(e)}")
                        # Continue with next batch rather than failing completely
                        continue
            
            logger.info(f"Successfully upserted {total_upserted} vectors for document {document.get('filename')}")
            return doc_id
            
        except Exception as e:
            logger.error(f"Failed to upsert document {document.get('filename')}: {str(e)}")
            raise
    
    def upsert_category(self, 
                        category: str, 
                        documents: List[Dict[str, Any]],
                        namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Upsert all documents for a category to Pinecone.
        
        Args:
            category: The worldview category (namespace)
            documents: List of processed documents
            namespace: Optional namespace override
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            "category": category,
            "total_documents": len(documents),
            "successful": 0,
            "failed": 0,
            "document_ids": []
        }
        
        for doc in documents:
            try:
                doc_id = self.upsert_document(doc, category, namespace)
                if doc_id:
                    stats["successful"] += 1
                    stats["document_ids"].append(doc_id)
                else:
                    stats["failed"] += 1
            except Exception as e:
                logger.error(f"Error upserting document {doc.get('filename')}: {str(e)}")
                stats["failed"] += 1
        
        return stats
    
    def delete_category(self, category: str, namespace: Optional[str] = None) -> bool:
        """
        Delete all vectors for a category.
        
        Args:
            category: The category to delete
            namespace: Optional namespace override (defaults to category)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use category as namespace if not specified
            ns = namespace or category
            
            # We need to find all document IDs first
            # This is a simple approach - fetch all vectors and extract document IDs
            # For production, consider using Pinecone metadata filtering if available
            
            # Get sample query vector (since we need one for the query)
            sample_vector = self.embedding_service.get_embeddings("sample query for deletion").tolist()
            
            # Query with high top_k to get many vectors
            query_result = self.vector_db.query_vectors(
                query_vector=sample_vector,
                top_k=10000,  # Adjust based on expected size
                filter=None
            )
            
            # Extract unique document IDs
            doc_ids = set()
            for match in query_result.matches:
                if match.metadata.get("category") == category:
                    doc_ids.add(match.metadata.get("document_id"))
            
            # Delete documents one by one
            for doc_id in doc_ids:
                self.delete_document(doc_id, category)
            
            logger.info(f"Deleted {len(doc_ids)} documents from category {category}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete category {category}: {str(e)}")
            return False
    
    def delete_document(self, document_id: str, category: str, namespace: Optional[str] = None) -> bool:
        """
        Delete a document and all its chunks.
        
        Args:
            document_id: ID of the document to delete
            category: The category the document belongs to
            namespace: Optional namespace override
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use category as namespace if not specified
            ns = namespace or category
            
            # We need to find all chunk IDs for this document
            # This is a simple approach - fetch all vectors and extract chunk IDs
            # For production, consider using Pinecone metadata filtering if available
            
            # Get sample query vector (since we need one for the query)
            sample_vector = self.embedding_service.get_embeddings("sample query for deletion").tolist()
            
            # Query with high top_k to get many vectors
            query_result = self.vector_db.query_vectors(
                query_vector=sample_vector,
                top_k=10000,  # Adjust based on expected size
                filter={"document_id": document_id}
            )
            
            # Extract IDs to delete
            ids_to_delete = [match.id for match in query_result.matches]
            
            if ids_to_delete:
                # Delete vectors
                self.vector_db.delete_vectors(ids_to_delete)
                logger.info(f"Deleted {len(ids_to_delete)} vectors for document {document_id}")
                return True
            else:
                logger.warning(f"No vectors found for document {document_id}")
                return False
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    def get_category_stats(self, category: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics for a category.
        
        Args:
            category: The category to get statistics for
            namespace: Optional namespace override
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Use category as namespace if not specified
            ns = namespace or category
            
            # Get sample query vector
            sample_vector = self.embedding_service.get_embeddings("sample query for stats").tolist()
            
            # Query with high top_k to get many vectors
            query_result = self.vector_db.query_vectors(
                query_vector=sample_vector,
                top_k=10000,  # Adjust based on expected size
                filter={"category": category}
            )
            
            # Calculate statistics
            doc_ids = set()
            authors = set()
            titles = set()
            chunk_count = len(query_result.matches)
            
            for match in query_result.matches:
                metadata = match.metadata
                if metadata.get("document_id"):
                    doc_ids.add(metadata.get("document_id"))
                if metadata.get("author"):
                    authors.add(metadata.get("author"))
                if metadata.get("title"):
                    titles.add(metadata.get("title"))
            
            return {
                "category": category,
                "document_count": len(doc_ids),
                "chunk_count": chunk_count,
                "author_count": len(authors),
                "title_count": len(titles),
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics for category {category}: {str(e)}")
            return {
                "category": category,
                "error": str(e),
                "document_count": 0,
                "chunk_count": 0,
            }


# Create a singleton instance
vector_store_manager = VectorStoreManager() 