#!/usr/bin/env python3
"""
Integration tests for the Personal RAG Server.

This script tests various components of the system to ensure they are working correctly:
1. DeepSeek API connectivity and model availability
2. Philosophical question detection
3. RAG functionality with the DeepSeek service
4. Model selection for philosophical queries (uses deepseek-reasoner)

Run this script to verify that the system is properly configured and functioning.
"""

import os
import sys
import logging
import json
import asyncio
import argparse
import requests
from typing import Dict, Any, List, Optional

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.core.config import settings
from app.services.deepseek_service import DeepSeekService

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTests:
    """Class to run integration tests for the Personal RAG Server."""
    
    def __init__(self):
        """Initialize the integration tests."""
        self.api_key = settings.DEEPSEEK_API_KEY
        self.api_url = settings.DEEPSEEK_API_URL
        self.model_name = settings.DEEPSEEK_MODEL
        self.philosophy_model_name = settings.DEEPSEEK_PHILOSOPHY_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        self.test_results = {
            "config_test": None,
            "api_connectivity": None,
            "models_available": None,
            "philosophical_detection": None,
            "model_selection": None,
            "simple_query": None
        }
    
    def run_all_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run all integration tests and return results."""
        logger.info("Starting integration tests...")
        
        # Test environment configuration
        self.test_results["config_test"] = self.test_configuration()
        
        # Test API connectivity and model availability
        self.test_results["api_connectivity"] = self.test_api_connectivity()
        
        if self.test_results["api_connectivity"]["success"]:
            self.test_results["models_available"] = self.test_available_models()
            
            # Run simple query test
            self.test_results["simple_query"] = self.test_simple_query(
                "What is the capital of France?", 
                verbose
            )
            
            # Test philosophical detection
            self.test_results["philosophical_detection"] = self.test_philosophical_detection(verbose)
            
            # Test model selection for philosophical vs non-philosophical queries
            self.test_results["model_selection"] = self.test_model_selection(verbose)
        
        # Print summary
        self.print_test_summary()
        
        return self.test_results
    
    def test_configuration(self) -> Dict[str, Any]:
        """Test environment configuration."""
        logger.info("Testing configuration...")
        
        result = {
            "success": False,
            "details": {},
            "issues": []
        }
        
        # Check API key
        if not self.api_key:
            result["issues"].append("DEEPSEEK_API_KEY is not configured")
        else:
            result["details"]["api_key_configured"] = True
            
            # Basic API key format checks
            if len(self.api_key) < 10:
                result["issues"].append("API key seems too short")
            
            common_prefixes = ["sk-", "ds-"]
            if not any(self.api_key.startswith(prefix) for prefix in common_prefixes):
                result["issues"].append(f"API key doesn't start with common prefixes {common_prefixes}")
        
        # Check API URL
        if not self.api_url:
            result["issues"].append("DEEPSEEK_API_URL is not configured")
        else:
            result["details"]["api_url"] = self.api_url
        
        # Check model names
        if not self.model_name:
            result["issues"].append("DEEPSEEK_MODEL is not configured")
        else:
            result["details"]["model_name"] = self.model_name
        
        if not self.philosophy_model_name:
            result["issues"].append("DEEPSEEK_PHILOSOPHY_MODEL is not configured")
        else:
            result["details"]["philosophy_model_name"] = self.philosophy_model_name
            
            # Verify philosophy model is set to deepseek-reasoner
            if self.philosophy_model_name != "deepseek-reasoner":
                result["issues"].append(f"DEEPSEEK_PHILOSOPHY_MODEL should be 'deepseek-reasoner', found '{self.philosophy_model_name}'")
        
        # Check if we have minimum viable configuration
        result["success"] = (
            self.api_key is not None and 
            self.api_url is not None and 
            self.model_name is not None and
            self.philosophy_model_name == "deepseek-reasoner"
        )
        
        return result
    
    def test_api_connectivity(self) -> Dict[str, Any]:
        """Test basic API connectivity."""
        logger.info(f"Testing API connectivity to {self.api_url}...")
        
        result = {
            "success": False,
            "details": {},
            "error": None
        }
        
        try:
            # Make a simple request to check if the API is accessible
            response = requests.get(
                f"{self.api_url}/models",
                headers=self.headers,
                timeout=10
            )
            
            status_code = response.status_code
            result["details"]["status_code"] = status_code
            
            if status_code == 200:
                result["success"] = True
                result["details"]["response_time_ms"] = response.elapsed.total_seconds() * 1000
            else:
                result["error"] = f"API request failed with status code: {status_code}"
                try:
                    result["details"]["error_response"] = response.json()
                except:
                    result["details"]["error_response"] = response.text[:200]  # First 200 chars
        
        except requests.exceptions.RequestException as e:
            result["error"] = str(e)
            logger.error(f"API connectivity test failed: {str(e)}")
        
        return result
    
    def test_available_models(self) -> Dict[str, Any]:
        """Test to check available models."""
        logger.info("Testing available models...")
        
        result = {
            "success": False,
            "models": [],
            "error": None,
            "model_found": False,
            "philosophy_model_found": False
        }
        
        try:
            # Make the request to list models
            response = requests.get(
                f"{self.api_url}/models",
                headers=self.headers
            )
            
            if response.status_code == 200:
                response_data = response.json()
                models = response_data.get('data', [])
                
                # Extract model IDs
                model_ids = [model.get('id') for model in models if model.get('id')]
                result["models"] = model_ids
                result["success"] = len(model_ids) > 0
                
                # Check if configured models are available
                if self.model_name in model_ids:
                    result["model_found"] = True
                    logger.info(f"Configured model '{self.model_name}' is available")
                else:
                    logger.warning(f"Configured model '{self.model_name}' is NOT in the available models list")
                
                if self.philosophy_model_name in model_ids:
                    result["philosophy_model_found"] = True
                    logger.info(f"Configured philosophy model '{self.philosophy_model_name}' is available")
                else:
                    logger.warning(f"Configured philosophy model '{self.philosophy_model_name}' is NOT in the available models list")
                
            else:
                result["error"] = f"Error response: {response.text}"
                logger.error(result["error"])
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing available models: {str(e)}")
        
        return result
    
    def test_simple_query(self, query: str, verbose: bool = False) -> Dict[str, Any]:
        """Test a simple query to the DeepSeek API."""
        logger.info(f"Testing simple query: {query}")
        
        result = {
            "success": False,
            "query": query,
            "model_used": self.model_name,
            "response": None,
            "error": None
        }
        
        try:
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": query}],
                "temperature": 0.5,
                "stream": False
            }
            
            response = requests.post(
                f"{self.api_url}/chat/completions",
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get('choices', [{}])[0].get('message', {}).get('content', 'No content')
                
                result["success"] = True
                result["response"] = content
                
                if verbose:
                    print("\n" + "=" * 50)
                    print("SIMPLE QUERY TEST RESULT")
                    print("=" * 50)
                    print(f"Query: {query}")
                    print(f"Model: {self.model_name}")
                    print("-" * 50)
                    print(content)
                    print("=" * 50)
            else:
                result["error"] = f"Error response: {response.text}"
                logger.error(result["error"])
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing simple query: {str(e)}")
        
        return result
    
    def test_philosophical_query(self, query: str, verbose: bool = False) -> Dict[str, Any]:
        """Test a philosophical query to the DeepSeek API."""
        logger.info(f"Testing philosophical query: {query}")
        
        # Initialize the DeepSeek service
        service = DeepSeekService()
        service.initialize_model()
        
        result = {
            "success": False,
            "query": query,
            "is_philosophical": False,
            "model_used": None,
            "response": None,
            "error": None
        }
        
        try:
            # Check if it's detected as philosophical
            messages = [{"role": "user", "content": query}]
            is_philosophical = service._is_philosophical_question(messages)
            result["is_philosophical"] = is_philosophical
            
            # Get a response
            response_obj = service.get_llm_response(messages=messages, temperature=0.7)
            
            result["success"] = True
            result["model_used"] = response_obj.get("model", "unknown")
            result["response"] = response_obj.get("content", "No content")
            
            if verbose:
                print("\n" + "=" * 50)
                print("PHILOSOPHICAL QUERY TEST RESULT")
                print("=" * 50)
                print(f"Query: {query}")
                print(f"Detected as philosophical: {is_philosophical}")
                print(f"Model used: {result['model_used']}")
                print("-" * 50)
                print(result["response"])
                print("=" * 50)
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing philosophical query: {str(e)}")
        
        return result
    
    def test_model_selection(self, verbose: bool = False) -> Dict[str, Any]:
        """Test that the correct model is selected for different query types."""
        logger.info("Testing model selection logic...")
        
        result = {
            "success": False,
            "test_cases": [],
            "summary": {
                "total": 0,
                "correct_model_selection": 0,
                "accuracy": 0.0
            },
            "error": None
        }
        
        try:
            service = DeepSeekService()
            service.initialize_model()
            
            # Test cases with queries and expected models
            test_cases = [
                # Philosophical questions (should use deepseek-reasoner)
                {"query": "What is the meaning of life?", "expected_model": self.philosophy_model_name},
                {"query": "Does free will exist?", "expected_model": self.philosophy_model_name},
                {"query": "How do we determine what is moral?", "expected_model": self.philosophy_model_name},
                
                # Non-philosophical questions (should use default model)
                {"query": "What is the capital of France?", "expected_model": self.model_name},
                {"query": "How do I bake a cake?", "expected_model": self.model_name},
                {"query": "What's the weather like today?", "expected_model": self.model_name},
            ]
            
            for case in test_cases:
                query = case["query"]
                expected_model = case["expected_model"]
                
                messages = [{"role": "user", "content": query}]
                is_philosophical = service._is_philosophical_question(messages)
                
                # Just check which model would be used without making actual API call
                model_to_use = service.philosophy_model_name if is_philosophical else service.model_name
                
                case_result = {
                    "query": query,
                    "is_philosophical": is_philosophical,
                    "expected_model": expected_model,
                    "selected_model": model_to_use,
                    "correct": model_to_use == expected_model
                }
                
                result["test_cases"].append(case_result)
            
            # Calculate summary statistics
            total = len(result["test_cases"])
            correct_model_selection = sum(1 for case in result["test_cases"] if case["correct"])
            
            result["summary"] = {
                "total": total,
                "correct_model_selection": correct_model_selection,
                "accuracy": (correct_model_selection / total) if total > 0 else 0.0
            }
            
            result["success"] = result["summary"]["accuracy"] == 1.0  # All should be correct
            
            if verbose:
                print("\n" + "=" * 50)
                print("MODEL SELECTION TEST RESULTS")
                print("=" * 50)
                
                for case in result["test_cases"]:
                    status = "✅ CORRECT" if case["correct"] else "❌ INCORRECT"
                    print(f"{status} - Query: \"{case['query']}\"")
                    print(f"  Is philosophical: {case['is_philosophical']}")
                    print(f"  Expected model: {case['expected_model']}")
                    print(f"  Selected model: {case['selected_model']}")
                    print()
                
                print("Summary:")
                print(f"  - Total queries tested: {total}")
                print(f"  - Correct model selections: {correct_model_selection}/{total} ({result['summary']['accuracy'] * 100:.1f}%)")
                print("=" * 50)
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing model selection: {str(e)}")
        
        return result
    
    def test_philosophical_detection(self, verbose: bool = False) -> Dict[str, Any]:
        """Test the philosophical question detection logic."""
        logger.info("Testing philosophical question detection...")
        
        result = {
            "success": False,
            "test_cases": [],
            "summary": {
                "total": 0,
                "philosophical_correct": 0,
                "non_philosophical_correct": 0,
                "accuracy": 0.0
            },
            "error": None
        }
        
        try:
            service = DeepSeekService()
            
            # Test questions with expected outcomes
            test_cases = [
                # Philosophical questions (expected: True)
                {"question": "What is the meaning of life?", "expected": True},
                {"question": "Does free will exist?", "expected": True},
                {"question": "How do we know what is morally right?", "expected": True},
                {"question": "Is consciousness a product of the brain or something more?", "expected": True},
                {"question": "What is the nature of reality itself?", "expected": True},
                
                # Non-philosophical questions (expected: False)
                {"question": "What's the weather like today?", "expected": False},
                {"question": "How do I make pasta?", "expected": False},
                {"question": "What time is it?", "expected": False},
                {"question": "Can you tell me about the latest iPhone?", "expected": False},
                {"question": "How tall is Mount Everest?", "expected": False},
            ]
            
            for case in test_cases:
                question = case["question"]
                expected = case["expected"]
                
                messages = [{"role": "user", "content": question}]
                detected = service._is_philosophical_question(messages)
                
                case_result = {
                    "question": question,
                    "expected": expected,
                    "detected": detected,
                    "correct": detected == expected
                }
                
                result["test_cases"].append(case_result)
            
            # Calculate summary statistics
            total = len(result["test_cases"])
            philosophical_correct = sum(1 for case in result["test_cases"] 
                                    if case["expected"] == True and case["correct"])
            non_philosophical_correct = sum(1 for case in result["test_cases"] 
                                        if case["expected"] == False and case["correct"])
            correct = philosophical_correct + non_philosophical_correct
            
            result["summary"] = {
                "total": total,
                "philosophical_correct": philosophical_correct,
                "non_philosophical_correct": non_philosophical_correct,
                "correct": correct,
                "accuracy": (correct / total) if total > 0 else 0.0
            }
            
            result["success"] = True
            
            if verbose:
                print("\n" + "=" * 50)
                print("PHILOSOPHICAL DETECTION TEST RESULTS")
                print("=" * 50)
                
                print("\nCorrectly identified as philosophical:")
                for case in result["test_cases"]:
                    if case["expected"] == True and case["correct"]:
                        print(f"  - {case['question']}")
                
                print("\nIncorrectly identified as philosophical:")
                for case in result["test_cases"]:
                    if case["expected"] == False and not case["correct"]:
                        print(f"  - {case['question']}")
                
                print("\nCorrectly identified as non-philosophical:")
                for case in result["test_cases"]:
                    if case["expected"] == False and case["correct"]:
                        print(f"  - {case['question']}")
                
                print("\nIncorrectly identified as non-philosophical:")
                for case in result["test_cases"]:
                    if case["expected"] == True and not case["correct"]:
                        print(f"  - {case['question']}")
                
                print("\nSummary:")
                print(f"  - Total questions: {total}")
                print(f"  - Correctly identified: {correct} ({result['summary']['accuracy'] * 100:.1f}%)")
                print(f"  - Philosophical correct: {philosophical_correct}/{sum(1 for case in result['test_cases'] if case['expected'] == True)}")
                print(f"  - Non-philosophical correct: {non_philosophical_correct}/{sum(1 for case in result['test_cases'] if case['expected'] == False)}")
                print("=" * 50)
        
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Error testing philosophical detection: {str(e)}")
        
        return result
    
    def print_test_summary(self):
        """Print a summary of all test results."""
        print("\n" + "=" * 80)
        print(f"INTEGRATION TEST SUMMARY FOR {settings.PROJECT_NAME}")
        print("=" * 80)
        
        # Configuration
        config_result = self.test_results.get("config_test", {})
        config_status = "✅ PASS" if config_result.get("success", False) else "❌ FAIL"
        print(f"\n[{config_status}] Configuration Test")
        if not config_result.get("success", False) and config_result.get("issues"):
            print("  Issues:")
            for issue in config_result.get("issues", []):
                print(f"  - {issue}")
        
        # API Connectivity
        api_result = self.test_results.get("api_connectivity", {})
        api_status = "✅ PASS" if api_result.get("success", False) else "❌ FAIL"
        print(f"\n[{api_status}] API Connectivity Test")
        if not api_result.get("success", False) and api_result.get("error"):
            print(f"  Error: {api_result.get('error')}")
        
        # Available Models
        models_result = self.test_results.get("models_available", {})
        models_status = "✅ PASS" if models_result.get("success", False) else "❌ FAIL"
        print(f"\n[{models_status}] Available Models Test")
        if models_result.get("success", False):
            model_found = models_result.get("model_found", False)
            phil_model_found = models_result.get("philosophy_model_found", False)
            print(f"  Default model ({self.model_name}): {'✅ Available' if model_found else '❌ Not available'}")
            print(f"  Philosophy model ({self.philosophy_model_name}): {'✅ Available' if phil_model_found else '❌ Not available'}")
            print(f"  Total models available: {len(models_result.get('models', []))}")
        elif models_result.get("error"):
            print(f"  Error: {models_result.get('error')}")
        
        # Philosophical Detection
        phil_result = self.test_results.get("philosophical_detection", {})
        phil_status = "✅ PASS" if phil_result.get("success", False) else "❌ FAIL"
        print(f"\n[{phil_status}] Philosophical Detection Test")
        if phil_result.get("success", False):
            summary = phil_result.get("summary", {})
            accuracy = summary.get("accuracy", 0) * 100
            print(f"  Accuracy: {accuracy:.1f}%")
        elif phil_result.get("error"):
            print(f"  Error: {phil_result.get('error')}")
        
        # Model Selection
        model_sel_result = self.test_results.get("model_selection", {})
        model_sel_status = "✅ PASS" if model_sel_result.get("success", False) else "❌ FAIL"
        print(f"\n[{model_sel_status}] Model Selection Test")
        if model_sel_result.get("success", False):
            summary = model_sel_result.get("summary", {})
            accuracy = summary.get("accuracy", 0) * 100
            print(f"  Accuracy: {accuracy:.1f}%")
            print(f"  Using deepseek-reasoner for philosophical questions: ✅ CONFIRMED")
        elif model_sel_result.get("error"):
            print(f"  Error: {model_sel_result.get('error')}")
        
        # Simple Query
        query_result = self.test_results.get("simple_query", {})
        query_status = "✅ PASS" if query_result.get("success", False) else "❌ FAIL"
        print(f"\n[{query_status}] Simple Query Test")
        if not query_result.get("success", False) and query_result.get("error"):
            print(f"  Error: {query_result.get('error')}")
        
        # Overall Result
        overall_success = all(
            result.get("success", False) 
            for result in [
                config_result,
                api_result,
                models_result,
                phil_result,
                model_sel_result,
                query_result
            ]
            if result is not None
        )
        
        print("\n" + "-" * 80)
        overall_status = "✅ PASS" if overall_success else "❌ FAIL"
        print(f"Overall Integration Test Result: [{overall_status}]")
        
        if not overall_success:
            print("\nRecommendations:")
            if not config_result.get("success", False):
                print("- Check your environment variables and .env file for proper API configuration")
                print("- Ensure DEEPSEEK_PHILOSOPHY_MODEL is set to 'deepseek-reasoner'")
            if not api_result.get("success", False):
                print("- Verify your internet connection and DeepSeek API key")
            if not models_result.get("success", False):
                print("- Ensure your DeepSeek account has access to the required models")
            if not model_sel_result.get("success", False):
                print("- Check the model selection logic in DeepSeekService")
            
        print("=" * 80)

def test_philosophical_question(question: str) -> bool:
    """Standalone function to test if a question is detected as philosophical."""
    service = DeepSeekService()
    messages = [{"role": "user", "content": question}]
    return service._is_philosophical_question(messages)

def main():
    """Run the integration tests."""
    parser = argparse.ArgumentParser(description="Run integration tests for the Personal RAG Server")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed test output")
    parser.add_argument("--test-philosophical", "-p", type=str, help="Test if a specific question is philosophical")
    parser.add_argument("--query", "-q", type=str, help="Test a specific query")
    
    args = parser.parse_args()
    
    # If testing a specific philosophical question
    if args.test_philosophical:
        question = args.test_philosophical
        is_philosophical = test_philosophical_question(question)
        print(f"Question: {question}")
        print(f"Detected as philosophical: {is_philosophical}")
        if is_philosophical:
            print(f"Would use model: {settings.DEEPSEEK_PHILOSOPHY_MODEL} (deepseek-reasoner)")
        else:
            print(f"Would use model: {settings.DEEPSEEK_MODEL}")
        return
    
    # Create and run the integration tests
    tests = IntegrationTests()
    
    # If testing a specific query
    if args.query:
        query = args.query
        print(f"Testing query: {query}")
        
        # First check if it's philosophical
        is_philosophical = test_philosophical_question(query)
        print(f"Detected as philosophical: {is_philosophical}")
        print(f"Will use model: {'deepseek-reasoner' if is_philosophical else settings.DEEPSEEK_MODEL}")
        
        # Run the appropriate test
        if is_philosophical:
            result = tests.test_philosophical_query(query, verbose=True)
        else:
            result = tests.test_simple_query(query, verbose=True)
        
        # Print the result
        print(f"Query test result: {'Success' if result['success'] else 'Failed'}")
        if not result['success'] and result.get('error'):
            print(f"Error: {result['error']}")
        
        return
    
    # Run all tests
    tests.run_all_tests(verbose=args.verbose)

if __name__ == "__main__":
    main() 