# RAG CLI Tool

A Command Line Interface for RAG (Retrieval-Augmented Generation) Management.

## Features

-   **Knowledge Base Management**: Upload, update, delete, and get statistics about your knowledge base
-   **Search and Query**: Perform searches and queries against your vector database
-   **Diagnostics and Reporting**: Run diagnostics, check documents, and generate reports

## Installation

Clone the repository and install the package:

```bash
# From the project root directory
pip install -e scripts/rag-cli
```

Or use the script directly:

```bash
python scripts/rag-cli/main.py
```

## Usage

### Knowledge Base Management

```bash
# Upload documents to the vector store
rag-cli kb upload --source /path/to/kb --categories category1,category2

# Update existing documents
rag-cli kb update --source /path/to/kb --categories category1,category2

# Delete categories
rag-cli kb delete --categories category1,category2

# Re-index documents with a new embedding model
rag-cli kb reindex --source /path/to/kb --categories category1,category2

# Get statistics about indexed content
rag-cli kb stats --categories category1,category2
```

### Search and Query

```bash
# Perform a search query
rag-cli search query "Your search query" --category category1 --top-k 5
```

### Diagnostics and Reporting

```bash
# List all indexed documents
rag-cli diagnostics list-documents

# Validate configuration settings
rag-cli diagnostics validate-settings

# Run diagnostics on the retrieval system
rag-cli diagnostics diagnose-retrieval --query "Your query" --expected-doc "Document ID"

# Check a specific document
rag-cli diagnostics check-document --document-id "Document ID" --expected-category "Category"

# Generate a comprehensive analysis report
rag-cli diagnostics generate-report
```

## Improved Document Checking

The CLI includes an improved document checking command that is more reliable at finding documents in the vector store:

```bash
rag-cli diagnostics check-document-improved --document-id "Document ID" --expected-category "Category" --query-match
```

This command uses multiple strategies to find documents and handles various edge cases better than the original command.
