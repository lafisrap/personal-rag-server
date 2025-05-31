#!/usr/bin/env python3
"""
A simple script to test the DeepSeek service with a philosophical question.
This bypasses the REST API and directly calls the service.
"""

import os
import sys
import logging
import asyncio
import json
import requests

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.deepseek_service import DeepSeekService
from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_api_call():
    """Test a direct API call to DeepSeek without using the service."""
    try:
        # Setup the API call
        api_key = settings.DEEPSEEK_API_KEY
        api_url = settings.DEEPSEEK_API_URL
        model = settings.DEEPSEEK_PHILOSOPHY_MODEL
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "What is the meaning of life?"}],
            "temperature": 0.5,
            "stream": False
        }
        
        logger.info(f"Making direct API call to {api_url}/chat/completions")
        logger.info(f"Headers: {json.dumps({k: ('Bearer *****' if k == 'Authorization' else v) for k, v in headers.items()})}")
        logger.info(f"Payload: {json.dumps(payload)}")
        
        # Make the request
        response = requests.post(
            f"{api_url}/chat/completions",
            headers=headers,
            json=payload
        )
        
        # Check the response
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Response: {json.dumps(response_data)}")
            return response_data
        else:
            logger.error(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error making direct API call: {str(e)}")
        return None

async def test_philosophical_question():
    """Test a philosophical question directly with the DeepSeek service."""
    try:
        # Create and initialize the DeepSeek service
        service = DeepSeekService()
        service.initialize_model()
        
        # Define a philosophical question
        question = "What is the meaning of life?"
        messages = [{"role": "user", "content": question}]
        
        logger.info(f"Testing question: {question}")
        
        # Check if it's detected as philosophical
        is_philosophical = service._is_philosophical_question(messages)
        logger.info(f"Detected as philosophical: {is_philosophical}")
        logger.info(f"Default model: {service.model_name}")
        logger.info(f"Philosophy model: {service.philosophy_model_name}")
        
        # Get a response
        try:
            response = service.get_llm_response(messages=messages, temperature=0.7)
            logger.info(f"Response generated using model: {response.get('model', 'unknown')}")
            logger.info(f"Response content: {response.get('content', 'No content')}")
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {str(e)}")
            logger.error(f"Response status code: {e.response.status_code}")
            logger.error(f"Response text: {e.response.text}")
            return None
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error testing philosophical question: {str(e)}")
        return None

def test_api_key():
    """Check if the API key is configured properly."""
    api_key = settings.DEEPSEEK_API_KEY
    
    if not api_key:
        logger.error("DeepSeek API key is not configured")
        return False
    
    # Check API key format
    if len(api_key) < 10:
        logger.warning("DeepSeek API key seems too short")
    
    # Check if API key has common prefixes
    common_prefixes = ["sk-", "ds-"]
    if not any(api_key.startswith(prefix) for prefix in common_prefixes):
        logger.warning(f"DeepSeek API key doesn't start with common prefixes {common_prefixes}")
    
    return True

def main():
    """Run the test script."""
    logger.info("Testing DeepSeek service with a philosophical question")
    logger.info(f"DeepSeek API Key configured: {'Yes' if settings.DEEPSEEK_API_KEY else 'No'}")
    logger.info(f"DeepSeek API URL: {settings.DEEPSEEK_API_URL}")
    logger.info(f"Default model: {settings.DEEPSEEK_MODEL}")
    logger.info(f"Philosophy model: {settings.DEEPSEEK_PHILOSOPHY_MODEL}")
    
    # Test API key
    if not test_api_key():
        logger.error("API key validation failed, but continuing anyway")
    
    # First try a direct API call
    logger.info("Attempting direct API call to DeepSeek...")
    direct_response = test_direct_api_call()
    
    if direct_response:
        logger.info("Direct API call succeeded")
        # Print the result nicely
        print("\n" + "=" * 50)
        print("DIRECT API CALL RESULT")
        print("=" * 50)
        print(f"Question: What is the meaning of life?")
        content = direct_response.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
        print("-" * 50)
        print(content)
        print("=" * 50)
    else:
        logger.error("Direct API call failed")
        
        # Try through the service
        logger.info("Attempting through service...")
        # Run the async test
        response = asyncio.run(test_philosophical_question())
        
        if response:
            # Print the result nicely
            print("\n" + "=" * 50)
            print("PHILOSOPHICAL QUESTION TEST RESULT")
            print("=" * 50)
            print(f"Question: What is the meaning of life?")
            print(f"Model used: {response.get('model', 'unknown')}")
            print("-" * 50)
            print(response.get('content', 'No response generated'))
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("TEST FAILED")
            print("=" * 50)
            print("Both direct API call and service call failed.")
            print("Please check your DeepSeek API configuration and network connectivity.")
            print("=" * 50)

if __name__ == "__main__":
    main() 