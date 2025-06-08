#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
import argparse
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description='Download and cache embedding model')
    parser.add_argument('--cache-dir', default='./models', help='Directory to cache model')
    parser.add_argument('--model', default='T-Systems-onsite/cross-en-de-roberta-sentence-transformer', 
                        help='Model to download (default: T-Systems-onsite/cross-en-de-roberta-sentence-transformer)')
    args = parser.parse_args()
    
    model_name = args.model
    cache_dir = args.cache_dir
    
    # Ensure cache directory exists
    os.makedirs(cache_dir, exist_ok=True)
    
    logger.info(f"Downloading {model_name}...")
    try:
        model = SentenceTransformer(model_name, cache_folder=cache_dir)
        # Run a test encoding to ensure the model is properly downloaded
        _ = model.encode(["Test sentence to ensure model is working"])
        logger.info(f"Model downloaded and cached successfully in {cache_dir}")
    except Exception as e:
        logger.error(f"Failed to download model: {str(e)}")
        raise

if __name__ == "__main__":
    main() 