#!/usr/bin/env python3
"""
Script to list all indexed books in the vector store.
"""
import os
import sys
import logging
from datetime import datetime
from tqdm import tqdm
from typing import List, Dict, Any, Optional

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

from app.db.vector_db import vector_db
from app.services.rag_service import rag_service
from app.services.embedding_service import embedding_service
from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_indexed_books(output_dir: str = "results") -> bool:
    """
    List all indexed books in the vector store.
    
    Args:
        output_dir: Directory to save the output file
        
    Returns:
        True if successful, False otherwise
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "indexed_books.txt")
    
    logger.info("=== Starte Auflistung aller indizierten Bücher ===")
    
    try:
        # Initialize vector database
        if not vector_db.initialized:
            vector_db.init_pinecone()
        
        logger.info("Hole Dokumente aus dem Index...")
        
        # Get sample query vector (since we need one for the query)
        sample_vector = embedding_service.get_embeddings("sample query for listing").tolist()
        
        # We need to use a high top_k to get many vectors
        # Pinecone has a limit of 10,000 results per query
        top_k = 10000
        
        # Query with high top_k to get many vectors
        query_result = vector_db.index.query(
            vector=sample_vector,
            top_k=top_k,
            include_values=False,
            include_metadata=True
        )
        
        # Group documents by filename
        documents = {}
        for match in query_result.matches:
            metadata = match.metadata
            filename = metadata.get('filename', 'Unknown')
            category = metadata.get('category', 'Unknown')
            doc_id = match.id
            
            if filename not in documents:
                documents[filename] = {
                    'categories': set(),
                    'chunks': 0,
                    'ids': set()
                }
            
            documents[filename]['chunks'] += 1
            documents[filename]['ids'].add(doc_id)
            
            # Handle multiple categories (comma-separated)
            if isinstance(category, str) and ',' in category:
                for cat in category.split(','):
                    documents[filename]['categories'].add(cat.strip())
            else:
                documents[filename]['categories'].add(category)
        
        logger.info(f"Gefunden: {len(documents)} Dokumente")
        
        # Group documents by category
        categories = {}
        for filename, data in documents.items():
            for category in data['categories']:
                if category not in categories:
                    categories[category] = []
                categories[category].append(filename)
        
        # Write results to file
        with open(output_file, 'w', encoding='utf-8') as f:
            # Write header
            f.write(f"# Indizierte Bücher - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"Gesamt: {len(documents)} Dokumente in {len(categories)} Kategorien\n\n")
            
            # Table of all documents
            f.write("## Alle Dokumente\n\n")
            f.write("| Dateiname | Kategorien | Chunks | IDs |\n")
            f.write("| --- | --- | --- | --- |\n")
            
            for filename, data in sorted(documents.items()):
                categories_str = ', '.join(data['categories'])
                ids_str = ', '.join(list(data['ids'])[:2])  # Limit to 2 IDs to avoid too long lines
                if len(data['ids']) > 2:
                    ids_str += f"... (+{len(data['ids']) - 2} more)"
                
                f.write(f"| {filename} | {categories_str} | {data['chunks']} | {ids_str} |\n")
            
            # Documents by category
            f.write("\n## Dokumente nach Kategorie\n\n")
            
            for category, filenames in sorted(categories.items()):
                f.write(f"### Kategorie: {category}\n\n")
                f.write(f"Anzahl Dokumente: {len(filenames)}\n\n")
                
                for filename in sorted(filenames):
                    f.write(f"- **{filename}** ({documents[filename]['chunks']} Chunks)\n")
                
                f.write("\n")
            
            # Author statistics if available
            authors = {}
            for filename, data in documents.items():
                for match in query_result.matches:
                    if match.metadata.get('filename') == filename:
                        author = match.metadata.get('author', 'Unknown')
                        if author not in authors:
                            authors[author] = set()
                        authors[author].add(filename)
                        break
            
            if authors:
                f.write("\n## Dokumente nach Autor\n\n")
                
                for author, filenames in sorted(authors.items()):
                    if author and author != 'Unknown':
                        f.write(f"### Autor: {author}\n\n")
                        f.write(f"Anzahl Dokumente: {len(filenames)}\n\n")
                        
                        for filename in sorted(filenames):
                            f.write(f"- **{filename}** ({documents[filename]['chunks']} Chunks)\n")
                        
                        f.write("\n")
        
        logger.info(f"Liste aller indizierten Bücher wurde in '{output_file}' gespeichert.")
        return True
        
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Bücher: {str(e)}")
        return False

if __name__ == "__main__":
    success = list_indexed_books()
    exit(0 if success else 1) 