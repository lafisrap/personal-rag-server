#!/usr/bin/env python3
"""
A script to ask a philosophical question directly using the DeepSeek service.
This bypasses the REST API and directly calls the service.
"""

import os
import sys
import logging
import asyncio
import argparse

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.deepseek_service import DeepSeekService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def ask_philosophical_question(question):
    """Ask a philosophical question directly with the DeepSeek service."""
    try:
        # Create and initialize the DeepSeek service
        service = DeepSeekService()
        service.initialize_model()
        
        # Format the question as a message
        messages = [{"role": "user", "content": question}]
        
        logger.info(f"Asking philosophical question: {question}")
        
        # Check if it's detected as philosophical
        is_philosophical = service._is_philosophical_question(messages)
        
        if is_philosophical:
            logger.info("Question detected as philosophical.")
            logger.info(f"Using philosophy-specific model: {service.philosophy_model_name}")
        else:
            logger.info("Question not detected as philosophical.")
            logger.info(f"Using default model: {service.model_name}")
        
        # Get a response
        response = service.get_llm_response(
            messages=messages, 
            temperature=0.5,
            system_prompt="You are a knowledgeable philosophy assistant who specializes in exploring philosophical questions. Answer thoroughly, citing major philosophers and philosophical concepts."
        )
        
        logger.info(f"Response generated using model: {response.get('model', 'unknown')}")
        return response
        
    except Exception as e:
        logger.error(f"Error asking philosophical question: {str(e)}")
        raise

def main():
    """Run the script with command line arguments."""
    parser = argparse.ArgumentParser(description='Ask a philosophical question.')
    parser.add_argument('question', type=str, help='The philosophical question to ask')
    
    args = parser.parse_args()
    
    # Run the async function
    response = asyncio.run(ask_philosophical_question(args.question))
    
    # Print the result nicely
    print("\n" + "=" * 60)
    print("PHILOSOPHICAL QUESTION")
    print("=" * 60)
    print(f"Question: {args.question}")
    print(f"Model used: {response.get('model', 'unknown')}")
    print("-" * 60)
    print(response.get('content', 'No response generated'))
    print("=" * 60)

if __name__ == "__main__":
    main() 