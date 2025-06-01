# Knowledge Base Management System

This system provides tools for uploading, managing, and querying a philosophical knowledge base stored in Pinecone vector database.

## Overview

The knowledge base management system processes text files from a structured directory of philosophical worldviews and uploads them to a Pinecone vector database. Each worldview category is stored as a separate namespace in Pinecone, allowing for efficient organization and querying.

## Components

1. **Knowledge Base Scanner** (`app/services/kb_scanner.py`)

    - Scans the knowledge base directory structure
    - Extracts metadata from filenames
    - Groups related files (.txt, .quantify, .csv)

2. **File Processor** (`app/services/file_processor.py`)

    - Processes text files and chunks them for vectorization
    - Extracts word statistics from quantify and CSV files
    - Enriches text documents with metadata from related files

3. **Vector Store Manager** (`app/services/vector_store_manager.py`)

    - Manages Pinecone vector operations
    - Uploads document chunks with metadata
    - Provides operations for updating and deleting data
    - Reports statistics about the vector store

4. **CLI Tool** (`scripts/manage_kb.py`)
    - Command-line interface for knowledge base management
    - Supports uploading, updating, deleting, and viewing statistics

## Usage

### Prerequisites

Make sure you have set up the following environment variables:

-   `PINECONE_API_KEY`
-   `PINECONE_ENVIRONMENT`
-   `PINECONE_INDEX_NAME`
-   `OPENAI_API_KEY` (for embeddings)

### Commands

#### Upload the entire knowledge base

```bash
python scripts/manage_kb.py upload --source /path/to/knowledge_base
```

#### Upload specific categories

```bash
python scripts/manage_kb.py upload --source /path/to/knowledge_base --categories Materialismus,Idealismus
```

#### Update specific categories

```bash
python scripts/manage_kb.py update --source /path/to/knowledge_base --categories Materialismus --delete-existing
```

#### Delete categories

```bash
python scripts/manage_kb.py delete --categories Materialismus,Idealismus
```

#### View statistics

```bash
python scripts/manage_kb.py stats
```

View statistics for specific categories:

```bash
python scripts/manage_kb.py stats --categories Materialismus,Idealismus
```

## Integration with RAG System

The knowledge base can be queried using the existing RAG service. The worldview categories are stored as separate namespaces in Pinecone, allowing for targeted queries.

Example query:

```python
from app.services.rag_service import rag_service

# Query within a specific worldview
response = rag_service.generate_rag_response(
    messages=[{"role": "user", "content": "What is the concept of consciousness?"}],
    filter={"category": "Materialismus"}
)

# Cross-category query
response = rag_service.generate_rag_response(
    messages=[{"role": "user", "content": "Compare consciousness in materialism and idealism"}]
)
```

## File Structure Assumptions

The system assumes the knowledge base is organized as follows:

```
knowledge_base/
├── Worldview1/
│   ├── Author#Title.txt
│   ├── Author#Title.quantify
│   └── Worldview1.csv
├── Worldview2/
│   ├── ©Author@Title.txt
│   ├── ©Author@Title.quantify
│   └── Worldview2.csv
...
```

## Maintenance

The system logs all operations to both the console and log files. Statistics about uploads and the current state of the vector store are saved as JSON files for future reference.

Logs and statistics files are saved in the current directory with timestamps:

-   `kb_management_YYYYMMDD_HHMMSS.log`
-   `kb_upload_stats_YYYYMMDD_HHMMSS.json`
-   `kb_stats_YYYYMMDD_HHMMSS.json`
