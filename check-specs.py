#!/usr/bin/env python3
"""
Check if the OpenAPI specification files exist and are valid YAML.
If they don't exist, create empty template files.
"""

import os
import sys
import yaml
from pathlib import Path

def check_yaml_file(file_path):
    """Check if a file exists and is valid YAML."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"WARNING: File {path} does not exist")
        return False
    
    try:
        with open(path, 'r') as f:
            yaml.safe_load(f)
        print(f"SUCCESS: {path} is valid YAML")
        return True
    except yaml.YAMLError as e:
        print(f"ERROR: {path} is not valid YAML: {e}")
        return False

def create_template_file(file_path, title, description):
    """Create a template OpenAPI specification file."""
    path = Path(file_path)
    
    template = f"""openapi: 3.0.3
info:
  title: {title}
  description: {description}
  version: 1.0.0
  contact:
    name: API Support
servers:
  - url: /api/v1
    description: API v1

paths:
  /:
    get:
      summary: Root endpoint
      responses:
        '200':
          description: Successful response
"""
    
    with open(path, 'w') as f:
        f.write(template)
    
    print(f"Created template file: {path}")

def main():
    """Check the OpenAPI specification files."""
    current_dir = Path.cwd()
    
    specs = [
        {
            "filename": "personal-rag-server-openapi.yaml",
            "title": "Personal RAG Server API",
            "description": "Personal RAG Server with FastAPI - Secure and Production Ready"
        },
        {
            "filename": "personal-embeddings-service-openapi.yaml",
            "title": "Personal Embeddings Service API",
            "description": "Self-hosted cross-en-de-roberta-sentence-transformer embedding service for RAG applications"
        }
    ]
    
    all_valid = True
    
    print("Checking OpenAPI specification files...")
    
    for spec in specs:
        spec_path = current_dir / spec["filename"]
        if not spec_path.exists():
            print(f"File {spec_path} does not exist. Creating template...")
            create_template_file(spec_path, spec["title"], spec["description"])
            all_valid = False
        elif not check_yaml_file(spec_path):
            all_valid = False
    
    if all_valid:
        print("\nAll OpenAPI specification files are valid!")
        print("You can now run ./serve-swagger.py to start the Swagger UI server")
    else:
        print("\nSome OpenAPI specification files were missing or invalid.")
        print("Template files have been created for missing files.")
        print("Please edit these files with your actual API specifications.")
        print("Then run ./serve-swagger.py to start the Swagger UI server")
        sys.exit(1)

if __name__ == "__main__":
    main() 