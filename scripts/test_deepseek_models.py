#!/usr/bin/env python3
"""
A script to list available DeepSeek models.
"""

import os
import sys
import logging
import requests
import json

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def list_available_models():
    """List all available DeepSeek models."""
    try:
        # Setup the API call
        api_key = settings.DEEPSEEK_API_KEY
        api_url = settings.DEEPSEEK_API_URL
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        logger.info(f"Making API call to {api_url}/models")
        
        # Make the request
        response = requests.get(
            f"{api_url}/models",
            headers=headers
        )
        
        # Check the response
        logger.info(f"Response status code: {response.status_code}")
        
        if response.status_code == 200:
            response_data = response.json()
            logger.info(f"Found {len(response_data.get('data', []))} models")
            return response_data
        else:
            logger.error(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        logger.error(f"Error listing models: {str(e)}")
        return None

def try_alternative_models():
    """Try alternative model names that might work with DeepSeek."""
    try:
        # Setup the API call
        api_key = settings.DEEPSEEK_API_KEY
        api_url = settings.DEEPSEEK_API_URL
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # List of models to try
        test_models = [
            "deepseek-chat",
            "deepseek-llm",
            "deepseek-coder",
            "deepseek-v2",
            "deepseek-v3",
            "deepseek-text-base"
        ]
        
        results = {}
        
        for model in test_models:
            logger.info(f"Testing model: {model}")
            
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hello"}],
                "temperature": 0.5,
                "stream": False
            }
            
            try:
                # Make the request
                response = requests.post(
                    f"{api_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=5  # Short timeout to avoid waiting too long
                )
                
                status = response.status_code
                results[model] = {
                    "status": status,
                    "works": status == 200,
                    "message": response.text if status != 200 else "Success"
                }
                
                logger.info(f"Model {model}: Status {status}")
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Error testing model {model}: {str(e)}")
                results[model] = {
                    "status": 0,
                    "works": False,
                    "message": str(e)
                }
        
        return results
            
    except Exception as e:
        logger.error(f"Error testing alternative models: {str(e)}")
        return None

def test_simple_request():
    """Test a simple request using the default model."""
    try:
        # Setup the API call
        api_key = settings.DEEPSEEK_API_KEY
        api_url = settings.DEEPSEEK_API_URL
        model = settings.DEEPSEEK_MODEL  # Use the default model
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Hello, how are you?"}],
            "temperature": 0.5,
            "stream": False
        }
        
        logger.info(f"Making simple request with model: {model}")
        
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
        logger.error(f"Error making simple request: {str(e)}")
        return None

def main():
    """Run the script."""
    logger.info("Testing DeepSeek API and listing available models")
    logger.info(f"DeepSeek API Key configured: {'Yes' if settings.DEEPSEEK_API_KEY else 'No'}")
    logger.info(f"DeepSeek API URL: {settings.DEEPSEEK_API_URL}")
    logger.info(f"Default model: {settings.DEEPSEEK_MODEL}")
    logger.info(f"Philosophy model: {settings.DEEPSEEK_PHILOSOPHY_MODEL}")
    
    # First check if we can list the available models
    logger.info("Attempting to list available models...")
    models_response = list_available_models()
    
    if models_response:
        logger.info("Successfully retrieved models list")
        
        # Print available models
        print("\n" + "=" * 50)
        print("AVAILABLE DEEPSEEK MODELS")
        print("=" * 50)
        
        for model in models_response.get('data', []):
            print(f"- {model.get('id')}")
        
        print("=" * 50)
    else:
        logger.error("Failed to list models")
        
        # Try a simple request
        logger.info("Trying a simple request with the default model...")
        simple_response = test_simple_request()
        
        if simple_response:
            logger.info("Simple request succeeded")
            
            # Print the result
            print("\n" + "=" * 50)
            print("SIMPLE REQUEST RESULT")
            print("=" * 50)
            print(f"Model: {settings.DEEPSEEK_MODEL}")
            content = simple_response.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
            print("-" * 50)
            print(content)
            print("=" * 50)
        else:
            logger.error("Simple request failed")
            
            # Try alternative models
            logger.info("Trying alternative model names...")
            alternative_results = try_alternative_models()
            
            if alternative_results:
                # Print the results
                print("\n" + "=" * 50)
                print("ALTERNATIVE MODELS TEST RESULTS")
                print("=" * 50)
                
                for model, result in alternative_results.items():
                    status = "✅ WORKS" if result["works"] else "❌ FAILS"
                    print(f"- {model}: {status} (Status: {result['status']})")
                    if not result["works"]:
                        print(f"  Error: {result['message'][:100]}...")  # First 100 chars of error
                
                print("=" * 50)
                print("\nSUGGESTIONS:")
                print("1. Check if your API key has access to the models you're trying to use")
                print("2. Update your settings to use one of the working models")
                print("3. Contact DeepSeek support if none of the models work")
                print("=" * 50)
            else:
                print("\n" + "=" * 50)
                print("ALL TESTS FAILED")
                print("=" * 50)
                print("Could not list models or make any successful API calls.")
                print("Please check your DeepSeek API configuration and network connectivity.")
                print("=" * 50)

if __name__ == "__main__":
    main() 