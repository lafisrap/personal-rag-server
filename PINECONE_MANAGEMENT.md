# PINECONE MANAGEMENT PLAN

## Overview

This document outlines the plan for uploading and managing vector data from the knowledge base located at `/Users/michaelschmidt/Reniets/Ai/12-weltanschauungen/dist/knowledge_base` to Pinecone. The knowledge base appears to be organized into philosophical worldview categories (Materialismus, Idealismus, etc.), with each containing text documents, quantify files, and CSV files related to those worldviews.

## Data Structure Analysis

### Knowledge Base Structure

-   Root directory contains multiple worldview categories as subdirectories
-   Each subdirectory contains:
    -   Text files (`.txt`) with philosophical content
    -   Quantify files (`.quantify`) with word statistics
    -   CSV files with word frequency data

### Organization Strategy

We'll use the worldview categories (directory names) as the primary namespace in Pinecone. This will allow for:

1. Clean separation of different philosophical worldviews
2. Efficient querying within specific worldview domains
3. Easy management and updates per category

## Implementation Plan

### 1. Knowledge Base Processor

Create a dedicated service that will:

-   Scan the knowledge base directory
-   Process files by category
-   Extract and chunk text content
-   Generate embeddings
-   Upload to Pinecone with appropriate metadata

### 2. Components to Develop

#### a. Knowledge Base Scanner

```python
# app/services/kb_scanner.py
class KnowledgeBaseScanner:
    """Service for scanning and cataloging the knowledge base."""

    def scan_directory(self, base_path):
        """
        Scan the knowledge base directory and catalog all files.

        Returns:
            Dict mapping categories to file lists
        """
        # Implementation details
```

#### b. File Processor

```python
# app/services/file_processor.py
class FileProcessor:
    """Service for processing different file types in the knowledge base."""

    def process_text_file(self, file_path):
        """Process a text file and return its content."""
        # Implementation details

    def process_quantify_file(self, file_path):
        """Process a quantify file and extract relevant metadata."""
        # Implementation details

    def process_csv_file(self, file_path):
        """Process a CSV file with word frequencies."""
        # Implementation details
```

#### c. Vector Store Manager

```python
# app/services/vector_store_manager.py
class VectorStoreManager:
    """Service for managing vector data in Pinecone."""

    def upsert_category(self, category, documents):
        """
        Upsert all documents for a category to Pinecone.

        Args:
            category: The worldview category (namespace)
            documents: List of processed documents
        """
        # Implementation details

    def delete_category(self, category):
        """Delete all vectors for a category."""
        # Implementation details

    def update_document(self, category, document_id, document):
        """Update a specific document."""
        # Implementation details
```

#### d. CLI Tool for Management

```python
# scripts/manage_kb.py
# CLI tool for knowledge base management
# Commands:
# - upload: Upload entire knowledge base
# - update: Update specific categories
# - delete: Delete specific categories
# - stats: Show statistics about the vector store
```

### 3. Integration with Existing Services

Leverage existing services in the application:

-   Use `EmbeddingService` for generating embeddings
-   Use `VectorDatabase` for interacting with Pinecone
-   Extend `RAGService` to support the new namespaces/categories

### 4. Metadata Structure

Each document vector will include:

-   `text`: The chunk of text
-   `document_id`: Unique ID for the document
-   `filename`: Original filename
-   `category`: The worldview category (e.g., "Materialismus")
-   `author`: Extracted from filename if available
-   `title`: Extracted from filename if available
-   `chunk_index`: Position of chunk in document
-   `word_stats`: Key statistics from quantify files (top concepts/terms)

### 5. Update Strategy

For ongoing updates to the knowledge base:

1. Scan the knowledge base to detect changes
2. For new files: Process and upload
3. For modified files: Delete old vectors and upload new ones
4. For deleted files: Remove corresponding vectors
5. Implement tracking of last modification timestamps

## Implementation Timeline

1. **Phase 1 (Day 1-2)**: Develop the core components

    - Knowledge Base Scanner
    - File Processor with text chunking
    - Basic Vector Store Manager

2. **Phase 2 (Day 3-4)**: Enhance metadata and processing

    - Extract and process metadata from quantify files
    - Implement intelligent chunking strategies
    - Add metadata extraction from filenames

3. **Phase 3 (Day 5-6)**: Create management tools

    - Develop CLI tool for managing the knowledge base
    - Implement update detection
    - Add statistics and monitoring

4. **Phase 4 (Day 7)**: Integration and testing
    - Integrate with existing RAG service
    - Test with different query patterns
    - Optimize for performance

## Usage Examples

### Initial Upload

```bash
python scripts/manage_kb.py upload --source /Users/michaelschmidt/Reniets/Ai/12-weltanschauungen/dist/knowledge_base
```

### Update Specific Categories

```bash
python scripts/manage_kb.py update --categories Materialismus,Idealismus
```

### Query Statistics

```bash
python scripts/manage_kb.py stats
```

## Conclusion

This plan provides a systematic approach to upload and manage the philosophical knowledge base in Pinecone. The organization by worldview categories as namespaces provides a clean separation that will support efficient querying and targeted searches within specific philosophical domains.

The implementation leverages existing services in the application while adding new components specifically designed for knowledge base management. With proper metadata tagging and regular updates, this system will maintain an up-to-date vector store that accurately represents the knowledge base.
