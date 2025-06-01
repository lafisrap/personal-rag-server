#!/usr/bin/env python3
"""
CLI tool for knowledge base management.
"""

import os
import sys
import argparse
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.kb_scanner import kb_scanner
from app.services.file_processor import file_processor
from app.services.vector_store_manager import vector_store_manager
from app.db.vector_db import vector_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"kb_management_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    ]
)

logger = logging.getLogger("kb_management")

def upload_knowledge_base(args):
    """Upload the entire knowledge base to Pinecone."""
    source_path = args.source
    
    # Verify the source path
    if not os.path.exists(source_path):
        logger.error(f"Source path does not exist: {source_path}")
        return
    
    logger.info(f"Starting knowledge base upload from: {source_path}")
    
    # Scan the directory
    try:
        logger.info("Scanning knowledge base...")
        categories = kb_scanner.scan_directory(source_path)
        logger.info(f"Found {len(categories)} categories")
        
        stats = {
            "total_categories": len(categories),
            "total_documents": 0,
            "successful_documents": 0,
            "failed_documents": 0,
            "categories": {}
        }
        
        # Process each category
        for category, files in categories.items():
            if args.categories and category not in args.categories.split(','):
                logger.info(f"Skipping category: {category} (not in selected categories)")
                continue
                
            logger.info(f"Processing category: {category} with {len(files)} files")
            
            # Group related files
            related_files = kb_scanner.get_related_files(files)
            logger.info(f"Found {len(related_files)} document groups in {category}")
            
            # Process and upload text documents
            text_documents = []
            for base_name, files_by_ext in related_files.items():
                if ".txt" in files_by_ext:
                    # Process the text file
                    text_file_info = files_by_ext[".txt"]
                    processed_doc = file_processor.process_file(text_file_info)
                    
                    # Enrich with metadata from related files
                    if processed_doc["type"] == "text":
                        enriched_doc = file_processor.enrich_document_with_metadata(processed_doc, files_by_ext)
                        text_documents.append(enriched_doc)
            
            # Upload to Pinecone
            if text_documents:
                logger.info(f"Upserting {len(text_documents)} documents to category: {category}")
                category_stats = vector_store_manager.upsert_category(category, text_documents)
                
                # Update stats
                stats["total_documents"] += category_stats["total_documents"]
                stats["successful_documents"] += category_stats["successful"]
                stats["failed_documents"] += category_stats["failed"]
                stats["categories"][category] = {
                    "total_documents": category_stats["total_documents"],
                    "successful": category_stats["successful"],
                    "failed": category_stats["failed"]
                }
            else:
                logger.warning(f"No text documents found for category: {category}")
                stats["categories"][category] = {
                    "total_documents": 0,
                    "successful": 0,
                    "failed": 0
                }
        
        # Print summary
        logger.info("Upload completed")
        logger.info(f"Summary: {json.dumps(stats, indent=2)}")
        
        # Save stats to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"kb_upload_stats_{timestamp}.json", "w") as f:
            json.dump(stats, f, indent=2)
            
    except Exception as e:
        logger.error(f"Error during knowledge base upload: {str(e)}")
        raise

def update_categories(args):
    """Update specific categories in the knowledge base."""
    if not args.categories:
        logger.error("No categories specified for update. Use --categories.")
        return
    
    source_path = args.source
    categories = args.categories.split(',')
    
    logger.info(f"Updating categories: {', '.join(categories)}")
    
    # Delete existing categories first if requested
    if args.delete_existing:
        for category in categories:
            logger.info(f"Deleting existing data for category: {category}")
            vector_store_manager.delete_category(category)
    
    # Then upload new data
    args.categories = ','.join(categories)  # Convert back to string for upload function
    upload_knowledge_base(args)

def delete_categories(args):
    """Delete specific categories from the vector store."""
    if not args.categories:
        logger.error("No categories specified for deletion. Use --categories.")
        return
    
    categories = args.categories.split(',')
    logger.info(f"Deleting categories: {', '.join(categories)}")
    
    for category in categories:
        logger.info(f"Deleting category: {category}")
        success = vector_store_manager.delete_category(category)
        if success:
            logger.info(f"Successfully deleted category: {category}")
        else:
            logger.error(f"Failed to delete category: {category}")

def show_stats(args):
    """Show statistics about the vector store."""
    if args.categories:
        categories = args.categories.split(',')
    else:
        # Try to get all categories - not efficient but works for demo
        sample_vector = vector_store_manager.embedding_service.get_embeddings("sample query").tolist()
        query_result = vector_store_manager.vector_db.query_vectors(
            query_vector=sample_vector,
            top_k=10000
        )
        
        categories = set()
        for match in query_result.matches:
            if match.metadata.get("category"):
                categories.add(match.metadata.get("category"))
    
    logger.info(f"Retrieving statistics for categories: {', '.join(categories)}")
    
    stats = {
        "categories": {},
        "total_documents": 0,
        "total_chunks": 0
    }
    
    for category in categories:
        category_stats = vector_store_manager.get_category_stats(category)
        stats["categories"][category] = category_stats
        stats["total_documents"] += category_stats["document_count"]
        stats["total_chunks"] += category_stats["chunk_count"]
    
    # Print summary
    logger.info(f"Vector Store Statistics: {json.dumps(stats, indent=2)}")
    
    # Save stats to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"kb_stats_{timestamp}.json", "w") as f:
        json.dump(stats, f, indent=2)

def main():
    """Main function to parse arguments and execute commands."""
    parser = argparse.ArgumentParser(description="Knowledge Base Management Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload knowledge base to Pinecone")
    upload_parser.add_argument("--source", required=True, help="Path to knowledge base directory")
    upload_parser.add_argument("--categories", help="Comma-separated list of categories to upload")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update specific categories")
    update_parser.add_argument("--source", required=True, help="Path to knowledge base directory")
    update_parser.add_argument("--categories", required=True, help="Comma-separated list of categories to update")
    update_parser.add_argument("--delete-existing", action="store_true", help="Delete existing data before update")
    
    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete specific categories")
    delete_parser.add_argument("--categories", required=True, help="Comma-separated list of categories to delete")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show statistics about the vector store")
    stats_parser.add_argument("--categories", help="Comma-separated list of categories to show stats for")
    
    args = parser.parse_args()
    
    if args.command == "upload":
        upload_knowledge_base(args)
    elif args.command == "update":
        update_categories(args)
    elif args.command == "delete":
        delete_categories(args)
    elif args.command == "stats":
        show_stats(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 