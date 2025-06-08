#!/usr/bin/env python3
"""
Test script to verify the complete RAG pipeline with GBERT-large embeddings and DeepSeek LLM.
"""
import time
import logging
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.services.embedding_service import embedding_service
from app.db.vector_db import vector_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_embedding_service():
    """Test the embedding service with GBERT-large."""
    logger.info("\n=== Testing GBERT-large Embedding Service ===")
    
    # Test text in German
    test_text = "Dies ist ein Test für das deutsche Embedding-Modell GBERT-large."
    
    # Generate embedding
    start_time = time.time()
    embedding = embedding_service.get_embeddings(test_text)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Generated embedding in {elapsed_time:.4f} seconds")
    logger.info(f"Embedding dimension: {embedding.shape}")
    logger.info(f"Using device: {embedding_service.device}")
    
    return True

def test_document_addition():
    """Test adding a document to the vector database."""
    logger.info("\n=== Testing Document Addition to Vector DB ===")
    
    # Sample document
    content = """
    Die Philosophie ist eine Wissenschaft, die sich mit allgemeinen und grundlegenden Fragen 
    zum Sein, zum Wissen und zu den Werten befasst. Sie unterscheidet sich von anderen 
    Wissenschaften dadurch, dass sie nicht auf empirische Methoden zurückgreift, 
    sondern auf rationale Argumentation und kritisches Denken.
    """
    
    # Metadata - Pinecone requires flat metadata structure
    metadata = {
        "title": "Einführung in die Philosophie",
        "author": "Test Author",
        "category": "philosophy",
        "tags": ["introduction", "german"]
    }
    
    # Add document
    start_time = time.time()
    doc_id = rag_service.add_document(content, metadata)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Added document with ID {doc_id} in {elapsed_time:.4f} seconds")
    
    return doc_id

def test_vector_search(query_text="Was ist Philosophie?"):
    """Test vector search with a query."""
    logger.info("\n=== Testing Vector Search ===")
    
    # Search for documents
    start_time = time.time()
    results = rag_service.query(query_text, top_k=3)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Query: '{query_text}'")
    logger.info(f"Found {len(results)} results in {elapsed_time:.4f} seconds")
    
    for i, result in enumerate(results):
        logger.info(f"Result {i+1}: Score {result['score']:.4f}")
        logger.info(f"Text: {result['text'][:100]}...")
    
    return results

def test_rag_response(query_text="Was ist Philosophie?"):
    """Test generating a RAG response."""
    logger.info("\n=== Testing RAG Response Generation ===")
    
    # Create a simple conversation
    messages = [
        {"role": "user", "content": query_text}
    ]
    
    # Generate RAG response
    start_time = time.time()
    response = rag_service.generate_rag_response(messages)
    elapsed_time = time.time() - start_time
    
    logger.info(f"Generated RAG response in {elapsed_time:.4f} seconds")
    logger.info(f"Using LLM model: {response.get('model', 'unknown')}")
    logger.info(f"Response: {response['content']}")
    
    # Log retrieved documents
    logger.info(f"Retrieved {len(response.get('retrieved_documents', []))} documents")
    
    return response

def run_full_pipeline_test():
    """Run a full pipeline test."""
    logger.info("=== Starting Full RAG Pipeline Test ===")
    
    # 1. Test embedding service
    embedding_ok = test_embedding_service()
    
    # 2. Test document addition
    doc_id = test_document_addition()
    
    # 3. Test vector search
    search_results = test_vector_search()
    
    # 4. Test RAG response generation
    rag_response = test_rag_response()
    
    logger.info("\n=== RAG Pipeline Test Complete ===")
    logger.info(f"Pipeline success: {embedding_ok and doc_id and search_results and rag_response}")
    
    return {
        "embedding_ok": embedding_ok,
        "document_id": doc_id,
        "search_results": search_results,
        "rag_response": rag_response
    }

if __name__ == "__main__":
    # Initialize vector DB
    vector_db.init_pinecone()
    
    # Run the full pipeline test
    results = run_full_pipeline_test()
    
    # Print final results
    print("\n=== Final Results ===")
    print(f"Embedding Service: {'✓' if results['embedding_ok'] else '✗'}")
    print(f"Document Addition: {'✓' if results['document_id'] else '✗'}")
    print(f"Vector Search: {'✓' if results['search_results'] else '✗'}")
    print(f"RAG Response: {'✓' if results['rag_response'] else '✗'}") 