"""
Test script to verify embedding performance with GBERT-large on Apple M1 Max.
"""
import time
import numpy as np
from app.services.embedding_service import embedding_service
import sys

def test_single_embedding():
    """Test performance of generating a single embedding."""
    print("\n=== Testing Single Embedding Performance ===")
    
    text = "Dies ist ein Test für das deutsche Embedding-Modell GBERT-large auf dem Apple M1 Max."
    
    # First call might include model loading time
    start_time = time.time()
    embedding = embedding_service.get_embeddings(text)
    first_call_time = time.time() - start_time
    
    print(f"First call time (including model loading): {first_call_time:.4f} seconds")
    print(f"Embedding shape: {embedding.shape}")
    
    # Second call should be faster (model already loaded)
    start_time = time.time()
    embedding = embedding_service.get_embeddings(text)
    second_call_time = time.time() - start_time
    
    print(f"Second call time: {second_call_time:.4f} seconds")
    
    # Test caching
    start_time = time.time()
    embedding = embedding_service.get_embeddings(text)
    cached_call_time = time.time() - start_time
    
    # Avoid division by zero
    if cached_call_time > 0:
        print(f"Cached call time: {cached_call_time:.4f} seconds")
        print(f"Speedup from caching: {second_call_time / cached_call_time:.2f}x")
    else:
        print(f"Cached call time: {cached_call_time:.4f} seconds (too fast to measure)")
        print(f"Caching is working effectively!")

def test_batch_embedding(batch_size=32):
    """Test performance of generating batch embeddings."""
    print("\n=== Testing Batch Embedding Performance ===")
    
    # Generate a list of texts
    texts = [
        f"Dies ist ein Beispieltext Nummer {i} für den Batch-Test." 
        for i in range(100)
    ]
    
    # Process in different batch sizes
    batch_sizes = [1, 8, 16, 32, 64]
    
    for bs in batch_sizes:
        start_time = time.time()
        embeddings = embedding_service.get_embeddings(texts, batch_size=bs)
        elapsed_time = time.time() - start_time
        
        print(f"Batch size {bs}: {elapsed_time:.4f} seconds for {len(texts)} texts")
        print(f"  Average time per text: {elapsed_time / len(texts):.4f} seconds")
        print(f"  Embeddings shape: {embeddings.shape}")

def test_device_info():
    """Print information about the device being used."""
    print("\n=== Device Information ===")
    
    health_info = embedding_service.get_health_check()
    print(f"Model: {health_info['model']}")
    print(f"Device: {health_info['device']}")
    print(f"Test processing time: {health_info['test_processing_time']:.4f} seconds")
    print(f"Embedding dimension: {health_info['embedding_dimension']}")

if __name__ == "__main__":
    print("=== GBERT-large Embedding Performance Test on Apple M1 Max ===")
    
    # Run the tests
    test_device_info()
    test_single_embedding()
    test_batch_embedding()
    
    print("\nPerformance testing completed!") 