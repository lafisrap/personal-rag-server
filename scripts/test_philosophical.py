#!/usr/bin/env python3
"""
A simple script to test the philosophical question detection in the DeepSeek service.
This can be used to manually test and refine the detection logic.
"""

import os
import sys
import logging

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.deepseek_service import DeepSeekService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_question(question: str) -> bool:
    """Test if a question is detected as philosophical."""
    service = DeepSeekService()
    messages = [{"role": "user", "content": question}]
    return service._is_philosophical_question(messages)

def main():
    """Run the test script."""
    print("Philosophical Question Detection Test")
    print("-" * 40)
    
    test_questions = [
        # Philosophical questions
        "What is the meaning of life?",
        "Does free will exist?",
        "How do we know what is morally right?",
        "Is consciousness a product of the brain or something more?",
        "What is the nature of reality itself?",
        "Can we truly know anything with certainty?",
        "What would Aristotle say about modern virtue ethics?",
        "Is beauty subjective or objective?",
        "What is the relationship between mind and body?",
        "Is there an objective truth?",
        
        # Non-philosophical questions
        "What's the weather like today?",
        "How do I make pasta?",
        "What time is it?",
        "Can you tell me about the latest iPhone?",
        "How tall is Mount Everest?",
        "What's the capital of France?",
        "How do I fix a leaky faucet?",
        "What are the ingredients for chocolate chip cookies?",
        "When was the Declaration of Independence signed?",
        "How does photosynthesis work?",
    ]
    
    # Add some custom questions from the command line
    if len(sys.argv) > 1:
        custom_questions = sys.argv[1:]
        test_questions.extend(custom_questions)
    
    results = {"philosophical": [], "non_philosophical": []}
    
    for question in test_questions:
        is_philosophical = test_question(question)
        category = "philosophical" if is_philosophical else "non_philosophical"
        results[category].append(question)
    
    # Print results
    print("\nDetected as philosophical:")
    for q in results["philosophical"]:
        print(f"  - {q}")
    
    print("\nDetected as non-philosophical:")
    for q in results["non_philosophical"]:
        print(f"  - {q}")
    
    print("\nSummary:")
    print(f"  - Total questions: {len(test_questions)}")
    print(f"  - Philosophical: {len(results['philosophical'])}")
    print(f"  - Non-philosophical: {len(results['non_philosophical'])}")

if __name__ == "__main__":
    main() 