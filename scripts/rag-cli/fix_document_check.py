#!/usr/bin/env python3
"""
A simple script to check if a document exists in the vector database.
Uses a comprehensive search approach that doesn't rely on semantic search.
"""

import os
import sys
import logging
from datetime import datetime

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from app.db.vector_db import vector_db
from app.services.rag_service import rag_service
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_document_exists(document_id, expected_category=None):
    """
    Check if a document exists in the vector database.
    
    Args:
        document_id: Document ID to check
        expected_category: Optional category to check
        
    Returns:
        True if document exists, False otherwise
    """
    print(f"Checking document: {document_id}")
    print(f"Expected category: {expected_category}")
    
    # Connect to vector store
    if not vector_db.initialized:
        vector_db.init_pinecone()
        print("Connected to vector database")
    
    # Handle .txt extension - try both with and without .txt
    document_id_with_txt = document_id
    if not document_id.endswith('.txt'):
        document_id_with_txt = document_id + '.txt'
    document_id_without_txt = document_id
    if document_id.endswith('.txt'):
        document_id_without_txt = document_id[:-4]
    
    print(f"Will search for: {document_id}, {document_id_with_txt}, {document_id_without_txt}")
    
    # Get index stats
    stats = vector_db.index.describe_index_stats()
    total_vectors = stats.get('total_vector_count', 0)
    print(f"Total vectors in index: {total_vectors}")
    
    # Sample query vector (since we need one for the query)
    print("Generating sample embedding...")
    sample_vector = rag_service.embedding_service.get_embeddings("sample query").tolist()
    
    matching_docs = []
    batch_size = 1000
    
    # Fetch vectors in batches
    for i in range(0, min(10000, total_vectors), batch_size):
        print(f"Checking batch {i}-{i+batch_size}")
        query_result = vector_db.index.query(
            vector=sample_vector,
            top_k=batch_size,
            include_values=False,
            include_metadata=True,
            offset=i
        )
        
        print(f"Received {len(query_result.matches)} results in this batch")
        
        # Check each result for our document ID
        for match in query_result.matches:
            metadata = match.metadata
            filename = metadata.get('filename', '')
            if document_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                print(f"Found match: {filename}")
                matching_docs.append({
                    "id": match.id,
                    "score": match.score,
                    "metadata": metadata
                })
    
    # Process results
    if matching_docs:
        print(f"Found {len(matching_docs)} matching chunks for document '{document_id}'")
        
        # Show categories
        categories = set()
        for doc in matching_docs:
            category = doc["metadata"].get("category", "Unknown")
            if isinstance(category, str) and "," in category:
                for cat in category.split(","):
                    categories.add(cat.strip())
            else:
                categories.add(category)
        
        print(f"Categories: {', '.join(categories)}")
        
        # Check expected category
        if expected_category:
            category_match = expected_category in categories
            print(f"Expected category '{expected_category}' match: {category_match}")
        
        # Show sample metadata
        print(f"Sample metadata from first match:")
        for key, value in matching_docs[0]["metadata"].items():
            print(f"  {key}: {value}")
        
        return True
    else:
        print(f"No matches found for document '{document_id}'")
        return False

def main():
    """Run the script."""
    print("======= DOCUMENT CHECK SCRIPT =======")
    document_id = "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]"
    expected_category = "Realismus"
    
    print(f"Checking if document '{document_id}' exists")
    print(f"Expected category: '{expected_category}'")
    
    success = check_document_exists(document_id, expected_category)
    
    if success:
        print("SUCCESS: Document was found in the index!")
    else:
        print("FAILURE: Document was not found in the index!")
    
    print("======= SCRIPT COMPLETED =======")
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 