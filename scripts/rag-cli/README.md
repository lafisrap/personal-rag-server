# RAG CLI Tool

The RAG CLI (Command Line Interface) tool provides a unified interface for managing RAG (Retrieval-Augmented Generation) components, including the Pinecone vector database.

## Features

-   **Knowledge Base Management**: Upload, update, delete, and get statistics about your knowledge base
-   **Search and Query**: Perform searches and queries against your vector database
-   **Diagnostics and Reporting**: Run diagnostics, check documents, and generate reports

## Installation

The RAG CLI is automatically installed as part of the personal-rag-server package. Ensure that your Python environment is properly set up with all dependencies.

## Usage

```bash
python -m rag_cli [command-group] [command] [options]
```

## Command Groups

-   `pinecone`: Pinecone vector database management
-   `kb`: Knowledge base management
-   `search`: Search and query operations
-   `diagnostics`: Diagnostics and reporting

## Pinecone Commands

### Truncate Index

Delete all vectors from a Pinecone index:

```bash
python -m rag_cli pinecone truncate --index-name cross-en-de-roberta-sentence-transformer
```

This command will:

1. Connect to the specified Pinecone index
2. Delete all vectors from all namespaces in the index
3. Verify that the index is empty

### Upload Documents

Upload documents to a Pinecone index with custom chunking parameters:

```bash
python -m rag_cli pinecone upload \
  --index-name cross-en-de-roberta-sentence-transformer \
  --source-dir /Users/michaelschmidt/Reniets/Ai/12-weltanschauungen/dist/knowledge_base \
  --category Test \
  --chunk-size 600 \
  --chunk-overlap 250
```

This command will:

1. Connect to the specified Pinecone index
2. Process all text files in the source directory recursively
3. Extract metadata from filenames (author and title)
4. Chunk the text using the specified chunk size and overlap
5. Upload all chunks to the Pinecone index with appropriate metadata

Options:

-   `--chunk-size`: Size of text chunks (default: 600)
-   `--chunk-overlap`: Overlap between chunks (default: 250)
-   `--parallel/--no-parallel`: Use parallel processing (default: False)
-   `--workers`: Number of parallel workers (default: 4)

### Get Index Statistics

Get statistics about a Pinecone index:

```bash
python -m rag_cli pinecone stats --index-name cross-en-de-roberta-sentence-transformer
```

This command will:

1. Connect to the specified Pinecone index
2. Retrieve and display index statistics (total vector count, dimension)
3. Display namespace statistics (vector count per namespace)
4. Save statistics to a JSON file in the logs directory

## Complete Example

Here's a complete workflow for refreshing your vector database:

```bash
# 1. Truncate the index
python -m rag_cli pinecone truncate --index-name cross-en-de-roberta-sentence-transformer

# 2. Check that the index is empty
python -m rag_cli pinecone stats --index-name cross-en-de-roberta-sentence-transformer

# 3. Upload documents with custom chunking parameters
python -m rag_cli pinecone upload \
  --index-name cross-en-de-roberta-sentence-transformer \
  --source-dir /Users/michaelschmidt/Reniets/Ai/12-weltanschauungen/dist/knowledge_base \
  --category Test \
  --chunk-size 600 \
  --chunk-overlap 250

# 4. Verify upload statistics
python -m rag_cli pinecone stats --index-name cross-en-de-roberta-sentence-transformer
```

## Troubleshooting

If you encounter issues:

1. Check the logs in the `logs` directory
2. Ensure your `.env` file contains the correct Pinecone API key and index information
3. Verify that the Pinecone index exists and is accessible
4. For upload issues, check that the source directory contains valid text files

## Knowledge Base Management

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

## Search and Query

```bash
# Perform a search query
rag-cli search query "Your search query" --category category1 --top-k 5
```

## Diagnostics and Reporting

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
