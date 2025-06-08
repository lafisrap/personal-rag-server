#!/usr/bin/env python3
"""
Test script to evaluate the performance of the new embedding model.
This script tests queries related to Rudolf Steiner's 12 Weltanschauungen
with different number formats (digit vs spelled-out).
"""

import os
import sys
import json
import logging
from pprint import pprint

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.services.rag_service import rag_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_query(query: str, top_k: int = 30, filter_category: str = None):
    """Test a query against the RAG system."""
    logger.info(f"Testing query: '{query}'")
    
    # Prepare filter if category is specified
    filter = {"category": filter_category} if filter_category else None
    
    # Get query results
    results = rag_service.query(
        query_text=query,
        filter=filter,
        top_k=top_k
    )
    
    # Extract and format the results
    formatted_results = []
    for i, doc in enumerate(results):
        formatted_results.append({
            "position": i + 1,
            "document": doc.get("metadata", {}).get("filename", "Unknown"),
            "category": doc.get("metadata", {}).get("category", "Unknown"),
            "score": doc.get("score", 0.0),
            "text_preview": doc.get("text", "")[:100] + "..." if doc.get("text") else ""
        })
    
    # Check for our target document
    target_doc = "Rudolf_Steiner#Der_menschliche_und_der_kosmische_Gedanke_Zyklus_33_[GA_151].txt"
    target_found = False
    target_position = -1
    
    for result in formatted_results:
        if target_doc in result["document"]:
            target_found = True
            target_position = result["position"]
            break
    
    # Print summary
    print(f"\nQuery: '{query}'")
    print(f"Filter Category: {filter_category if filter_category else 'None'}")
    print(f"Total results: {len(formatted_results)}")
    print(f"Target document '{target_doc}' found: {target_found}")
    if target_found:
        print(f"Target position: {target_position}")
    
    # Print top 5 results
    print("\nTop 5 Results:")
    for i, result in enumerate(formatted_results[:5]):
        print(f"{i+1}. {result['document']} (Score: {result['score']:.4f})")
    
    # Save detailed results to file
    result_file = f"test_results_{query.replace(' ', '_')}.json"
    with open(result_file, 'w') as f:
        json.dump({
            "query": query,
            "filter_category": filter_category,
            "top_k": top_k,
            "target_found": target_found,
            "target_position": target_position,
            "results": formatted_results
        }, f, indent=2)
    
    logger.info(f"Saved detailed results to {result_file}")
    
    return target_found, target_position, formatted_results

def main():
    """Run test queries with different formats."""
    # Test queries with different number formats
    queries = [
        "Welches sind die 12 Weltanschauungen?",
        "Welches sind die zwölf Weltanschauungen?",
        "12 Weltanschauungen",
        "zwölf Weltanschauungen",
        "12 Weltanschauungen Materialismus Idealismus Spiritualismus",
        "zwölf Weltanschauungen Materialismus Idealismus Spiritualismus",
    ]
    
    # Test with and without category filter
    filters = [None, "Realismus_Test"]
    
    results = []
    
    # Run tests
    for filter_category in filters:
        print(f"\n{'='*80}")
        print(f"Testing with filter_category: {filter_category}")
        print(f"{'='*80}")
        
        for query in queries:
            found, position, _ = test_query(
                query=query,
                top_k=30,
                filter_category=filter_category
            )
            
            results.append({
                "query": query,
                "filter_category": filter_category,
                "found": found,
                "position": position
            })
    
    # Print summary table
    print("\n\nSummary Table:")
    print(f"{'Query':<50} | {'Filter':<15} | {'Found':<5} | {'Position':<8}")
    print(f"{'-'*50}-+-{'-'*15}-+-{'-'*5}-+-{'-'*8}")
    
    for result in results:
        print(f"{result['query']:<50} | {str(result['filter_category']):<15} | {str(result['found']):<5} | {result['position'] if result['position'] > 0 else 'N/A':<8}")
    
    # Save overall results
    with open("test_summary.json", "w") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    main() 