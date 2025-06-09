# Swagger UI for Personal RAG Server

This directory contains Python scripts to serve and manage OpenAPI specifications for the Personal RAG Server and Personal Embeddings Service.

## Files

-   `serve-swagger.py` - Main script to serve Swagger UI with both API specifications
-   `check-specs.py` - Utility to validate the OpenAPI YAML specifications
-   `personal-rag-server-openapi.yaml` - OpenAPI specification for the Personal RAG Server
-   `personal-embeddings-service-openapi.yaml` - OpenAPI specification for the Personal Embeddings Service

## Usage

### Check if OpenAPI specs are valid

```bash
./check-specs.py
```

### Serve Swagger UI (no Docker required)

```bash
./serve-swagger.py
```

Then open your browser to http://localhost:8080

## Features

-   Displays both API specifications in a dropdown menu
-   No Docker required - pure Python solution
-   Automatically downloads and configures Swagger UI
-   Validates YAML specifications
