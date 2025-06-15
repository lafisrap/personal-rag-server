#!/usr/bin/env python3
"""
RAG CLI - Command Line Interface for RAG (Retrieval-Augmented Generation) Management

This tool provides a unified interface for managing RAG components:
- Knowledge base management (upload, update, delete, stats)
- Search and query operations
- Diagnostics and reporting
"""

import os
import sys
import click
import logging
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import time
from tqdm import tqdm
import uuid

# Add the project root to the Python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, PROJECT_ROOT)

# Configure logging
log_dir = os.path.join(PROJECT_ROOT, 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, f"rag_cli_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"))
    ]
)
logger = logging.getLogger("rag-cli")

# Suppress noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)
logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
logging.getLogger("transformers").setLevel(logging.WARNING)
logging.getLogger("numexpr").setLevel(logging.WARNING)
logging.getLogger("assistants.deepseek_assistant_manager").setLevel(logging.WARNING)

# Set tokenizers parallelism to avoid warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Suppress specific ML library warnings
import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="transformers")
warnings.filterwarnings("ignore", message="No sentence-transformers model found.*")
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")

# Additional logging configuration for ML libraries
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)
logging.getLogger("transformers").setLevel(logging.ERROR)

# Create main CLI group
@click.group()
@click.version_option(version="0.1.0")
def cli():
    """RAG CLI - Command Line Interface for RAG (Retrieval-Augmented Generation) Management."""
    pass

# Pinecone Management Commands
@cli.group('pinecone')
def pinecone_group():
    """Pinecone vector database management commands."""
    pass

@pinecone_group.command('truncate')
@click.option('--index-name', required=True, help='Name of the Pinecone index to truncate')
@click.confirmation_option(prompt='Are you sure you want to truncate the Pinecone index? This will delete ALL vectors!')
def pinecone_truncate(index_name: str):
    """Truncate (delete all vectors from) a Pinecone index."""
    from app.db.vector_db import vector_db
    from app.core.config import settings
    
    click.echo(f"Truncating Pinecone index: {index_name}")
    
    try:
        # Verify the index name
        if settings.PINECONE_INDEX_NAME != index_name:
            click.echo(f"Warning: The specified index ({index_name}) does not match the configured index ({settings.PINECONE_INDEX_NAME})")
            if not click.confirm("Do you want to continue anyway?"):
                click.echo("Operation cancelled.")
                return
        
        # Initialize Vector-DB
        vector_db.init_pinecone()
        
        # Delete all vectors using namespace deletion approach
        namespaces = vector_db.index.describe_index_stats().get('namespaces', {})
        
        if not namespaces:
            click.echo("No namespaces found in the index. The index may already be empty.")
            return
        
        click.echo(f"Found {len(namespaces)} namespaces: {', '.join(namespaces.keys())}")
        with click.progressbar(namespaces.keys(), label='Truncating namespaces') as bar:
            for namespace in bar:
                try:
                    vector_db.index.delete(delete_all=True, namespace=namespace)
                    click.echo(f"Deleted all vectors in namespace: {namespace}")
                except Exception as e:
                    click.echo(f"Error deleting namespace {namespace}: {str(e)}", err=True)
        
        # Verify the index is empty
        new_stats = vector_db.index.describe_index_stats()
        new_vector_count = new_stats.get('total_vector_count', 0)
        
        if new_vector_count == 0:
            click.echo("✅ Successfully truncated the index. The index is now empty.")
        else:
            click.echo(f"⚠️ Index truncation may be incomplete. There are still {new_vector_count} vectors in the index.")
        
    except Exception as e:
        click.echo(f"Error truncating index: {str(e)}", err=True)
        sys.exit(1)

