#!/usr/bin/env python3
from sentence_transformers import SentenceTransformer
import numpy as np
import time
import torch
import logging
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Test data focused on German philosophical content with number variations
texts = [
    "Die Philosophie ist die kritische Untersuchung fundamentaler Fragen.",
    "Rudolf Steiners 12 Weltanschauungen bieten verschiedene Perspektiven.",
    "Materialismus, Idealismus und Spiritualismus sind wichtige philosophische Richtungen.",
    "Welches sind die 12 Weltanschauungen?",
    "Welches sind die zwölf Weltanschauungen?"
]

# Pairs to test similarity detection
similarity_pairs = [
    ("Welches sind die 12 Weltanschauungen?", "Welches sind die zwölf Weltanschauungen?"),
    ("Materialismus", "Idealismus"),
    ("Rudolf Steiner", "Rudolf Steiners 12 Weltanschauungen"),
]

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def test_model(model_name, texts, similarity_pairs):
    logger.info(f"Testing model: {model_name}")
    
    start_load = time.time()
    model = SentenceTransformer(model_name)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    load_time = time.time() - start_load
    
    # Warmup
    _ = model.encode(["Warmup text"])
    
    # Single embedding timing
    start_time = time.time()
    embedding = model.encode(texts[0])
    single_time = time.time() - start_time
    
    # Batch timing
    start_time = time.time()
    embeddings = model.encode(texts)
    batch_time = time.time() - start_time
    
    # Similarity tests
    similarity_results = {}
    for text1, text2 in similarity_pairs:
        emb1 = model.encode(text1)
        emb2 = model.encode(text2)
        similarity = cosine_similarity(emb1, emb2)
        similarity_results[f"{text1} vs {text2}"] = float(similarity)
    
    return {
        "model": model_name,
        "dimension": len(embedding),
        "load_time_sec": load_time,
        "single_text_time_ms": single_time * 1000,
        "batch_time_ms": batch_time * 1000,
        "throughput_texts_per_sec": len(texts) / batch_time,
        "device": str(device),
        "similarity_scores": similarity_results
    }

def main():
    output_file = Path("model_comparison_results.json")
    
    # Models to test
    models = [
        "intfloat/multilingual-e5-large",  # Current model
        "T-Systems-onsite/cross-en-de-roberta-sentence-transformer"  # New model
    ]
    
    results = {}
    for model_name in models:
        try:
            model_results = test_model(model_name, texts, similarity_pairs)
            results[model_name] = model_results
            logger.info(f"Completed testing {model_name}")
            logger.info(f"Dimension: {model_results['dimension']}")
            logger.info(f"Single text time: {model_results['single_text_time_ms']:.2f}ms")
            logger.info(f"Batch throughput: {model_results['throughput_texts_per_sec']:.2f} texts/sec")
            
            # Log similarity results
            logger.info("Similarity scores:")
            for pair, score in model_results['similarity_scores'].items():
                logger.info(f"  {pair}: {score:.4f}")
            
            logger.info("-" * 50)
        except Exception as e:
            logger.error(f"Error testing {model_name}: {str(e)}")
    
    # Save results
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_file}")
    
    # Simple comparison
    if len(results) > 1:
        logger.info("\nKey comparison points:")
        for metric in ["dimension", "single_text_time_ms", "throughput_texts_per_sec"]:
            values = {name: result[metric] for name, result in results.items()}
            logger.info(f"{metric}: {values}")
        
        # Compare similarity of number variations
        key_pair = "Welches sind die 12 Weltanschauungen? vs Welches sind die zwölf Weltanschauungen?"
        sim_scores = {name: result["similarity_scores"][key_pair] for name, result in results.items()}
        logger.info(f"Number variation similarity: {sim_scores}")

if __name__ == "__main__":
    main() 