@pinecone_group.command('upload')
@click.option('--index-name', required=True, help='Name of the Pinecone index to upload to')
@click.option('--source-dir', required=True, help='Source directory containing documents to upload')
@click.option('--category', required=True, help='Category to assign to the documents')
@click.option('--chunk-size', type=int, default=600, help='Size of text chunks')
@click.option('--chunk-overlap', type=int, default=250, help='Overlap between chunks')
@click.option('--parallel/--no-parallel', default=False, help='Use parallel processing')
@click.option('--workers', type=int, default=4, help='Number of parallel workers')
def pinecone_upload(index_name: str, source_dir: str, category: str, chunk_size: int, chunk_overlap: int, 
                    parallel: bool, workers: int):
    """Upload documents to a Pinecone index with custom chunking parameters."""
    from app.services.file_processor import FileProcessor
    from app.services.vector_store_manager import vector_store_manager
    from app.db.vector_db import vector_db
    from app.core.config import settings
    import glob
    
    click.echo(f"Uploading documents from {source_dir}/{category} to Pinecone index {index_name}")
    click.echo(f"Using chunk size: {chunk_size}, chunk overlap: {chunk_overlap}")
    
    try:
        # Verify the index name
        if settings.PINECONE_INDEX_NAME != index_name:
            click.echo(f"Warning: The specified index ({index_name}) does not match the configured index ({settings.PINECONE_INDEX_NAME})")
            if not click.confirm("Do you want to continue anyway?"):
                click.echo("Operation cancelled.")
                return
        
        # Initialize Vector-DB
        vector_db.init_pinecone()
        
        # Construct the specific category directory path
        category_dir = os.path.join(source_dir, category)
        
        # Validate category directory
        if not os.path.isdir(category_dir):
            click.echo(f"Error: Category directory does not exist: {category_dir}", err=True)
            sys.exit(1)
        
        # Find all text files in the specific category directory (non-recursive)
        text_files = glob.glob(os.path.join(category_dir, "*.txt"))
        
        if not text_files:
            click.echo(f"Error: No text files found in {category_dir}", err=True)
            sys.exit(1)
        
        click.echo(f"Found {len(text_files)} text files to process in category '{category}'")
        
        # Create custom file processor with specified chunk size
        custom_processor = FileProcessor(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        
        # Process files
        documents = []
        for file_path in tqdm(text_files, desc="Processing files"):
            try:
                # Extract filename without path
                filename = os.path.basename(file_path)
                
                # Extract metadata (author and title) from filename if possible
                author = ""
                title = filename
                if "#" in filename:
                    parts = filename.split("#", 1)
                    author = parts[0]
                    title = parts[1].replace(".txt", "")
                
                # Create file_info dictionary needed by processor
                file_info = {
                    "path": file_path,
                    "filename": filename,
                    "extension": ".txt",
                    "metadata": {
                        "filename": filename,
                        "author": author,
                        "title": title,
                        "category": category,
                        "document_id": str(uuid.uuid4())  # Generate a unique ID
                    }
                }
                
                # Process the file using the custom processor
                processed_doc = custom_processor.process_file(file_info)
                
                if processed_doc and "chunks" in processed_doc:
                    documents.append(processed_doc)
                    
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        if not documents:
            click.echo("No documents were successfully processed.")
            return
        
        click.echo(f"Successfully processed {len(documents)} documents")
        
        # Upload to vector store
        try:
            click.echo(f"Uploading documents to Pinecone...")
            
            if parallel:
                stats = vector_store_manager.upsert_category_parallel(
                    category, 
                    documents,
                    max_workers=workers
                )
            else:
                stats = vector_store_manager.upsert_category(category, documents)
            
            click.echo(f"Upload complete: {stats['successful']} documents successful, {stats['failed']} documents failed")
            
        except Exception as e:
            logger.error(f"Error uploading documents: {str(e)}")
            click.echo(f"Error uploading documents: {str(e)}", err=True)
            sys.exit(1)
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@pinecone_group.command('stats')
@click.option('--index-name', required=True, help='Name of the Pinecone index to get statistics for')
def pinecone_stats(index_name: str):
    """Get statistics about a Pinecone index."""
    from app.db.vector_db import vector_db
    from app.core.config import settings
    
    click.echo(f"Getting statistics for Pinecone index: {index_name}")
    
    try:
        # Verify the index name
        if settings.PINECONE_INDEX_NAME != index_name:
            click.echo(f"Warning: The specified index ({index_name}) does not match the configured index ({settings.PINECONE_INDEX_NAME})")
            if not click.confirm("Do you want to continue anyway?"):
                click.echo("Operation cancelled.")
                return
        
        # Initialize Vector-DB
        vector_db.init_pinecone()
        
        # Get index statistics
        stats = vector_db.index.describe_index_stats()
        
        # Display statistics
        click.echo("\nIndex Statistics:")
        click.echo(f"Total Vector Count: {stats.get('total_vector_count', 0)}")
        click.echo(f"Dimension: {stats.get('dimension', 'Unknown')}")
        
        # Display namespace statistics
        namespaces = stats.get('namespaces', {})
        click.echo(f"\nNamespaces ({len(namespaces)}):")
        
        for namespace, ns_stats in namespaces.items():
            click.echo(f"\n  Namespace: {namespace}")
            click.echo(f"  Vector Count: {ns_stats.get('vector_count', 0)}")
        
        # Save statistics to file
        stats_file = f"logs/pinecone_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        click.echo(f"\nStatistics saved to {stats_file}")
        
    except Exception as e:
        click.echo(f"Error getting statistics: {str(e)}", err=True)
        sys.exit(1)

# Knowledge Base Management Commands
@cli.group('kb')
def kb_group():
    """Knowledge base management commands."""
    pass

@kb_group.command('upload')
@click.option('--source', required=True, help='Path to knowledge base directory')
@click.option('--categories', help='Comma-separated list of categories to upload')
@click.option('--parallel/--no-parallel', default=False, help='Use parallel processing')
@click.option('--workers', type=int, default=4, help='Number of parallel workers')
def kb_upload(source: str, categories: Optional[str], parallel: bool, workers: int):
    """Upload documents to the vector store."""
    from app.services.kb_scanner import kb_scanner
    from app.services.file_processor import file_processor
    from app.services.vector_store_manager import vector_store_manager
    
    click.echo(f"Uploading knowledge base from: {source}")
    
    try:
        # Validate source directory
        if not os.path.isdir(source):
            click.echo(f"Error: Source directory does not exist: {source}", err=True)
            sys.exit(1)
        
        # Scan knowledge base
        click.echo("Scanning knowledge base...")
        categories_dict = kb_scanner.scan_kb(source)
        
        # Filter categories if specified
        if categories:
            category_list = categories.split(',')
            categories_dict = {k: v for k, v in categories_dict.items() if k in category_list}
        
        if not categories_dict:
            click.echo("Error: No categories found or matched", err=True)
            sys.exit(1)
        
        click.echo(f"Found {len(categories_dict)} categories: {', '.join(categories_dict.keys())}")
        
        # Process and upload each category
        upload_stats = []
        
        with click.progressbar(categories_dict.items(), label='Processing categories') as bar:
            for category, files in bar:
                click.echo(f"\nProcessing category: {category} with {len(files)} files")
                
                # Process files
                documents = []
                for file_info in files:
                    try:
                        doc = file_processor.process_file(file_info)
                        if doc:
                            # Ensure author and title are always strings
                            if "author" not in doc or doc["author"] is None:
                                doc["author"] = ""
                            if "title" not in doc or doc["title"] is None:
                                doc["title"] = ""
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"Error processing file {file_info.get('path')}: {str(e)}")
                
                click.echo(f"Processed {len(documents)} documents for category {category}")
                
                # Upload to vector store
                try:
                    click.echo(f"Uploading category {category} to vector store")
                    
                    if parallel:
                        stats = vector_store_manager.upsert_category_parallel(
                            category, 
                            documents,
                            max_workers=workers
                        )
                    else:
                        stats = vector_store_manager.upsert_category(category, documents)
                        
                    upload_stats.append(stats)
                    click.echo(f"Uploaded category {category}: {stats['successful']} successful, {stats['failed']} failed")
                except Exception as e:
                    logger.error(f"Error uploading category {category}: {str(e)}")
        
        # Save upload stats
        stats_file = f"logs/kb_upload_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(upload_stats, f, indent=2)
        
        click.echo(f"Upload stats saved to {stats_file}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@kb_group.command('update')
@click.option('--source', required=True, help='Path to knowledge base directory')
@click.option('--categories', help='Comma-separated list of categories to update')
@click.option('--delete-existing/--no-delete-existing', default=False, help='Delete existing data before update')
@click.option('--parallel/--no-parallel', default=False, help='Use parallel processing')
@click.option('--workers', type=int, default=4, help='Number of parallel workers')
def kb_update(source: str, categories: Optional[str], delete_existing: bool, parallel: bool, workers: int):
    """Update existing documents in the vector store."""
    from app.services.kb_scanner import kb_scanner
    from app.services.file_processor import file_processor
    from app.services.vector_store_manager import vector_store_manager
    
    click.echo(f"Updating knowledge base from: {source}")
    
    try:
        # Validate source directory
        if not os.path.isdir(source):
            click.echo(f"Error: Source directory does not exist: {source}", err=True)
            sys.exit(1)
        
        # Scan knowledge base
        click.echo("Scanning knowledge base...")
        categories_dict = kb_scanner.scan_kb(source)
        
        # Filter categories if specified
        if categories:
            category_list = categories.split(',')
            categories_dict = {k: v for k, v in categories_dict.items() if k in category_list}
        
        if not categories_dict:
            click.echo("Error: No categories found or matched", err=True)
            sys.exit(1)
        
        click.echo(f"Found {len(categories_dict)} categories: {', '.join(categories_dict.keys())}")
        
        # Process and update each category
        update_stats = []
        
        with click.progressbar(categories_dict.items(), label='Updating categories') as bar:
            for category, files in bar:
                click.echo(f"\nProcessing category: {category} with {len(files)} files")
                
                # Delete existing data if requested
                if delete_existing:
                    click.echo(f"Deleting existing data for category {category}")
                    vector_store_manager.delete_category(category)
                
                # Process files
                documents = []
                for file_info in files:
                    try:
                        doc = file_processor.process_file(file_info)
                        if doc:
                            # Ensure author and title are always strings
                            if "author" not in doc or doc["author"] is None:
                                doc["author"] = ""
                            if "title" not in doc or doc["title"] is None:
                                doc["title"] = ""
                            documents.append(doc)
                    except Exception as e:
                        logger.error(f"Error processing file {file_info.get('path')}: {str(e)}")
                
                click.echo(f"Processed {len(documents)} documents for category {category}")
                
                # Upload to vector store
                try:
                    click.echo(f"Updating category {category} in vector store")
                    
                    if parallel:
                        stats = vector_store_manager.upsert_category_parallel(
                            category, 
                            documents,
                            max_workers=workers
                        )
                    else:
                        stats = vector_store_manager.upsert_category(category, documents)
                        
                    update_stats.append(stats)
                    click.echo(f"Updated category {category}: {stats['successful']} successful, {stats['failed']} failed")
                except Exception as e:
                    logger.error(f"Error updating category {category}: {str(e)}")
        
        # Save update stats
        stats_file = f"logs/kb_update_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(update_stats, f, indent=2)
        
        click.echo(f"Update stats saved to {stats_file}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@kb_group.command('delete')
@click.option('--categories', required=True, help='Comma-separated list of categories to delete')
@click.confirmation_option(prompt='Are you sure you want to delete these categories?')
def kb_delete(categories: str):
    """Delete categories from the vector store."""
    from app.services.vector_store_manager import vector_store_manager
    
    category_list = categories.split(',')
    click.echo(f"Deleting categories: {', '.join(category_list)}")
    
    success_count = 0
    fail_count = 0
    
    for category in category_list:
        try:
            click.echo(f"Deleting category: {category}")
            result = vector_store_manager.delete_category(category)
            if result:
                click.echo(f"Successfully deleted category: {category}")
                success_count += 1
            else:
                click.echo(f"Failed to delete category: {category}", err=True)
                fail_count += 1
        except Exception as e:
            click.echo(f"Error deleting category {category}: {str(e)}", err=True)
            fail_count += 1
    
    click.echo(f"Deletion complete: {success_count} succeeded, {fail_count} failed")

@kb_group.command('reindex')
@click.option('--source', required=True, help='Path to knowledge base directory')
@click.option('--categories', help='Comma-separated list of categories to re-index (default: all)')
@click.option('--batch-size', type=int, default=50, help='Batch size for indexing')
@click.option('--workers', type=int, default=4, help='Number of parallel workers')
@click.option('--dry-run/--no-dry-run', default=False, help='Dry run (no actual indexing)')
@click.option('--delete-existing/--no-delete-existing', default=False, help='Delete existing data before re-indexing')
@click.option('--check-only/--no-check-only', default=False, help='Only check settings and exit')
def kb_reindex(source: str, categories: Optional[str], batch_size: int, workers: int, 
              dry_run: bool, delete_existing: bool, check_only: bool):
    """Re-index documents with a new embedding model."""
    from app.services.kb_scanner import kb_scanner
    from app.services.file_processor import file_processor
    from app.services.vector_store_manager import vector_store_manager
    from app.services.embedding_service import embedding_service
    from app.db.vector_db import vector_db
    from app.core.config import settings
    
    # Function to verify settings
    def verify_settings():
        """Verify that the necessary settings are configured correctly."""
        required_settings = [
            ("PINECONE_API_KEY", settings.PINECONE_API_KEY),
            ("PINECONE_INDEX_NAME", settings.PINECONE_INDEX_NAME),
            ("PINECONE_HOST", settings.PINECONE_HOST),
            ("EMBEDDINGS_MODEL", settings.EMBEDDINGS_MODEL),
            ("EMBEDDINGS_DIMENSION", settings.EMBEDDINGS_DIMENSION),
            ("LOCAL_EMBEDDING_SERVICE_URL", settings.LOCAL_EMBEDDING_SERVICE_URL)
        ]
        
        all_set = True
        for name, value in required_settings:
            if not value:
                click.echo(f"Error: {name} is not set. Please configure it in your .env file.", err=True)
                all_set = False
        
        return all_set
    
    # Function to reindex a specific category
    def reindex_category(category: str):
        """Reindex a specific category."""
        click.echo(f"Re-indexing category: {category}")
        
        # Scan the category directory
        category_path = os.path.join(source, category)
        if not os.path.isdir(category_path):
            click.echo(f"Error: Category directory does not exist: {category_path}", err=True)
            return {"category": category, "status": "error", "message": "Directory not found"}
        
        # Get all files in the category
        files = kb_scanner._scan_category(category_path, category)
        click.echo(f"Found {len(files)} files in category {category}")
        
        if dry_run:
            click.echo(f"DRY RUN: Would process {len(files)} files for category {category}")
            return {"category": category, "status": "dry_run", "file_count": len(files)}
        
        # Delete existing data if requested
        if delete_existing:
            click.echo(f"Deleting existing data for category {category}")
            vector_store_manager.delete_category(category)
        
        # Process files
        documents = []
        failed_files = []
        
        with click.progressbar(files, label=f"Processing {category} files") as bar:
            for file_info in bar:
                try:
                    doc = file_processor.process_file(file_info)
                    if doc:
                        # Ensure author and title are always strings
                        if "author" not in doc or doc["author"] is None:
                            doc["author"] = ""
                        if "title" not in doc or doc["title"] is None:
                            doc["title"] = ""
                        documents.append(doc)
                except Exception as e:
                    logger.error(f"Error processing file {file_info.get('path')}: {str(e)}")
                    failed_files.append(file_info.get('path'))
        
        click.echo(f"Processed {len(documents)} documents for category {category}")
        
        # Upload to vector store
        try:
            click.echo(f"Uploading {len(documents)} documents for category {category} to vector store")
            
            # Process in batches to avoid overwhelming the embedding service
            batch_count = (len(documents) + batch_size - 1) // batch_size
            successful = 0
            failed = 0
            
            with click.progressbar(range(batch_count), label=f"Uploading {category} batches") as bar:
                for i in bar:
                    batch = documents[i*batch_size:(i+1)*batch_size]
                    
                    try:
                        if len(batch) > 0:
                            result = vector_store_manager.upsert_category(category, batch)
                            successful += result.get('successful', 0)
                            failed += result.get('failed', 0)
                            
                            # Sleep briefly to avoid overwhelming the embedding service
                            time.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Error uploading batch {i} for category {category}: {str(e)}")
                        failed += len(batch)
            
            return {
                "category": category,
                "status": "completed",
                "total_documents": len(documents),
                "successful": successful,
                "failed": failed,
                "failed_files": failed_files
            }
        except Exception as e:
            logger.error(f"Error uploading category {category}: {str(e)}")
            return {
                "category": category,
                "status": "error",
                "message": str(e),
                "failed_files": failed_files
            }
    
    try:
        # Verify settings
        click.echo("Verifying settings...")
        if not verify_settings():
            click.echo("Settings verification failed. Please fix the issues above.", err=True)
            if not check_only:
                sys.exit(1)
        else:
            click.echo("Settings verification passed.")
        
        if check_only:
            click.echo("Check only mode, exiting.")
            return
        
        # Validate source directory
        if not os.path.isdir(source):
            click.echo(f"Error: Source directory does not exist: {source}", err=True)
            sys.exit(1)
        
        # Scan knowledge base
        click.echo(f"Scanning knowledge base: {source}")
        all_categories = kb_scanner.scan_kb(source)
        
        # Filter categories if specified
        if categories:
            category_list = categories.split(',')
            all_categories = {k: v for k, v in all_categories.items() if k in category_list}
        
        if not all_categories:
            click.echo("Error: No categories found or matched", err=True)
            sys.exit(1)
        
        click.echo(f"Found {len(all_categories)} categories: {', '.join(all_categories.keys())}")
        
        start_time = time.time()
        results = []
        
        # Process each category
        for category in all_categories.keys():
            result = reindex_category(category)
            results.append(result)
        
        # Calculate total time
        total_time = time.time() - start_time
        
        # Save results
        result_data = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": total_time,
            "settings": {
                "source_dir": source,
                "batch_size": batch_size,
                "workers": workers,
                "dry_run": dry_run,
                "delete_existing": delete_existing
            },
            "embedding_model": settings.EMBEDDINGS_MODEL,
            "embedding_dimension": settings.EMBEDDINGS_DIMENSION,
            "index_name": settings.PINECONE_INDEX_NAME,
            "category_results": results
        }
        
        results_file = f"logs/reindex_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        click.echo(f"Re-indexing completed in {total_time:.2f} seconds. Results saved to {results_file}")
        
        # Print summary
        successful_categories = sum(1 for r in results if r.get("status") == "completed")
        total_documents = sum(r.get("total_documents", 0) for r in results if r.get("status") == "completed")
        total_successful = sum(r.get("successful", 0) for r in results if r.get("status") == "completed")
        total_failed = sum(r.get("failed", 0) for r in results if r.get("status") == "completed")
        
        click.echo(f"Summary: {successful_categories}/{len(results)} categories processed successfully")
        click.echo(f"Total documents: {total_documents}")
        click.echo(f"Successfully indexed: {total_successful}")
        click.echo(f"Failed to index: {total_failed}")
        
    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        sys.exit(1)

@kb_group.command('stats')
@click.option('--categories', help='Comma-separated list of categories to get statistics for')
def kb_stats(categories: Optional[str]):
    """Get statistics about indexed content."""
    from app.services.vector_store_manager import vector_store_manager
    
    try:
        # Get categories to check
        category_list = categories.split(',') if categories else None
        
        if category_list:
            click.echo(f"Getting statistics for categories: {', '.join(category_list)}")
            stats = []
            
            with click.progressbar(category_list, label='Fetching stats') as bar:
                for category in bar:
                    cat_stats = vector_store_manager.get_category_stats(category)
                    stats.append(cat_stats)
                    click.echo(f"\nCategory {category}: {cat_stats['document_count']} documents, {cat_stats['chunk_count']} chunks")
        else:
            click.echo("Getting statistics for all categories")
            # TODO: Implement getting all categories from vector store
            click.echo("Getting stats for all categories is not yet implemented")
            stats = []
        
        # Save stats
        stats_file = f"logs/kb_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        click.echo(f"Statistics saved to {stats_file}")
        
    except Exception as e:
        click.echo(f"Error getting statistics: {str(e)}", err=True)
        sys.exit(1)

# Search and Query Commands
@cli.group('search')
def search_group():
    """Search and query commands."""
    pass

@search_group.command('query')
@click.argument('query_text')
@click.option('--category', help='Category filter')
@click.option('--top-k', type=int, default=5, help='Number of results to return')
@click.option('--alpha', type=float, default=0.5, help='Weight for dense vectors (0-1)')
def search_query(query_text: str, category: Optional[str], top_k: int, alpha: float):
    """Perform a search query."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    try:
        # Initialize Vector-DB
        vector_db.init_pinecone()
        
        # Prepare filter if category is provided
        filter_dict = {"category": category} if category else None
        
        click.echo(f"Searching for: '{query_text}'")
        if category:
            click.echo(f"With category filter: {category}")
        
        # Perform search
        results = rag_service.query(
            query_text=query_text,
            filter=filter_dict,
            top_k=top_k
        )
        
        # Display results
        click.echo(f"\nFound {len(results)} results:")
        
        for i, result in enumerate(results):
            click.echo(f"\n--- Result {i+1} ---")
            click.echo(f"Score: {result.get('score', 0):.4f}")
            
            metadata = result.get('metadata', {})
            if metadata:
                click.echo("Metadata:")
                for key, value in metadata.items():
                    if key in ['filename', 'title', 'author', 'category']:
                        click.echo(f"  {key}: {value}")
            
            # Show text preview
            text = result.get('text', '')
            preview = text[:200] + "..." if len(text) > 200 else text
            click.echo(f"\nPreview: {preview}")
        
    except Exception as e:
        click.echo(f"Error performing search: {str(e)}", err=True)
        sys.exit(1)

# Diagnostics and Reporting Commands
@cli.group('diagnostics')
def diagnostics_group():
    """Diagnostics and reporting commands."""
    pass

@diagnostics_group.command('list-documents')
@click.option('--output-dir', default="results", help='Directory to save results')
def list_documents(output_dir: str):
    """List all indexed documents and their metadata."""
    click.echo("Listing all indexed documents...")
    
    try:
        # Import from local directory
        from scripts.rag_cli.list_indexed_books import list_indexed_books
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run the list_indexed_books function
        success = list_indexed_books(output_dir)
        
        if success:
            click.echo(f"Document listing complete. Results saved to {output_dir}/indexed_books.txt")
        else:
            click.echo("Failed to list documents", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error listing documents: {str(e)}", err=True)
        sys.exit(1)

@diagnostics_group.command('validate-settings')
def validate_settings():
    """Verify configuration settings."""
    from app.core.config import settings
    
    click.echo("Validating configuration settings...")
    
    # Check essential settings
    essential_settings = [
        ("PINECONE_API_KEY", settings.PINECONE_API_KEY),
        ("PINECONE_INDEX_NAME", settings.PINECONE_INDEX_NAME),
        ("PINECONE_HOST", settings.PINECONE_HOST),
        ("EMBEDDINGS_MODEL", settings.EMBEDDINGS_MODEL),
        ("EMBEDDINGS_DIMENSION", settings.EMBEDDINGS_DIMENSION),
    ]
    
    all_valid = True
    
    click.echo("\nEssential Settings:")
    for name, value in essential_settings:
        if value:
            click.echo(f"✅ {name} is set")
        else:
            click.echo(f"❌ {name} is not set")
            all_valid = False
    
    # Check optional settings
    optional_settings = [
        ("OPENAI_API_KEY", getattr(settings, "OPENAI_API_KEY", None)),
        ("ANTHROPIC_API_KEY", getattr(settings, "ANTHROPIC_API_KEY", None)),
        ("DEEPSEEK_API_KEY", getattr(settings, "DEEPSEEK_API_KEY", None)),
        ("LOCAL_EMBEDDING_SERVICE_URL", getattr(settings, "LOCAL_EMBEDDING_SERVICE_URL", None)),
    ]
    
    click.echo("\nOptional Settings:")
    for name, value in optional_settings:
        if value:
            click.echo(f"✅ {name} is set")
        else:
            click.echo(f"ℹ️ {name} is not set")
    
    if all_valid:
        click.echo("\n✅ All essential settings are valid")
    else:
        click.echo("\n❌ Some essential settings are missing")
        sys.exit(1)

@diagnostics_group.command('diagnose-retrieval')
@click.option('--query', default="Welches sind die 12 Weltanschauungen?", 
              help='Query text to diagnose')
@click.option('--expected-doc', 
              default="Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
              help='Expected document ID')
@click.option('--category', default="Realismus", help='Category to filter by')
@click.option('--top-k', type=int, default=20, help='Number of results to return')
@click.option('--output-dir', default="results", help='Directory to save results')
def diagnose_retrieval(query: str, expected_doc: str, category: str, top_k: int, output_dir: str):
    """Run diagnostics on the retrieval system."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Diagnose-Datei
    diagnose_file = os.path.join(output_dir, f"rag_diagnose_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
    
    click.echo(f"Running retrieval diagnostics for query: '{query}'")
    click.echo(f"Expected document: '{expected_doc}'")
    
    try:
        # Initialisiere Vector-Datenbank
        vector_db.init_pinecone()
        
        # 1. Test ohne Filter
        click.echo("Test 1: Searching without filter...")
        results_without_filter = rag_service.query(
            query_text=query,
            filter=None,
            top_k=top_k
        )
        
        # 2. Test mit Filter
        filter_dict = {"category": category} if category else None
        if filter_dict:
            click.echo(f"Test 2: Searching with category filter: {category}...")
            results_with_filter = rag_service.query(
                query_text=query,
                filter=filter_dict,
                top_k=top_k
            )
        else:
            results_with_filter = []
        
        # 3. Direkte Suche nach dem erwarteten Dokument (falls möglich)
        click.echo("Test 3: Directly searching for the expected document...")
        try:
            # Search with a high top_k to try to find the document
            direct_results = rag_service.query(
                query_text=expected_doc.replace("#", " "),
                filter=None,
                top_k=100
            )
            expected_doc_exists = False
            expected_doc_data = None
            
            for result in direct_results:
                metadata = result.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc in filename:
                    expected_doc_exists = True
                    expected_doc_data = result
                    break
        except Exception as e:
            logger.warning(f"Could not directly search for document ID: {str(e)}")
            expected_doc_exists = "Unknown"
            expected_doc_data = None
        
        # Ergebnisse in Datei schreiben
        with open(diagnose_file, "w", encoding="utf-8") as f:
            f.write(f"# RAG Retrieval Diagnostics Report\n\n")
            f.write(f"*Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
            f.write(f"## Query\n`{query}`\n\n")
            f.write(f"## Expected Document\n`{expected_doc}`\n\n")
            
            # Existenz des erwarteten Dokuments
            f.write(f"## Expected Document Existence\n")
            f.write(f"- Document exists in index: {expected_doc_exists}\n\n")
            
            if expected_doc_data:
                f.write("### Metadata of Expected Document\n")
                metadata = expected_doc_data.get('metadata', {})
                for key, value in metadata.items():
                    f.write(f"- **{key}:** {value}\n")
                f.write("\n")
            
            # Test 1: Ergebnisse ohne Filter
            f.write(f"## Test 1: Search Without Filter (Top-{top_k})\n\n")
            
            # Prüfen, ob das erwartete Dokument in den Ergebnissen ist
            found_at_position = None
            for i, result in enumerate(results_without_filter):
                metadata = result.get('metadata', {})
                filename = metadata.get('filename', '')
                if expected_doc in filename:
                    found_at_position = i + 1
                    break
            
            if found_at_position:
                f.write(f"✅ Expected document found at position {found_at_position} of {len(results_without_filter)}\n\n")
            else:
                f.write(f"❌ Expected document NOT found in the top {top_k} results\n\n")
            
            # Top-5 Ergebnisse ohne Filter
            f.write("### Top Results Without Filter\n\n")
            for i, result in enumerate(results_without_filter[:5]):
                f.write(f"#### Result {i+1}\n\n")
                f.write(f"- **Relevance:** {result.get('score', 0):.4f}\n")
                
                metadata = result.get('metadata', {})
                filename = metadata.get('filename', 'No filename available')
                title = metadata.get('title', 'No title available')
                result_category = metadata.get('category', 'No category available')
                
                f.write(f"- **Filename:** {filename}\n")
                f.write(f"- **Title:** {title}\n")
                f.write(f"- **Category:** {result_category}\n")
                
                # Hervorheben, wenn es das erwartete Dokument ist
                if expected_doc in filename:
                    f.write(f"- **⭐ EXPECTED DOCUMENT ⭐**\n")
                
                # Textauszug
                text = result.get('text', '')[:200]
                f.write(f"- **Text Preview:** {text}...\n\n")
            
            # Test 2: Ergebnisse mit Filter
            if filter_dict:
                f.write(f"## Test 2: Search With Filter {filter_dict} (Top-{top_k})\n\n")
                
                # Prüfen, ob das erwartete Dokument in den Ergebnissen ist
                found_at_position = None
                for i, result in enumerate(results_with_filter):
                    metadata = result.get('metadata', {})
                    filename = metadata.get('filename', '')
                    if expected_doc in filename:
                        found_at_position = i + 1
                        break
                
                if found_at_position:
                    f.write(f"✅ Expected document found at position {found_at_position} of {len(results_with_filter)}\n\n")
                else:
                    f.write(f"❌ Expected document NOT found in the top {top_k} results\n\n")
                
                # Top-5 Ergebnisse mit Filter
                f.write("### Top Results With Filter\n\n")
                for i, result in enumerate(results_with_filter[:5]):
                    f.write(f"#### Result {i+1}\n\n")
                    f.write(f"- **Relevance:** {result.get('score', 0):.4f}\n")
                    
                    metadata = result.get('metadata', {})
                    filename = metadata.get('filename', 'No filename available')
                    title = metadata.get('title', 'No title available')
                    result_category = metadata.get('category', 'No category available')
                    
                    f.write(f"- **Filename:** {filename}\n")
                    f.write(f"- **Title:** {title}\n")
                    f.write(f"- **Category:** {result_category}\n")
                    
                    # Hervorheben, wenn es das erwartete Dokument ist
                    if expected_doc in filename:
                        f.write(f"- **⭐ EXPECTED DOCUMENT ⭐**\n")
                    
                    # Textauszug
                    text = result.get('text', '')[:200]
                    f.write(f"- **Text Preview:** {text}...\n\n")
            
            # Diagnostic Conclusions
            f.write("## Diagnostic Conclusions\n\n")
            
            if expected_doc_exists == "Unknown":
                f.write("- The existence of the expected document in the index could not be determined.\n")
            elif not expected_doc_exists:
                f.write("- ❌ The expected document does not exist in the index. This explains why it cannot be found in search results.\n")
                f.write("  - **Action:** Upload the document to the vector store.\n")
            
            if expected_doc_data:
                doc_category = expected_doc_data.get('metadata', {}).get('category', None)
                if doc_category != category:
                    f.write(f"- ❌ The expected document has category '{doc_category}', not '{category}'. This explains the filter effect.\n")
                    f.write(f"  - **Action:** Update the document metadata or adjust your filter.\n")
            
            if found_at_position and found_at_position > 5:
                f.write(f"- ⚠️ The expected document was found, but only at position {found_at_position}. The top-k value in production code might be too low.\n")
                f.write(f"  - **Action:** Consider increasing the top-k value or improving the query formulation.\n")
            
            if not found_at_position and expected_doc_exists:
                f.write("- ❌ The expected document was not found in any search results. Possible reasons:\n")
                f.write("  - The embedding quality is suboptimal\n")
                f.write("  - The chunks might be poorly segmented\n")
                f.write("  - The query might need reformulation\n")
                f.write("  - **Action:** Try query variations, adjust chunking parameters, or consider a different embedding model.\n")
            
            # Overall recommendation
            f.write("\n## Recommended Next Steps\n\n")
            
            if not expected_doc_exists:
                f.write("1. Upload the expected document to the vector store\n")
            elif expected_doc_data and expected_doc_data.get('metadata', {}).get('category', None) != category:
                f.write(f"1. Adjust the filter to include category '{expected_doc_data.get('metadata', {}).get('category', 'Unknown')}'\n")
            elif not found_at_position:
                f.write("1. Try different query formulations\n")
                f.write("2. Check document chunking parameters\n")
                f.write("3. Consider re-indexing with a different embedding model\n")
            else:
                f.write("1. Increase the top-k parameter in your production code\n")
                f.write("2. Refine the query to improve the ranking of the expected document\n")
        
        click.echo(f"Diagnostics complete. Results saved to: {diagnose_file}")
        
        # Print a brief summary to the console
        click.echo("\nSummary:")
        if expected_doc_exists == True:
            click.echo("✅ Expected document exists in the index")
        elif expected_doc_exists == False:
            click.echo("❌ Expected document does NOT exist in the index")
        else:
            click.echo("⚠️ Could not determine if expected document exists")
        
        if found_at_position:
            click.echo(f"✅ Expected document found at position {found_at_position} without filter")
        else:
            click.echo("❌ Expected document NOT found without filter")
        
        if filter_dict:
            filter_found = any(expected_doc in result.get('metadata', {}).get('filename', '') 
                             for result in results_with_filter)
            if filter_found:
                click.echo(f"✅ Expected document found with filter: {filter_dict}")
            else:
                click.echo(f"❌ Expected document NOT found with filter: {filter_dict}")
        
    except Exception as e:
        click.echo(f"Error during diagnostics: {str(e)}", err=True)
        logger.error(f"Diagnostics failed: {str(e)}")
        sys.exit(1)

@diagnostics_group.command('check-document')
@click.option('--document-id', default="Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
              help='Document ID to check')
@click.option('--expected-category', default="Realismus", help='Expected category')
@click.option('--output-dir', default="results", help='Directory to save results')
def check_document(document_id: str, expected_category: str, output_dir: str):
    """Verify specific document attributes and category assignment."""
    click.echo(f"Checking document: {document_id}")
    click.echo(f"Expected category: {expected_category}")
    
    try:
        # Import from local directory
        from scripts.rag_cli.check_document_category import check_document_category
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Run the check_document_category function
        success = check_document_category(
            expected_doc_id=document_id,
            expected_category=expected_category,
            output_dir=output_dir
        )
        
        if success:
            click.echo(f"Document check complete. Results saved to {output_dir}/kategorie_pruefung.txt")
        else:
            click.echo("Failed to check document", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"Error checking document: {str(e)}", err=True)
        sys.exit(1)

@diagnostics_group.command('check-document-improved')
@click.option('--document-id', default="Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151]",
              help='Document ID to check')
@click.option('--expected-category', default="Realismus", help='Expected category')
@click.option('--query-match', is_flag=True, default=False, help='Use query matching instead of exact ID match')
@click.option('--output-dir', default="results", help='Directory to save results')
def check_document_improved(document_id: str, expected_category: str, query_match: bool, output_dir: str):
    """
    Improved document check that uses direct search to reliably find documents.
    Addresses the issue with the original check-document command.
    """
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    from datetime import datetime
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "document_check_improved.md")
    
    click.echo(f"Checking document: {document_id}")
    click.echo(f"Expected category: {expected_category}")
    
    try:
        # Connect to vector store
        if not vector_db.initialized:
            vector_db.init_pinecone()
        
        # Handle .txt extension - try both with and without .txt
        document_id_with_txt = document_id
        if not document_id.endswith('.txt'):
            document_id_with_txt = document_id + '.txt'
        document_id_without_txt = document_id
        if document_id.endswith('.txt'):
            document_id_without_txt = document_id[:-4]
        
        # Strategy 1: Use direct query to search for the document
        search_query = document_id.replace("#", " ")  # Convert ID to search terms
        results_unfiltered = rag_service.query(
            query_text=search_query if query_match else document_id,
            filter=None,  # No filter to get all possible matches
            top_k=20  # Higher number to ensure we find it
        )
        
        # Extract documents that match our target (check both with and without .txt)
        matching_docs = []
        for item in results_unfiltered:
            metadata = item.get('metadata', {})
            filename = metadata.get('filename', '')
            if document_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                matching_docs.append(item)
        
        # Strategy 2: Try direct search with filter
        results_filtered = rag_service.query(
            query_text=search_query if query_match else document_id,
            filter={"category": expected_category},
            top_k=20
        )
        
        # Extract filtered documents that match our target
        matching_filtered_docs = []
        for item in results_filtered:
            metadata = item.get('metadata', {})
            filename = metadata.get('filename', '')
            if document_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                matching_filtered_docs.append(item)
        
        # Strategy 3: Try getting all documents and searching for matches
        # This is a more comprehensive approach for when the first strategies fail
        click.echo("Performing comprehensive document search...")
        try:
            import pinecone
            from app.core.config import settings
            
            all_matching_docs = []
            batch_size = 1000
            
            # Get the total number of vectors
            stats = vector_db.index.describe_index_stats()
            total_vectors = stats.get('total_vector_count', 0)
            
            if total_vectors > 0:
                # Sample query vector (since we need one for the query)
                sample_vector = rag_service.embedding_service.get_embeddings("sample query for comprehensive search").tolist()
                
                # Fetch vectors in batches
                for i in range(0, min(10000, total_vectors), batch_size):
                    query_result = vector_db.index.query(
                        vector=sample_vector,
                        top_k=batch_size,
                        include_values=False,
                        include_metadata=True,
                        offset=i
                    )
                    
                    # Check each result for our document ID
                    for match in query_result.matches:
                        metadata = match.metadata
                        filename = metadata.get('filename', '')
                        if document_id in filename or document_id_with_txt in filename or document_id_without_txt in filename:
                            all_matching_docs.append({
                                "id": match.id,
                                "score": match.score,
                                "text": metadata.get("text", ""),
                                "metadata": {k: v for k, v in metadata.items() if k != "text"}
                            })
            
            if all_matching_docs and not matching_docs:
                matching_docs = all_matching_docs
                click.echo(f"Found {len(matching_docs)} matches using comprehensive search")
        except Exception as e:
            click.echo(f"Comprehensive search failed: {str(e)}")
        
        # Generate report
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Improved Document Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Target Document\n")
            f.write(f"`{document_id}`\n\n")
            f.write(f"## Expected Category\n")
            f.write(f"`{expected_category}`\n\n")
            
            # Document existence check
            f.write(f"## Document Existence Check\n")
            if matching_docs:
                f.write(f"✅ **Document FOUND in the index!**\n\n")
                f.write(f"Found {len(matching_docs)} matching document chunks.\n\n")
            else:
                f.write(f"❌ **Document was NOT found in the index!**\n\n")
            
            # Category check
            if matching_docs:
                found_categories = set()
                for doc in matching_docs:
                    category = doc.get('metadata', {}).get('category', 'Unknown')
                    found_categories.add(category)
                
                f.write(f"## Category Check\n")
                f.write(f"Found categories: {', '.join(found_categories)}\n\n")
                
                if expected_category in found_categories:
                    f.write(f"✅ **Document HAS the expected category `{expected_category}`**\n\n")
                else:
                    f.write(f"❌ **Document does NOT have the expected category `{expected_category}`**\n\n")
                
                # Check results with filter
                f.write(f"## Filter Check\n")
                if matching_filtered_docs:
                    f.write(f"✅ **Document is retrievable when filtering by category `{expected_category}`**\n\n")
                    f.write(f"Found {len(matching_filtered_docs)} matching chunks with filter.\n\n")
                else:
                    f.write(f"❌ **Document is NOT retrievable when filtering by category `{expected_category}`**\n\n")
                
                # Display metadata from first matching document
                if matching_docs:
                    first_doc = matching_docs[0]
                    f.write(f"## Sample Document Metadata\n")
                    for key, value in first_doc.get('metadata', {}).items():
                        f.write(f"- **{key}:** {value}\n")
                    f.write("\n")
                    
                    # Display text preview
                    text = first_doc.get('text', '')
                    if text:
                        f.write(f"## Text Preview\n")
                        f.write(f"```\n{text[:500]}...\n```\n\n")
            
            # Conclusion
            f.write(f"## Conclusion\n")
            if matching_docs and expected_category in found_categories:
                f.write(f"✅ **Document exists and has the expected category.**\n")
            elif matching_docs:
                f.write(f"⚠️ **Document exists but has category(s) `{', '.join(found_categories)}` instead of expected `{expected_category}`.**\n")
            else:
                f.write(f"❌ **Document was not found in the vector store.**\n")
                
            # Diagnostic information
            f.write(f"\n## Diagnostic Information\n")
            f.write(f"- Document ID: `{document_id}`\n")
            f.write(f"- With .txt: `{document_id_with_txt}`\n")
            f.write(f"- Without .txt: `{document_id_without_txt}`\n")
            f.write(f"- Search query: `{search_query}`\n")
            f.write(f"- Query match enabled: `{query_match}`\n")
            f.write(f"- Expected category: `{expected_category}`\n")
        
        click.echo(f"Check completed. Results saved to {log_file}")
        if matching_docs:
            click.echo(f"✅ Document found with {len(matching_docs)} chunks")
            categories = ", ".join(set(doc.get('metadata', {}).get('category', 'Unknown') for doc in matching_docs))
            click.echo(f"Categories: {categories}")
            return True
        else:
            click.echo("❌ Document not found in the index")
            return False
    
    except Exception as e:
        click.echo(f"Error checking document: {str(e)}", err=True)
        with open(log_file, "w", encoding="utf-8") as f:
            f.write(f"# Error in Document Check\n\n")
            f.write(f"Error: {str(e)}\n")
        return False

@diagnostics_group.command('generate-report')
@click.option('--output-dir', default="results", help='Directory to save report')
@click.option('--format', type=click.Choice(['text', 'markdown', 'json']), default='markdown',
              help='Report format')
def generate_report(output_dir: str, format: str):
    """Generate a comprehensive analysis report of the RAG system."""
    from app.services.rag_service import rag_service
    from app.db.vector_db import vector_db
    from app.core.config import settings
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = os.path.join(output_dir, f"rag_system_report_{timestamp}.{format}")
    
    click.echo(f"Generating comprehensive RAG system report...")
    
    try:
        # Initialize Vector-DB
        vector_db.init_pinecone()
        
        # Collect system information
        system_info = {
            "timestamp": datetime.now().isoformat(),
            "embeddings_model": settings.EMBEDDINGS_MODEL,
            "embeddings_dimension": settings.EMBEDDINGS_DIMENSION,
            "index_name": settings.PINECONE_INDEX_NAME,
        }
        
        # Try to get index statistics
        try:
            index_stats = vector_db.get_index_stats()
            system_info["index_stats"] = index_stats
        except Exception as e:
            logger.warning(f"Could not get index statistics: {str(e)}")
            system_info["index_stats"] = {"error": str(e)}
        
        # Run sample queries to test system performance
        test_queries = [
            "Welches sind die 12 Weltanschauungen?",
            "Rudolf Steiner Anthroposophie",
            "Materialismus Idealismus Spiritualismus"
        ]
        
        query_results = []
        for query in test_queries:
            click.echo(f"Testing query: {query}")
            try:
                start_time = time.time()
                results = rag_service.query(query_text=query, filter=None, top_k=5)
                query_time = time.time() - start_time
                
                query_results.append({
                    "query": query,
                    "time_seconds": query_time,
                    "result_count": len(results),
                    "top_results": [
                        {
                            "score": r.get("score", 0),
                            "title": r.get("metadata", {}).get("title", "Unknown"),
                            "category": r.get("metadata", {}).get("category", "Unknown"),
                        } for r in results[:3]  # Include top 3 results
                    ]
                })
            except Exception as e:
                logger.error(f"Error testing query '{query}': {str(e)}")
                query_results.append({
                    "query": query,
                    "error": str(e)
                })
        
        system_info["query_tests"] = query_results
        
        # Write the report in the specified format
        if format == 'json':
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(system_info, f, indent=2)
        else:  # text or markdown
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(f"# RAG System Report\n\n" if format == 'markdown' else "RAG SYSTEM REPORT\n\n")
                f.write(f"Generated: {system_info['timestamp']}\n\n")
                
                f.write(f"## System Configuration\n\n" if format == 'markdown' else "SYSTEM CONFIGURATION\n\n")
                f.write(f"- Embeddings Model: {system_info['embeddings_model']}\n")
                f.write(f"- Embeddings Dimension: {system_info['embeddings_dimension']}\n")
                f.write(f"- Index Name: {system_info['index_name']}\n\n")
                
                f.write(f"## Index Statistics\n\n" if format == 'markdown' else "INDEX STATISTICS\n\n")
                if "error" in system_info.get("index_stats", {}):
                    f.write(f"Error retrieving index statistics: {system_info['index_stats']['error']}\n\n")
                else:
                    stats = system_info.get("index_stats", {})
                    for key, value in stats.items():
                        f.write(f"- {key}: {value}\n")
                    f.write("\n")
                
                f.write(f"## Query Performance Tests\n\n" if format == 'markdown' else "QUERY PERFORMANCE TESTS\n\n")
                for i, query_test in enumerate(system_info["query_tests"]):
                    f.write(f"### Query {i+1}: `{query_test['query']}`\n\n" if format == 'markdown' else f"QUERY {i+1}: {query_test['query']}\n\n")
                    
                    if "error" in query_test:
                        f.write(f"Error: {query_test['error']}\n\n")
                        continue
                    
                    f.write(f"- Time: {query_test.get('time_seconds', 0):.4f} seconds\n")
                    f.write(f"- Results: {query_test.get('result_count', 0)}\n\n")
                    
                    f.write(f"#### Top Results:\n\n" if format == 'markdown' else "TOP RESULTS:\n\n")
                    for j, result in enumerate(query_test.get("top_results", [])):
                        f.write(f"{j+1}. {result.get('title', 'Unknown')} (Score: {result.get('score', 0):.4f}, Category: {result.get('category', 'Unknown')})\n")
                    f.write("\n")
                
                f.write(f"## System Health Assessment\n\n" if format == 'markdown' else "SYSTEM HEALTH ASSESSMENT\n\n")
                
                # Calculate average query time
                query_times = [q.get("time_seconds", 0) for q in query_results if "time_seconds" in q]
                avg_time = sum(query_times) / len(query_times) if query_times else 0
                
                if avg_time < 0.5:
                    f.write("✅ Query performance is excellent (< 0.5s)\n")
                elif avg_time < 2.0:
                    f.write("✓ Query performance is good (< 2.0s)\n")
                else:
                    f.write("⚠️ Query performance is slow (> 2.0s), consider optimization\n")
                
                # Check result quality based on scores
                avg_top_score = 0
                score_count = 0
                for q in query_results:
                    if "top_results" in q and q["top_results"]:
                        avg_top_score += q["top_results"][0].get("score", 0)
                        score_count += 1
                
                avg_top_score = avg_top_score / score_count if score_count else 0
                
                if avg_top_score > 0.8:
                    f.write("✅ Result relevance scores are high (> 0.8)\n")
                elif avg_top_score > 0.6:
                    f.write("✓ Result relevance scores are acceptable (> 0.6)\n")
                else:
                    f.write("⚠️ Result relevance scores are low (< 0.6), consider improving embeddings\n")
        
        click.echo(f"Report generation complete. Report saved to: {report_file}")
        
    except Exception as e:
        click.echo(f"Error generating report: {str(e)}", err=True)
        sys.exit(1)

# Assistant Management Commands
@cli.group('assistants')
def assistants_group():
    """Pinecone Assistant management commands."""
    pass

@assistants_group.command('gedanke-umkehren')
@click.argument('weltanschauung')
@click.argument('gedanke')
@click.option('--aspekt', help='Zusätzlicher Aspekt zur Berücksichtigung')
def assistants_gedanke_umkehren(weltanschauung: str, gedanke: str, aspekt: Optional[str]):
    """Philosophische Gedankenfehler mit interaktiver Umformulierung korrigieren."""
    try:
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        
        # Find assistant by worldview (first 4 letters, case insensitive)
        weltanschauung_short = weltanschauung[:4].lower()
        matching_assistant = None
        matching_config = None
        
        for assistant_id, config in manager.assistant_configs.items():
            if config['worldview'][:4].lower() == weltanschauung_short:
                matching_assistant = assistant_id
                matching_config = config
                break
        
        if not matching_assistant:
            click.echo(f"❌ Kein Assistent für Weltanschauung '{weltanschauung}' gefunden.", err=True)
            click.echo("Verfügbare Weltanschauungen:")
            for assistant_id, config in manager.assistant_configs.items():
                click.echo(f"  - {config['worldview']} ({assistant_id})")
            return
        
        click.echo(f"🤖 Verwende Assistent: {matching_config['name']} ({matching_config['worldview']})")
        click.echo(f"💭 Ursprünglicher Gedanke: {gedanke}")
        if aspekt:
            click.echo(f"🎯 Aspekt: {aspekt}")
        
        # Step 1: Reformulate the gedanke first (without aspekt)
        click.echo(f"\n🔄 Schritt 1: Umformulierung des Gedankens...")
        
        reformulate_prompt = f"""Formuliere aus der Sicht deiner Weltanschauung ({matching_config['worldview']}) 3 philosophische Variationen zu folgendem Gedanken:

Gedanke: {gedanke}

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "gedanken_in_weltanschauung": [
        "Erste Variation des Gedankens",
        "Zweite Variation des Gedankens", 
        "Dritte Variation des Gedankens"
    ],
    "gedanke": "{gedanke}"
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
        
        while True:
            reformulate_response = manager.query_assistant(
                assistant_id=matching_assistant,
                user_message=reformulate_prompt,
                use_knowledge_base=True
            )
            
            # Parse reformulation response
            try:
                import re
                json_match = re.search(r'\{.*\}', reformulate_response["message"], re.DOTALL)
                if not json_match:
                    click.echo("❌ Konnte JSON-Antwort nicht parsen.")
                    return
                    
                parsed_reformulation = json.loads(json_match.group())
                reformulations = parsed_reformulation.get('gedanken_in_weltanschauung', [])
                
                if len(reformulations) < 3:
                    click.echo("❌ Nicht genügend Umformulierungen erhalten.")
                    return
                
                # Show options to user
                click.echo(f"\n📝 Umformulierungsoptionen von {matching_config['name']}:")
                click.echo("-" * 60)
                for i, reform in enumerate(reformulations, 1):
                    click.echo(f"{i}. {reform}")
                
                click.echo(f"\n4. Erneut umformulieren")
                click.echo(f"5. Abbrechen")
                
                # Get user choice
                while True:
                    try:
                        choice = click.prompt('Wählen Sie eine Option (1-5)', type=int)
                        if 1 <= choice <= 3:
                            chosen_reformulation = reformulations[choice - 1]
                            break
                        elif choice == 4:
                            click.echo("\n🔄 Erneute Umformulierung...")
                            break
                        elif choice == 5:
                            click.echo("❌ Vorgang abgebrochen.")
                            return
                        else:
                            click.echo("❌ Ungültige Auswahl. Bitte wählen Sie 1-5.")
                    except click.Abort:
                        click.echo("\n❌ Vorgang abgebrochen.")
                        return
                    except (ValueError, TypeError):
                        click.echo("❌ Bitte geben Sie eine Zahl zwischen 1 und 5 ein.")
                
                if 1 <= choice <= 3:
                    break  # Exit the reformulation loop
                    
            except Exception as e:
                click.echo(f"❌ Fehler beim Parsen der Umformulierung: {e}")
                return
        
        # Step 2: Use chosen reformulation for resolve
        click.echo(f"\n✅ Gewählte Umformulierung: {chosen_reformulation}")
        click.echo(f"\n🔄 Schritt 2: Korrektur des Gedankenfehlers...")
        
        while True:
            resolve_prompt = f"""Korrigiere folgenden kulturgewordenen Gedankenfehler:

** {chosen_reformulation} **

{f"Berücksichtige dabei: {aspekt}" if aspekt else ""}

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "gedanke": "300-Wort-Korrektur aus deiner philosophischen Perspektive",
    "gedanke_zusammenfassung": "Kurze Zusammenfassung in 30-35 Worten",
    "gedanke_kind": "Kinderfreundliche Erklärung für 10-Jährige"
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
            
            resolve_response = manager.query_assistant(
                assistant_id=matching_assistant,
                user_message=resolve_prompt,
                use_knowledge_base=True
            )
            
            # Parse resolve response
            try:
                json_match = re.search(r'\{.*\}', resolve_response["message"], re.DOTALL)
                if not json_match:
                    click.echo("❌ Konnte JSON-Antwort nicht parsen.")
                    return
                    
                parsed_resolve = json.loads(json_match.group())
                
                # Display result
                click.echo(f"\n✅ Korrektur von {matching_config['name']} ({matching_config['worldview']}):")
                click.echo("=" * 80)
                click.echo(f"💡 Korrektur: {parsed_resolve.get('gedanke', 'N/A')}")
                click.echo(f"\n📝 Zusammenfassung: {parsed_resolve.get('gedanke_zusammenfassung', 'N/A')}")
                click.echo(f"\n👶 Für Kinder: {parsed_resolve.get('gedanke_kind', 'N/A')}")
                click.echo(f"\n⏱️ Verarbeitungszeit: {resolve_response['processing_time']:.2f}s")
                click.echo(f"💰 Kosten: ${resolve_response['usage']['cost']:.6f}")
                
                # Ask for user decision
                click.echo(f"\n" + "=" * 80)
                click.echo("Was möchten Sie tun?")
                click.echo("1. Ergebnis akzeptieren und speichern")
                click.echo("2. Ergebnis ablehnen")
                click.echo("3. Aspekt hinzufügen/ändern")
                
                while True:
                    try:
                        decision = click.prompt('Wählen Sie eine Option (1-3)', type=int)
                        if decision == 1:
                            # Save to file
                            result_data = {
                                "timestamp": datetime.now().isoformat(),
                                "urspruenglicher_gedanke": gedanke,
                                "gewaehlte_umformulierung": chosen_reformulation,
                                "weltanschauung": matching_config['worldview'],
                                "assistent": matching_config['name'],
                                "aspekt": aspekt,
                                "korrektur": parsed_resolve,
                                "verarbeitungszeit": resolve_response['processing_time'],
                                "kosten": resolve_response['usage']['cost']
                            }
                            
                            with open('tmp-gedanke.json', 'w', encoding='utf-8') as f:
                                json.dump(result_data, f, indent=2, ensure_ascii=False)
                            
                            click.echo(f"\n💾 Ergebnis wurde in 'tmp-gedanke.json' gespeichert.")
                            click.echo("✅ Vorgang erfolgreich abgeschlossen.")
                            return
                            
                        elif decision == 2:
                            click.echo("❌ Ergebnis abgelehnt. Vorgang beendet.")
                            return
                            
                        elif decision == 3:
                            new_aspekt = click.prompt('Neuen Aspekt eingeben (oder Enter für leeren Aspekt)', default='', show_default=False)
                            aspekt = new_aspekt if new_aspekt.strip() else None
                            click.echo(f"\n🔄 Wiederhole Korrektur mit {'neuem' if aspekt else 'ohne'} Aspekt...")
                            if aspekt:
                                click.echo(f"🎯 Neuer Aspekt: {aspekt}")
                            break  # Exit decision loop to retry resolve
                            
                        else:
                            click.echo("❌ Ungültige Auswahl. Bitte wählen Sie 1-3.")
                    except click.Abort:
                        click.echo("\n❌ Vorgang abgebrochen.")
                        return
                    except (ValueError, TypeError):
                        click.echo("❌ Bitte geben Sie eine Zahl zwischen 1 und 3 ein.")
                
                if decision != 3:
                    break  # Exit resolve loop
                    
            except Exception as e:
                click.echo(f"❌ Fehler beim Parsen der Korrektur: {e}")
                return
        
    except Exception as e:
        click.echo(f"❌ Fehler bei der Gedankenumkehr: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('gedankenfehler-umkehren')
@click.option('--weltanschauung', '-w', required=True, help='Weltanschauung zur Auswahl des Assistenten')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--output-file', help='Save output to file')
def assistants_gedankenfehler_umkehren(weltanschauung: str, 
                          output_format: str, output_file: Optional[str]):
    """Select and correct philosophical thought errors from predefined list."""
    try:
        # Load gedankenfehler from YAML file
        import yaml
        gedankenfehler_file = os.path.join(PROJECT_ROOT, 'base_data', 'gedankenfehler.yaml')
        
        try:
            with open(gedankenfehler_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                gedankenfehler_list = data['gedankenfehler']
        except FileNotFoundError:
            click.echo(f"❌ Gedankenfehler-Datei nicht gefunden: {gedankenfehler_file}", err=True)
            return
        except Exception as e:
            click.echo(f"❌ Fehler beim Laden der Gedankenfehler-Datei: {e}", err=True)
            return
        
        # Display gedankenfehler list
        click.echo("📋 Verfügbare Gedankenfehler:")
        click.echo("=" * 80)
        for fehler in gedankenfehler_list:
            nummer = fehler['nummer']
            gedankenfehler_text = fehler['gedankenfehler']
            click.echo(f"{nummer:2d}. {gedankenfehler_text}")
        
        # Get user selection
        while True:
            try:
                selection = click.prompt(f'\nWählen Sie einen Gedankenfehler (1-{len(gedankenfehler_list)})', type=int)
                if 1 <= selection <= len(gedankenfehler_list):
                    selected_fehler = gedankenfehler_list[selection - 1]
                    gedanke = selected_fehler['gedankenfehler']
                    stichwort = selected_fehler['stichwort']
                    break
                else:
                    click.echo(f"❌ Bitte wählen Sie eine Zahl zwischen 1 und {len(gedankenfehler_list)}.")
            except click.Abort:
                click.echo("\n❌ Vorgang abgebrochen.")
                return
            except (ValueError, TypeError):
                click.echo(f"❌ Bitte geben Sie eine gültige Zahl ein.")
        
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        
        # Find assistant by worldview (first 4 letters, case insensitive)
        weltanschauung_short = weltanschauung[:4].lower()
        matching_assistant = None
        matching_config = None
        
        for assistant_id, config in manager.assistant_configs.items():
            if config['worldview'][:4].lower() == weltanschauung_short:
                matching_assistant = assistant_id
                matching_config = config
                break
        
        if not matching_assistant:
            click.echo(f"❌ Kein Assistent für Weltanschauung '{weltanschauung}' gefunden.", err=True)
            click.echo("Verfügbare Weltanschauungen:")
            for assistant_id, config in manager.assistant_configs.items():
                click.echo(f"  - {config['worldview']} ({assistant_id})")
            return
        
        click.echo(f"\n🔄 Reformulating with {matching_config['name']}...")
        click.echo(f"💭 Ausgewählter Gedankenfehler: {gedanke}")
        click.echo(f"🏷️  Stichwort: {stichwort}")
        
        # Generate reformulate prompt  
        prompt = f"""Formuliere aus der Sicht deiner Weltanschauung ({matching_config['worldview']}) 3 philosophische Variationen zu folgendem Gedanken:

Gedanke: {gedanke}

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "gedanken_in_weltanschauung": [
        "Erste Variation des Gedankens",
        "Zweite Variation des Gedankens", 
        "Dritte Variation des Gedankens"
    ],
    "gedanke": "{gedanke}"
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
        
        # Query assistant
        response = manager.query_assistant(
            assistant_id=matching_assistant,
            user_message=prompt,
            use_knowledge_base=True
        )
        
        # Parse JSON response
        while True:
            try:
                import re
                json_match = re.search(r'\{.*\}', response["message"], re.DOTALL)
                if not json_match:
                    click.echo("❌ Konnte JSON-Antwort nicht parsen.")
                    return
                    
                parsed = json.loads(json_match.group())
                reformulations = parsed.get('gedanken_in_weltanschauung', [])
                
                if len(reformulations) < 3:
                    click.echo("❌ Nicht genügend Umformulierungen erhalten.")
                    return
                
                # Show options to user
                click.echo(f"\n📝 Umformulierungsoptionen von {matching_config['name']}:")
                click.echo("-" * 60)
                for i, reform in enumerate(reformulations, 1):
                    click.echo(f"{i}. {reform}")
                
                click.echo(f"\n4. Erneut umformulieren")
                click.echo(f"5. Abbrechen")
                
                # Get user choice
                while True:
                    try:
                        choice = click.prompt('Wählen Sie eine Option (1-5)', type=int)
                        if 1 <= choice <= 3:
                            chosen_reformulation = reformulations[choice - 1]
                            
                            # Display chosen reformulation and results
                            click.echo(f"\n✅ Gewählte Umformulierung:")
                            click.echo("=" * 80)
                            click.echo(f"💭 {chosen_reformulation}")
                            click.echo(f"\n🤖 Von: {matching_config['name']} ({matching_config['worldview']})")
                            click.echo(f"⏱️  Verarbeitungszeit: {response['processing_time']:.2f}s")
                            click.echo(f"💰 Kosten: ${response['usage']['cost']:.6f}")
                            
                            # Step 2: Process with gedankenfehler template
                            click.echo(f"\n🔄 Schritt 2: Korrektur des Gedankenfehlers...")
                            
                            aspekt = ""  # Start with empty aspekt
                            
                            while True:
                                try:
                                    # Generate resolve prompt
                                    resolve_prompt = f"""Du bist ein Experte der philosophischen Weltanschauung {matching_config['worldview']}. 

Korrigiere folgenden kulturgewordenen Gedankenfehler:

** {chosen_reformulation} **

{f"Berücksichtige dabei: {aspekt}" if aspekt else ""}

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "gedanke": "300-Wort-Korrektur aus deiner philosophischen Perspektive",
    "gedanke_kurz": "Kurze Zusammenfassung in 30-35 Worten",
    "gedanke_einfach": "Kinderfreundliche Erklärung für 10-Jährige"
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
                                    
                                    # Query assistant with built-in RAG enabled
                                    click.echo(f"\n🤖 Sende Anfrage an {matching_config['name']}...")
                                    
                                    resolve_response = manager.query_assistant(
                                        assistant_id=matching_assistant,
                                        user_message=resolve_prompt,
                                        use_knowledge_base=True,  # Use assistant's built-in RAG
                                        debug_mode=True  # Enable debug logging to see RAG results
                                    )
                                    
                                    # Parse resolve response
                                    json_match = re.search(r'\{.*\}', resolve_response["message"], re.DOTALL)
                                    if not json_match:
                                        click.echo("❌ Konnte JSON-Antwort nicht parsen.")
                                        return
                                        
                                    template_result = json.loads(json_match.group())
                                    
                                    # Use assistant's RAG citations
                                    rag_data = resolve_response.get("citations", [])
                                    
                                    click.echo(f"📚 {len(rag_data)} relevante Quellen aus RAG gefunden")
                                    
                                    # Calculate totals for display
                                    total_processing_time = response['processing_time'] + resolve_response['processing_time']
                                    total_cost = response['usage']['cost'] + resolve_response['usage']['cost']
                                    
                                    # Display result
                                    click.echo(f"\n✅ Korrektur von {matching_config['name']} ({matching_config['worldview']}):")
                                    click.echo("=" * 80)
                                    click.echo(f"💡 Korrektur: {template_result.get('gedanke', 'N/A')}")
                                    click.echo(f"\n📝 Zusammenfassung: {template_result.get('gedanke_kurz', template_result.get('gedanke_zusammenfassung', 'N/A'))}")
                                    click.echo(f"\n👶 Für Kinder: {template_result.get('gedanke_einfach', template_result.get('gedanke_kind', 'N/A'))}")
                                    click.echo(f"\n🤖 Model: {resolve_response.get('model', matching_config.get('model', 'unknown'))}")
                                    click.echo(f"📚 Pinecone Quellen: {len(rag_data)} verwendet")
                                    if rag_data:
                                        # Show source summary
                                        authors = list(set(result.get('metadata', {}).get('author', 'Unbekannt') for result in rag_data))
                                        click.echo(f"👥 Autoren: {', '.join(authors[:3])}{' ...' if len(authors) > 3 else ''}")
                                    click.echo(f"⏱️ Gesamte Verarbeitungszeit: {total_processing_time:.2f}s")
                                    click.echo(f"💰 Gesamte Kosten: ${total_cost:.6f}")
                                    
                                    # Ask for user decision
                                    click.echo(f"\n" + "=" * 80)
                                    click.echo("Was möchten Sie tun?")
                                    click.echo("1. Ergebnis akzeptieren und speichern")
                                    click.echo("2. Ergebnis ablehnen")
                                    click.echo("3. Aspekt hinzufügen")
                                    
                                    while True:
                                        try:
                                            decision = click.prompt('Wählen Sie eine Option (1-3)', type=int)
                                            if decision == 1:
                                                # Also save to output file if requested
                                                if output_file:
                                                    result_data = {
                                                        "timestamp": datetime.now().isoformat(),
                                                        "ausgewaehlter_gedankenfehler": {
                                                            "nummer": selected_fehler['nummer'],
                                                            "stichwort": selected_fehler['stichwort'],
                                                            "text": gedanke
                                                        },
                                                        "gewaehlte_umformulierung": chosen_reformulation,
                                                        "weltanschauung": matching_config['worldview'],
                                                        "assistent": matching_config['name'],
                                                        "model": resolve_response.get('model', matching_config.get('model', 'unknown')),
                                                        "aspekt": aspekt if aspekt else None,
                                                        "korrektur": template_result,
                                                        "rag_result": rag_data,
                                                        "gesamte_verarbeitungszeit": total_processing_time,
                                                        "gesamte_kosten": total_cost
                                                    }
                                                    
                                                    with open(output_file, 'w', encoding='utf-8') as f:
                                                        if output_format == 'json':
                                                            json.dump(result_data, f, indent=2, ensure_ascii=False)
                                                        else:  # table
                                                            f.write(f"Ausgewählter Gedankenfehler: [{selected_fehler['stichwort']}] {gedanke}\n")
                                                            f.write(f"Gewählte Umformulierung: {chosen_reformulation}\n\n")
                                                            f.write(f"Korrektur: {template_result.get('gedanke', 'N/A')}\n\n")
                                                            f.write(f"Zusammenfassung: {template_result.get('gedanke_kurz', template_result.get('gedanke_zusammenfassung', 'N/A'))}\n\n")
                                                            f.write(f"Für Kinder: {template_result.get('gedanke_einfach', template_result.get('gedanke_kind', 'N/A'))}\n\n")
                                                            f.write(f"Von: {matching_config['name']} ({matching_config['worldview']})\n")
                                                            f.write(f"Model: {resolve_response.get('model', matching_config.get('model', 'unknown'))}\n")
                                                            f.write(f"Aspekt: {aspekt if aspekt else 'Keiner'}\n")
                                                            f.write(f"RAG Quellen: {len(rag_data)} gefunden\n")
                                                            f.write(f"Gesamte Verarbeitungszeit: {total_processing_time:.2f}s\n")
                                                            f.write(f"Gesamte Kosten: ${total_cost:.6f}\n")
                                                    
                                                    click.echo(f"💾 Zusätzlich gespeichert in '{output_file}'.")
                                                
                                                # Database connection and insertion
                                                try:
                                                    from pymongo import MongoClient
                                                    import uuid
                                                    
                                                    # Database connection
                                                    mongodb_uri = "mongodb+srv://lafisrap:iRyZyiAK3uaXi0ee@ai-cluster-one.m1w8j.mongodb.net/12_weltanschauungen"
                                                    client = MongoClient(mongodb_uri)
                                                    db = client['12_weltanschauungen']
                                                    
                                                    # Author mappings
                                                    authors = {
                                                        "Dynamismus": "Ariadne Ikarus Nietzsche",
                                                        "Idealismus": "Aurelian I. Schelling", 
                                                        "Individualismus": "Amara Illias Leibniz",
                                                        "Materialismus": "Aloys I. Freud",
                                                        "Mathematismus": "Arcadius Ikarus Torvalds",
                                                        "Phänomenalismus": "Aetherius Imaginaris Goethe",
                                                        "Pneumatismus": "Aurelian Irenicus Novalis",
                                                        "Psychismus": "Archetype Intuitionis Fichte",
                                                        "Rationalismus": "Aristoteles Isaak Herder",
                                                        "Realismus": "Arvid I. Steiner",
                                                        "Sensualismus": "Apollo Ikarus Schiller",
                                                        "Spiritualismus": "Amara I. Steiner"
                                                    }
                                                    
                                                    # Check existing entries for this nummer/weltanschauung
                                                    existing_entries = list(db.gedanken.find({
                                                        "nummer": selected_fehler['nummer'],
                                                        "weltanschauung": matching_config['worldview']
                                                    }).sort("rank", 1))
                                                    
                                                    if existing_entries:
                                                        click.echo(f"\n📋 Bestehende Einträge für Nummer {selected_fehler['nummer']} in {matching_config['worldview']}:")
                                                        for i, entry in enumerate(existing_entries, 1):
                                                            gedanke_preview = entry.get('gedanke', '')[:100] + '...' if len(entry.get('gedanke', '')) > 100 else entry.get('gedanke', '')
                                                            click.echo(f"  {i}. Rank {entry.get('rank', '?')}: {gedanke_preview}")
                                                    
                                                    # Ask for prioritization
                                                    click.echo(f"\n💭 Wie möchten Sie den neuen Eintrag priorisieren?")
                                                    if existing_entries:
                                                        click.echo(f"1. Als höchste Priorität (Rank 1) - alle anderen Ränge nach unten verschieben")
                                                        click.echo(f"2. Als niedrigste Priorität (Rank {len(existing_entries) + 1})")
                                                        click.echo(f"3. Spezifischen Rang wählen (1-{len(existing_entries) + 1})")
                                                        
                                                        while True:
                                                            try:
                                                                priority_choice = click.prompt('Wählen Sie eine Option (1-3)', type=int)
                                                                if priority_choice == 1:
                                                                    chosen_rank = 1
                                                                    adjust_ranks = True
                                                                    break
                                                                elif priority_choice == 2:
                                                                    chosen_rank = len(existing_entries) + 1
                                                                    adjust_ranks = False
                                                                    break
                                                                elif priority_choice == 3:
                                                                    chosen_rank = click.prompt(f'Spezifischen Rang eingeben (1-{len(existing_entries) + 1})', type=int)
                                                                    if 1 <= chosen_rank <= len(existing_entries) + 1:
                                                                        adjust_ranks = chosen_rank <= len(existing_entries)
                                                                        break
                                                                    else:
                                                                        click.echo(f"❌ Bitte geben Sie einen Rang zwischen 1 und {len(existing_entries) + 1} ein.")
                                                                else:
                                                                    click.echo("❌ Ungültige Auswahl. Bitte wählen Sie 1-3.")
                                                            except (ValueError, TypeError):
                                                                click.echo("❌ Bitte geben Sie eine gültige Zahl ein.")
                                                            except click.Abort:
                                                                click.echo("\n❌ Vorgang abgebrochen.")
                                                                return
                                                    else:
                                                        # No existing entries, this will be rank 1
                                                        chosen_rank = 1
                                                        adjust_ranks = False
                                                        click.echo(f"📝 Kein bestehender Eintrag gefunden. Neuer Eintrag wird als Rank 1 gespeichert.")
                                                    
                                                    # Adjust existing ranks if needed
                                                    if adjust_ranks:
                                                        click.echo(f"\n🔄 Adjusting existing ranks...")
                                                        for entry in existing_entries:
                                                            if entry['rank'] >= chosen_rank:
                                                                new_rank = entry['rank'] + 1
                                                                db.gedanken.update_one(
                                                                    {"_id": entry["_id"]},
                                                                    {"$set": {"rank": new_rank}}
                                                                )
                                                                click.echo(f"   • Entry {entry.get('gedanke', '')[:50]}... : Rank {entry['rank']} → {new_rank}")
                                                    
                                                    # Get author info
                                                    autor = authors[matching_config['worldview']]
                                                    autor_info = db.autoren.find_one({"name": autor})
                                                    autor_id = autor_info.get("id") if autor_info else "unknown"
                                                    
                                                    # Create database entry
                                                    db_entry = {
                                                        "autor": autor,
                                                        "autorId": autor_id,
                                                        "weltanschauung": matching_config['worldview'],
                                                        "created_at": datetime.now(),
                                                        "ausgangsgedanke": gedanke,
                                                        "ausgangsgedanke_in_weltanschauung": chosen_reformulation,
                                                        "id": str(uuid.uuid4()),
                                                        "gedanke": template_result.get('gedanke', 'N/A'),
                                                        "gedanke_einfach": template_result.get('gedanke_einfach', template_result.get('gedanke_kind', 'N/A')),
                                                        "gedanke_kurz": template_result.get('gedanke_kurz', template_result.get('gedanke_zusammenfassung', 'N/A')),
                                                        "nummer": selected_fehler['nummer'],
                                                        "model": f"gedankenfehler-umkehren-rag-cli-{resolve_response.get('model', matching_config.get('model', 'unknown'))}",
                                                        "rank": chosen_rank,
                                                        "stichwort": selected_fehler['stichwort'],
                                                        "aspekt": aspekt if aspekt else None,
                                                        "rag_citations": rag_data,
                                                        "processing_time": total_processing_time,
                                                        "cost": total_cost
                                                    }
                                                    
                                                    # Insert into database
                                                    result = db.gedanken.insert_one(db_entry)
                                                    
                                                    if result.inserted_id:
                                                        click.echo(f"\n✅ Erfolgreich in Datenbank gespeichert:")
                                                        click.echo(f"   🏷️  Nummer: {selected_fehler['nummer']}")
                                                        click.echo(f"   🌍 Weltanschauung: {matching_config['worldview']}")
                                                        click.echo(f"   📊 Rank: {chosen_rank}")
                                                        click.echo(f"   👤 Autor: {autor}")
                                                        click.echo(f"   🆔 ID: {db_entry['id']}")
                                                        click.echo(f"   📚 RAG Quellen: {len(rag_data)}")
                                                        click.echo(f"   🤖 Model: {db_entry['model']}")
                                                    else:
                                                        click.echo(f"❌ Fehler beim Speichern in der Datenbank")
                                                    
                                                    client.close()
                                                    
                                                except Exception as e:
                                                    click.echo(f"❌ Fehler bei der Datenbank-Operation: {str(e)}")
                                                
                                                click.echo(f"\n✅ Umformulierung und Korrektur erfolgreich abgeschlossen.")
                                                click.echo(f"📊 Gesamt: {total_processing_time:.2f}s, ${total_cost:.6f}")
                                                return
                                                
                                            elif decision == 2:
                                                click.echo("❌ Ergebnis abgelehnt. Vorgang beendet.")
                                                return
                                                
                                            elif decision == 3:
                                                new_aspekt = click.prompt('Neuen Aspekt eingeben (oder Enter für leeren Aspekt)', default='', show_default=False)
                                                aspekt = new_aspekt if new_aspekt.strip() else ""
                                                click.echo(f"\n🔄 Wiederhole Korrektur mit {'neuem' if aspekt else 'ohne'} Aspekt...")
                                                if aspekt:
                                                    click.echo(f"🎯 Neuer Aspekt: {aspekt}")
                                                break  # Exit decision loop to retry template processing
                                                
                                            else:
                                                click.echo("❌ Ungültige Auswahl. Bitte wählen Sie 1-3.")
                                        except click.Abort:
                                            click.echo("\n❌ Vorgang abgebrochen.")
                                            return
                                        except (ValueError, TypeError):
                                            click.echo("❌ Bitte geben Sie eine Zahl zwischen 1 und 3 ein.")
                                    
                                    if decision != 3:
                                        break  # Exit template processing loop
                                        
                                except Exception as e:
                                    click.echo(f"❌ Fehler bei der Gedankenfehler-Verarbeitung: {str(e)}")
                                    return
                            
                            return
                            
                        elif choice == 4:
                            click.echo("\n🔄 Erneute Umformulierung...")
                            # Regenerate response
                            response = manager.query_assistant(
                                assistant_id=matching_assistant,
                                user_message=prompt,
                                use_knowledge_base=True
                            )
                            break  # Exit inner loop to retry parsing
                            
                        elif choice == 5:
                            click.echo("❌ Vorgang abgebrochen.")
                            return
                        else:
                            click.echo("❌ Ungültige Auswahl. Bitte wählen Sie 1-5.")
                    except click.Abort:
                        click.echo("\n❌ Vorgang abgebrochen.")
                        return
                    except (ValueError, TypeError):
                        click.echo("❌ Bitte geben Sie eine Zahl zwischen 1 und 5 ein.")
                
                # If we reach here, user chose option 4 (redo), so continue the while loop
                
            except Exception as e:
                click.echo(f"❌ Fehler beim Parsen der Umformulierung: {e}")
                return
        
    except Exception as e:
        click.echo(f"❌ Error correcting thought error: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('glossar')
@click.argument('assistant-name')
@click.option('--korrektur', help='Text to extract concepts from')
@click.option('--begriffe', help='Comma-separated list of specific concepts to define')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table', help='Output format')
@click.option('--output-file', help='Save output to file')
def assistants_glossar(assistant_name: str, korrektur: Optional[str], begriffe: Optional[str],
                       output_format: str, output_file: Optional[str]):
    """Generate philosophical glossary from text or concepts."""
    try:
        # Validate request
        if not korrektur and not begriffe:
            click.echo("❌ Either --korrektur or --begriffe must be provided", err=True)
            return
        
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        
        # Verify assistant exists
        if assistant_name not in manager.assistant_configs:
            click.echo(f"❌ Assistant {assistant_name} not found", err=True)
            return
        
        config = manager.assistant_configs[assistant_name]
        
        click.echo(f"📚 Generating glossary with {config['name']}...")
        if korrektur:
            click.echo(f"📝 From text: {korrektur[:100]}...")
        if begriffe:
            click.echo(f"🎯 Concepts: {begriffe}")
        
        # Generate glossary prompt
        if korrektur:
            text_to_process = korrektur
        else:
            # Create a text from provided concepts
            begriff_list = [b.strip() for b in begriffe.split(',')]
            text_to_process = f"Key philosophical concepts: {', '.join(begriff_list)}"
        
        prompt = f"""Erstelle ein philosophisches Glossar aus der Sicht deiner Weltanschauung ({config['worldview']}) für folgenden Text:

{text_to_process}

Extrahiere nur die wichtigsten philosophischen EINZELBEGRIFFE (einzelne Substantive) und erkläre sie aus deiner Weltanschauung heraus.

WICHTIG: Verwende nur einzelne Substantive wie "Erziehung", "Kind", "Harmonie", "Seele" - NICHT zusammengesetzte Begriffe oder Phrasen.

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "glossar": [
        {{
            "begriff": "Begriff1",
            "beschreibung": "Erklärung aus deiner Weltanschauung"
        }},
        {{
            "begriff": "Begriff2", 
            "beschreibung": "Erklärung aus deiner Weltanschauung"
        }}
    ]
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
        
        # Query assistant
        response = manager.query_assistant(
            assistant_id=assistant_name,
            user_message=prompt,
            use_knowledge_base=True
        )
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response["message"], re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                
                if output_format == 'table':
                    click.echo(f"\n📚 Glossary by {config['name']} ({config['worldview']}):")
                    click.echo("-" * 80)
                    glossary = parsed.get('glossar', [])
                    for term in glossary:
                        begriff = term.get('begriff', 'Unknown')
                        beschreibung = term.get('beschreibung', 'No description')
                        click.echo(f"\n🔖 {begriff}")
                        click.echo(f"   {beschreibung}")
                    click.echo(f"\n⏱️  Processing time: {response['processing_time']:.2f}s")
                    click.echo(f"💰 Cost: ${response['usage']['cost']:.6f}")
                
                else:  # json
                    result = {
                        **parsed,
                        "assistant_id": assistant_name,
                        "assistant_name": config['name'],
                        "weltanschauung": config['worldview'],
                        "processing_time": response['processing_time'],
                        "cost": response['usage']['cost'],
                        "original_request": {
                            "korrektur": korrektur,
                            "begriffe": begriffe.split(',') if begriffe else None
                        }
                    }
                    output = json.dumps(result, indent=2, ensure_ascii=False)
                    click.echo(output)
                    
            else:
                click.echo("❌ Could not parse JSON response from assistant")
                click.echo(f"Raw response: {response['message']}")
                
        except Exception as e:
            click.echo(f"❌ Error parsing response: {e}")
            click.echo(f"Raw response: {response['message']}")
        
        # Save to file if requested
        if output_file and json_match:
            with open(output_file, 'w', encoding='utf-8') as f:
                if output_format == 'json':
                    result = {
                        **parsed,
                        "assistant_id": assistant_name,
                        "assistant_name": config['name'],
                        "weltanschauung": config['worldview'],
                        "processing_time": response['processing_time'],
                        "cost": response['usage']['cost'],
                        "original_request": {
                            "korrektur": korrektur,
                            "begriffe": begriffe.split(',') if begriffe else None
                        }
                    }
                    json.dump(result, f, indent=2, ensure_ascii=False)
                else:  # table
                    f.write(f"Glossary by {config['name']} ({config['worldview']}):\n")
                    f.write("-" * 80 + "\n")
                    glossary = parsed.get('glossar', [])
                    for term in glossary:
                        begriff = term.get('begriff', 'Unknown')
                        beschreibung = term.get('beschreibung', 'No description')
                        f.write(f"\n{begriff}\n")
                        f.write(f"   {beschreibung}\n")
                    f.write(f"\nProcessing time: {response['processing_time']:.2f}s\n")
                    f.write(f"Cost: ${response['usage']['cost']:.6f}\n")
            
            click.echo(f"💾 Output saved to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error generating glossary: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('models')
def assistants_models():
    """Show available LLM models for Pinecone Assistant."""
    try:
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        models = manager.get_available_models()
        
        click.echo("🤖 Available LLM Models for Pinecone Assistant:")
        click.echo("=" * 50)
        
        model_descriptions = {
            "deepseek-reasoner": "DeepSeek Reasoner (default) - Exceptional reasoning, perfect for philosophy",
            "deepseek-chat": "DeepSeek Chat - Strong performance, good for coding and technical tasks",
            "claude-3-5-sonnet": "Anthropic Claude 3.5 Sonnet - Excellent reasoning, good for analysis",
            "gpt-4o": "OpenAI GPT-4o - High performance, good for general tasks",
            "gpt-4o-mini": "OpenAI GPT-4o Mini - Faster, cost-effective for simpler tasks"
        }
        
        for model in models:
            description = model_descriptions.get(model, "No description available")
            click.echo(f"  • {model}")
            click.echo(f"    {description}")
            click.echo()
        
        click.echo("💡 Use the --model option when creating assistants:")
        click.echo("   rag-cli assistants create my-assistant Idealismus --model deepseek-reasoner")
        click.echo("   (or omit --model to use deepseek-reasoner by default)")
        
    except Exception as e:
        click.echo(f"❌ Error listing models: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('list')
@click.option('--output-format', type=click.Choice(['table', 'json', 'csv']), default='table',
              help='Output format for assistant list')
@click.option('--output-file', help='Save output to file')
def assistants_list(output_format: str, output_file: Optional[str]):
    """List all Pinecone assistants."""
    try:
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        assistants = manager.list_assistants()
        
        if not assistants:
            click.echo("📭 No assistants found.")
            return
        
        # Process data for display
        for assistant in assistants:
            # Handle None values that could cause formatting errors
            assistant['name'] = assistant.get('name') or 'Unknown'
            assistant['status'] = assistant.get('status') or 'Unknown'
            assistant['created_on'] = assistant.get('created_on') or 'Unknown'
            # Default to deepseek-reasoner if no model specified
            assistant['model'] = assistant.get('model') or 'deepseek-reasoner'
        
        if output_format == 'table':
            # Display as table
            click.echo(f"🤖 Found {len(assistants)} assistants:")
            click.echo()
            
            # Calculate column widths
            id_width = max(len(a.get('id', '')) for a in assistants) + 2
            name_width = max(len(a['name']) for a in assistants) + 2
            status_width = max(len(a['status']) for a in assistants) + 2
            model_width = max(len(a['model']) for a in assistants) + 2
            date_width = 20
            
            # Header
            header = f"{'ID':<{id_width}} {'Name':<{name_width}} {'Status':<{status_width}} {'Model':<{model_width}} {'Created':<{date_width}}"
            click.echo(header)
            click.echo("-" * len(header))
            
            # Rows
            for assistant in assistants:
                created_date = assistant['created_on']
                if created_date != 'Unknown' and 'T' in created_date:
                    # Format datetime
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_date.replace('Z', '+00:00'))
                        created_date = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        pass
                
                assistant_id = assistant.get('id', 'N/A')
                
                row = f"{assistant_id:<{id_width}} {assistant['name']:<{name_width}} {assistant['status']:<{status_width}} {assistant['model']:<{model_width}} {created_date:<{date_width}}"
                click.echo(row)
                
        elif output_format == 'json':
            output_data = json.dumps(assistants, indent=2)
            click.echo(output_data)
            
        elif output_format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['id', 'name', 'status', 'model', 'created_on'])
            writer.writeheader()
            writer.writerows(assistants)
            output_data = output.getvalue()
            click.echo(output_data)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                if output_format == 'json':
                    json.dump(assistants, f, indent=2)
                elif output_format == 'csv':
                    import csv
                    writer = csv.DictWriter(f, fieldnames=['id', 'name', 'status', 'model', 'created_on'])
                    writer.writeheader()
                    writer.writerows(assistants)
                else:  # table
                    f.write("ID,Name,Status,Model,Created\n")
                    for assistant in assistants:
                        assistant_id = assistant.get('id', 'N/A')
                        f.write(f"{assistant_id},{assistant['name']},{assistant['status']},{assistant['model']},{assistant['created_on']}\n")
            
            click.echo(f"💾 Output saved to: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error listing assistants: {str(e)}", err=True)
        sys.exit(1)





@assistants_group.command('chat')
@click.argument('assistant-name')
@click.argument('message')
@click.option('--interactive/--no-interactive', default=False, help='Start interactive chat session')
@click.option('--history-file', help='File to save/load chat history')
def assistants_chat(assistant_name: str, message: str, interactive: bool, history_file: Optional[str]):
    """Chat with a Pinecone assistant."""
    try:
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        
        # Verify assistant exists
        if assistant_name not in manager.assistant_configs:
            click.echo(f"❌ Assistant {assistant_name} not found", err=True)
            return
        
        config = manager.assistant_configs[assistant_name]
        
        # Load chat history if file provided
        chat_history = []
        if history_file and os.path.exists(history_file):
            with open(history_file, 'r', encoding='utf-8') as f:
                chat_history = json.load(f)
        
        if not interactive:
            # Single message
            click.echo(f"💬 Chatting with {config['name']}...")
            response = manager.query_assistant(
                assistant_id=assistant_name,
                user_message=message,
                chat_history=chat_history,
                use_knowledge_base=True
            )
            
            click.echo(f"\n🤖 {config['name']}:")
            click.echo(response['message'])
            
            if response.get('citations'):
                click.echo(f"\n📚 Citations: {len(response['citations'])}")
                for i, citation in enumerate(response['citations'][:3]):  # Show first 3
                    click.echo(f"  {i+1}. {citation}")
            
            # Save to history
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": response['message']})
            
        else:
            # Interactive session
            click.echo(f"🚀 Starting interactive chat with {config['name']}")
            click.echo("Type 'quit' or 'exit' to end the session")
            
            # Send initial message
            response = manager.query_assistant(
                assistant_id=assistant_name,
                user_message=message,
                chat_history=chat_history,
                use_knowledge_base=True
            )
            
            click.echo(f"\n🤖 {config['name']}:")
            click.echo(response['message'])
            
            chat_history.append({"role": "user", "content": message})
            chat_history.append({"role": "assistant", "content": response['message']})
            
            # Interactive loop
            while True:
                user_input = click.prompt('\n👤 You', default='', show_default=False)
                
                if user_input.lower() in ['quit', 'exit', '']:
                    break
                
                response = manager.query_assistant(
                    assistant_id=assistant_name,
                    user_message=user_input,
                    chat_history=chat_history,
                    use_knowledge_base=True
                )
                
                click.echo(f"\n🤖 {config['name']}:")
                click.echo(response['message'])
                
                chat_history.append({"role": "user", "content": user_input})
                chat_history.append({"role": "assistant", "content": response['message']})
        
        # Save chat history
        if history_file:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(chat_history, f, indent=2, ensure_ascii=False)
            click.echo(f"\n💾 Chat history saved to {history_file}")
        
    except Exception as e:
        click.echo(f"Error chatting with assistant: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('list-files')
@click.argument('assistant-name')
@click.option('--output-format', type=click.Choice(['table', 'json']), default='table',
              help='Output format')
@click.option('--output-file', help='Save output to file')
def assistants_list_files(assistant_name: str, output_format: str, output_file: Optional[str]):
    """Show documents available to assistant via shared knowledge base."""
    try:
        # Import the assistant manager  
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        
        # Get assistant configuration to determine worldview
        assistant_configs = manager.assistant_configs
        if assistant_name not in assistant_configs:
            click.echo(f"❌ Assistant {assistant_name} not found", err=True)
            return
        
        config = assistant_configs[assistant_name]
        worldview = config["worldview"]
        
        click.echo(f"📚 Documents available to '{config['name']}' ({worldview}):")
        click.echo(f"🔍 Filter: worldview = {worldview}")
        
        # Get actual documents from the shared knowledge base
        documents = manager._get_assistant_documents(assistant_name)
        
        if output_format == 'table':
            if documents:
                click.echo(f"\n📚 Available Documents ({len(documents)} total):")
                click.echo("-" * 80)
                for i, doc in enumerate(documents[:50], 1):
                    title = doc.get('title', doc.get('source', 'Unknown'))
                    # Clean up the title for better display
                    if title.startswith('🌎'):
                        title = title[2:]  # Remove emoji
                    if '#' in title:
                        title = title.replace('#', ' - ')
                    click.echo(f"{i:3d}. {title}")
                
                if len(documents) > 50:
                    click.echo(f"\n... and {len(documents) - 50} more documents")
            else:
                click.echo("📭 No documents found for this worldview")
            
            click.echo()
            click.echo("📝 Note: Documents are accessed via shared Pinecone index with worldview filtering.")
            
        else:  # json
            data = {
                "assistant_name": assistant_name,
                "assistant_display_name": config['name'],
                "worldview": worldview,
                "model": config['model'],
                "documents": [
                    {
                        "title": doc.get('title', doc.get('source', 'Unknown')),
                        "source": doc.get('source', ''),
                        "metadata": doc
                    }
                    for doc in documents[:50]  # Limit to first 50 for JSON output
                ],
                "architecture": "hybrid_deepseek_pinecone",
                "note": "Documents are accessed via shared Pinecone index with worldview filtering"
            }
            output = json.dumps(data, indent=2)
            click.echo(output)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w') as f:
                if output_format == 'json':
                    data = {
                        "assistant_name": assistant_name,
                        "assistant_display_name": config['name'],
                        "worldview": worldview,
                        "model": config['model'],
                        "documents": [
                            {
                                "title": doc.get('title', doc.get('source', 'Unknown')),
                                "source": doc.get('source', ''),
                                "metadata": doc
                            }
                            for doc in documents[:50]
                        ],
                        "architecture": "hybrid_deepseek_pinecone",
                        "note": "Documents are accessed via shared Pinecone index with worldview filtering"
                    }
                    json.dump(data, f, indent=2)
                else:  # table
                    f.write(f"Documents available to '{config['name']}' ({worldview}):\n")
                    f.write(f"Filter: worldview = {worldview}\n\n")
                    
                    if documents:
                        f.write(f"Available Documents ({len(documents)} total):\n")
                        f.write("-" * 40 + "\n")
                        for i, doc in enumerate(documents[:50], 1):
                            title = doc.get('title', doc.get('source', 'Unknown'))
                            if title.startswith('🌎'):
                                title = title[2:]
                            if '#' in title:
                                title = title.replace('#', ' - ')
                            f.write(f"{i:3d}. {title}\n")
                        if len(documents) > 50:
                            f.write(f"\n... and {len(documents) - 50} more documents\n")
                    else:
                        f.write("No documents found for this worldview\n")
                    
                    f.write("\nNote: Documents are accessed via shared Pinecone index with worldview filtering.\n")
            
            click.echo(f"💾 Output saved to {output_file}")
        
    except Exception as e:
        click.echo(f"❌ Error listing files for assistant: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('add-files')
@click.argument('assistant-name')
@click.argument('file-paths', nargs=-1, required=True)
@click.option('--worldview', help='Worldview metadata for files')
@click.option('--batch-size', type=int, default=5, help='Number of files to upload in parallel')
@click.option('--dry-run/--no-dry-run', default=False, help='Show what would be uploaded')
def assistants_add_files(assistant_name: str, file_paths: tuple, worldview: Optional[str], 
                        batch_size: int, dry_run: bool):
    """Add files/documents to an assistant."""
    try:
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        assistant = manager.pc.assistant.Assistant(assistant_name=assistant_name)
        
        # Validate files exist
        valid_files = []
        for file_path in file_paths:
            if os.path.exists(file_path):
                valid_files.append(file_path)
            else:
                click.echo(f"Warning: File not found: {file_path}", err=True)
        
        if not valid_files:
            click.echo("No valid files to upload.", err=True)
            sys.exit(1)
        
        if dry_run:
            click.echo(f"Would upload {len(valid_files)} files to assistant '{assistant_name}':")
            for file_path in valid_files:
                file_size = os.path.getsize(file_path)
                click.echo(f"  - {file_path} ({file_size} bytes)")
            return
        
        click.echo(f"Uploading {len(valid_files)} files to assistant '{assistant_name}'...")
        
        # Prepare documents list
        documents = []
        for file_path in valid_files:
            doc_metadata = {"source": file_path}
            if worldview:
                doc_metadata["worldview"] = worldview
            
            documents.append({
                "path": file_path,
                "metadata": doc_metadata
            })
        
        # Upload files
        with click.progressbar(documents, label='Uploading files') as bar:
            upload_results = []
            for doc in bar:
                try:
                    result = manager.upload_documents_to_assistant(
                        assistant=assistant,
                        documents=[doc],
                        worldview=worldview or "Unknown"
                    )
                    upload_results.extend(result)
                except Exception as e:
                    upload_results.append({
                        "file": doc["path"],
                        "status": "error",
                        "error": str(e)
                    })
        
        # Show results
        successful = sum(1 for r in upload_results if r["status"] == "success")
        failed = sum(1 for r in upload_results if r["status"] == "error")
        
        click.echo(f"\nUpload complete: {successful} successful, {failed} failed")
        
        if failed > 0:
            click.echo("\nFailed uploads:")
            for result in upload_results:
                if result["status"] == "error":
                    click.echo(f"  ❌ {result['file']}: {result['error']}")
        
        # Save upload log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "add_files",
            "assistant_name": assistant_name,
            "files_uploaded": len(valid_files),
            "successful": successful,
            "failed": failed,
            "worldview": worldview
        }
        
        log_file = os.path.join(log_dir, f"assistant_file_upload_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
    except Exception as e:
        click.echo(f"Error adding files to assistant: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('remove-files')
@click.argument('assistant-name')
@click.argument('file-ids', nargs=-1, required=True)
@click.confirmation_option(prompt='Are you sure you want to remove these files?')
def assistants_remove_files(assistant_name: str, file_ids: tuple):
    """Remove files/documents from an assistant."""
    try:
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        assistant = manager.pc.assistant.Assistant(assistant_name=assistant_name)
        
        click.echo(f"Removing {len(file_ids)} files from assistant '{assistant_name}'...")
        
        successful = 0
        failed = 0
        
        for file_id in file_ids:
            try:
                # This would need to be implemented based on Pinecone Assistant API
                if hasattr(assistant, 'delete_file'):
                    assistant.delete_file(file_id)
                    click.echo(f"✅ Removed file: {file_id}")
                    successful += 1
                else:
                    click.echo(f"⚠️ File removal not supported by Pinecone Assistant API")
                    break
            except Exception as e:
                click.echo(f"❌ Failed to remove file {file_id}: {str(e)}", err=True)
                failed += 1
        
        click.echo(f"\nFile removal complete: {successful} successful, {failed} failed")
        
        # Save removal log
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": "remove_files",
            "assistant_name": assistant_name,
            "files_removed": len(file_ids),
            "successful": successful,
            "failed": failed
        }
        
        log_file = os.path.join(log_dir, f"assistant_file_removal_{datetime.now().strftime('%Y%m%d')}.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
    except Exception as e:
        click.echo(f"Error removing files from assistant: {str(e)}", err=True)
        sys.exit(1)

@assistants_group.command('context')
@click.argument('assistant-name')
@click.argument('query')
@click.option('--top-k', type=int, default=5, help='Number of context snippets to return')
@click.option('--worldview-filter', help='Filter by worldview metadata')
@click.option('--output-file', help='Save context results to file')
def assistants_context(assistant_name: str, query: str, top_k: int, 
                      worldview_filter: Optional[str], output_file: Optional[str]):
    """Query an assistant for context without generating a response."""
    try:
        # Import the assistant manager
        sys.path.insert(0, PROJECT_ROOT)
        from assistants.deepseek_assistant_manager import DeepSeekAssistantManager as PineconeAssistantManager
        
        manager = PineconeAssistantManager()
        assistant = manager.pc.assistant.Assistant(assistant_name=assistant_name)
        
        # Prepare metadata filter
        metadata_filter = {}
        if worldview_filter:
            metadata_filter["worldview"] = worldview_filter
        
        click.echo(f"🔍 Querying context from assistant '{assistant_name}'...")
        click.echo(f"Query: {query}")
        
        response = manager.query_with_context(
            assistant=assistant,
            query=query,
            metadata_filter=metadata_filter if metadata_filter else None
        )
        
        snippets = response['snippets'][:top_k]
        
        click.echo(f"\n📄 Found {len(snippets)} context snippets:")
        click.echo("-" * 80)
        
        for i, snippet in enumerate(snippets, 1):
            click.echo(f"\nSnippet {i} (Score: {snippet['score']:.3f}):")
            click.echo(f"Content: {snippet['content'][:200]}...")
            if snippet.get('metadata'):
                click.echo(f"Metadata: {snippet['metadata']}")
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "query": query,
                    "assistant_name": assistant_name,
                    "metadata_filter": metadata_filter,
                    "snippets": snippets,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
            
            click.echo(f"\n💾 Context results saved to {output_file}")
        
    except Exception as e:
        click.echo(f"Error querying context: {str(e)}", err=True)
        sys.exit(1)



if __name__ == '__main__':
    cli() 