import unittest
from unittest.mock import patch, MagicMock
import json
import os
import sys

# Add the root directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app.services.llm_service_base import BaseLLMService
from app.services.openai_service import OpenAIService
from app.services.deepseek_service import DeepSeekService
from app.services.llm_service_factory import LLMServiceFactory
from app.services.provider_config import ProviderConfigFactory, validate_provider_config


class TestOpenAIService(unittest.TestCase):
    """Tests for the OpenAI service implementation."""
    
    @patch('app.services.openai_service.OpenAI')
    def test_initialize_model(self, mock_openai):
        """Test initializing the OpenAI model."""
        service = OpenAIService()
        service.initialize_model()
        
        # Assert that the OpenAI client was initialized
        mock_openai.assert_called_once()
    
    @patch('app.services.openai_service.OpenAI')
    def test_get_llm_response(self, mock_openai):
        """Test getting a response from the OpenAI model."""
        # Set up the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create the service and get a response
        service = OpenAIService()
        messages = [{"role": "user", "content": "Hello"}]
        response = service.get_llm_response(messages)
        
        # Assert the response format
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["content"], "This is a test response")
        self.assertTrue("model" in response)
        
        # Assert the client was called correctly
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('app.services.openai_service.OpenAI')
    def test_generate_with_rag(self, mock_openai):
        """Test generating a response with RAG using the OpenAI model."""
        # Set up the mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a RAG response"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create the service and get a RAG response
        service = OpenAIService()
        messages = [{"role": "user", "content": "What is RAG?"}]
        context = ["RAG stands for Retrieval Augmented Generation", "It combines retrieval with generation"]
        response = service.generate_with_rag(messages, context)
        
        # Assert the response format
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["content"], "This is a RAG response")
        self.assertTrue("model" in response)
        
        # Assert the client was called correctly
        mock_client.chat.completions.create.assert_called_once()


class TestDeepSeekService(unittest.TestCase):
    """Tests for the DeepSeek service implementation."""
    
    @patch('app.services.deepseek_service.requests')
    def test_initialize_model(self, mock_requests):
        """Test initializing the DeepSeek model."""
        service = DeepSeekService()
        service.initialize_model()
        
        # Assert that the headers were initialized correctly
        self.assertIsNotNone(service.headers)
        self.assertTrue("Authorization" in service.headers)
        self.assertTrue("Content-Type" in service.headers)
    
    def test_is_philosophical_question(self):
        """Test the philosophical question detection."""
        service = DeepSeekService()
        
        # Test philosophical questions
        philosophical_messages = [
            [{"role": "user", "content": "What is the meaning of life?"}],
            [{"role": "user", "content": "Is consciousness merely an emergent property of the brain?"}],
            [{"role": "user", "content": "How can we define what is morally right or wrong?"}],
            [{"role": "user", "content": "Does free will exist or is everything determined?"}],
            [{"role": "user", "content": "What did Kant say about the categorical imperative?"}],
            [{"role": "user", "content": "Discuss the problem of existential nihilism."}],
        ]
        
        for messages in philosophical_messages:
            self.assertTrue(service._is_philosophical_question(messages), 
                           f"Failed to detect philosophical question: {messages[0]['content']}")
        
        # Test non-philosophical questions
        non_philosophical_messages = [
            [{"role": "user", "content": "What's the weather like today?"}],
            [{"role": "user", "content": "How do I make pasta?"}],
            [{"role": "user", "content": "Tell me about the latest smartphone."}],
            [{"role": "user", "content": "What's 2+2?"}],
            [{"role": "user", "content": "List the capitals of Europe."}],
        ]
        
        for messages in non_philosophical_messages:
            self.assertFalse(service._is_philosophical_question(messages),
                            f"Incorrectly identified as philosophical: {messages[0]['content']}")
    
    @patch('app.services.deepseek_service.requests.post')
    @patch('app.services.deepseek_service.DeepSeekService._is_philosophical_question')
    def test_get_llm_response_normal(self, mock_is_philosophical, mock_post):
        """Test getting a response for a normal (non-philosophical) question."""
        # Set up the mock
        mock_is_philosophical.return_value = False
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a test response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Create the service and get a response
        service = DeepSeekService()
        service.initialize_model()  # Initialize headers
        service.model_name = "deepseek-chat"
        service.philosophy_model_name = "deepseek-v3-0324"
        
        messages = [{"role": "user", "content": "Hello"}]
        response = service.get_llm_response(messages)
        
        # Assert the response format
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["content"], "This is a test response")
        self.assertEqual(response["model"], "deepseek-chat")
        
        # Assert the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/chat/completions', args[0])
        self.assertIn('headers', kwargs)
        self.assertIn('json', kwargs)
        self.assertEqual(kwargs['json']['model'], "deepseek-chat")
    
    @patch('app.services.deepseek_service.requests.post')
    @patch('app.services.deepseek_service.DeepSeekService._is_philosophical_question')
    def test_get_llm_response_philosophical(self, mock_is_philosophical, mock_post):
        """Test getting a response for a philosophical question."""
        # Set up the mock
        mock_is_philosophical.return_value = True
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a philosophical response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Create the service and get a response
        service = DeepSeekService()
        service.initialize_model()  # Initialize headers
        service.model_name = "deepseek-chat"
        service.philosophy_model_name = "deepseek-v3-0324"
        
        messages = [{"role": "user", "content": "What is the meaning of life?"}]
        response = service.get_llm_response(messages, temperature=0.7)
        
        # Assert the response format
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["content"], "This is a philosophical response")
        self.assertEqual(response["model"], "deepseek-v3-0324")
        
        # Assert the request was made correctly
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn('/chat/completions', args[0])
        self.assertIn('headers', kwargs)
        self.assertIn('json', kwargs)
        self.assertEqual(kwargs['json']['model'], "deepseek-v3-0324")
        # Check that temperature was adjusted
        self.assertLessEqual(kwargs['json']['temperature'], 0.5)
    
    @patch('app.services.deepseek_service.requests.post')
    def test_generate_with_rag(self, mock_post):
        """Test generating a response with RAG using the DeepSeek model."""
        # Set up the mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": "This is a RAG response"
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Create the service and get a RAG response
        service = DeepSeekService()
        service.initialize_model()  # Initialize headers
        
        messages = [{"role": "user", "content": "What is RAG?"}]
        context = ["RAG stands for Retrieval Augmented Generation", "It combines retrieval with generation"]
        response = service.generate_with_rag(messages, context)
        
        # Assert the response format
        self.assertEqual(response["role"], "assistant")
        self.assertEqual(response["content"], "This is a RAG response")
        self.assertTrue("model" in response)
        
        # Assert the request was made correctly
        mock_post.assert_called_once()


class TestLLMServiceFactory(unittest.TestCase):
    """Tests for the LLM service factory."""
    
    @patch('app.services.llm_service_factory.settings')
    def test_create_llm_service_openai(self, mock_settings):
        """Test creating an OpenAI service."""
        # Set up the mock
        mock_settings.LLM_PROVIDER = "openai"
        mock_settings.OPENAI_API_KEY = "test-key"
        
        # Create a service
        service = LLMServiceFactory.create_llm_service()
        
        # Assert the service type
        self.assertIsInstance(service, OpenAIService)
    
    @patch('app.services.llm_service_factory.settings')
    def test_create_llm_service_deepseek(self, mock_settings):
        """Test creating a DeepSeek service."""
        # Set up the mock
        mock_settings.LLM_PROVIDER = "deepseek"
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        
        # Create a service
        service = LLMServiceFactory.create_llm_service()
        
        # Assert the service type
        self.assertIsInstance(service, DeepSeekService)
    
    @patch('app.services.llm_service_factory.settings')
    def test_create_llm_service_invalid(self, mock_settings):
        """Test creating a service with an invalid provider."""
        # Set up the mock
        mock_settings.LLM_PROVIDER = "invalid"
        
        # Assert that creating a service raises an error
        with self.assertRaises(ValueError):
            LLMServiceFactory.create_llm_service()


class TestProviderConfig(unittest.TestCase):
    """Tests for the provider configuration."""
    
    @patch('app.services.provider_config.settings')
    def test_validate_provider_config_openai_valid(self, mock_settings):
        """Test validating OpenAI configuration when valid."""
        # Set up the mock
        mock_settings.OPENAI_API_KEY = "test-key"
        
        # Validate the configuration
        valid = validate_provider_config("openai")
        
        # Assert the validation result
        self.assertTrue(valid)
    
    @patch('app.services.provider_config.settings')
    def test_validate_provider_config_openai_invalid(self, mock_settings):
        """Test validating OpenAI configuration when invalid."""
        # Set up the mock
        mock_settings.OPENAI_API_KEY = ""
        
        # Validate the configuration
        valid = validate_provider_config("openai")
        
        # Assert the validation result
        self.assertFalse(valid)
    
    @patch('app.services.provider_config.settings')
    def test_validate_provider_config_deepseek_valid(self, mock_settings):
        """Test validating DeepSeek configuration when valid."""
        # Set up the mock
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DEEPSEEK_API_URL = "https://api.deepseek.com"
        
        # Validate the configuration
        valid = validate_provider_config("deepseek")
        
        # Assert the validation result
        self.assertTrue(valid)
    
    @patch('app.services.provider_config.settings')
    def test_validate_provider_config_deepseek_invalid(self, mock_settings):
        """Test validating DeepSeek configuration when invalid."""
        # Set up the mock
        mock_settings.DEEPSEEK_API_KEY = "test-key"
        mock_settings.DEEPSEEK_API_URL = ""
        
        # Validate the configuration
        valid = validate_provider_config("deepseek")
        
        # Assert the validation result
        self.assertFalse(valid)
    
    @patch('app.services.provider_config.settings')
    def test_validate_provider_config_invalid(self, mock_settings):
        """Test validating configuration for an invalid provider."""
        # Validate the configuration
        valid = validate_provider_config("invalid")
        
        # Assert the validation result
        self.assertFalse(valid)


if __name__ == '__main__':
    unittest.main() 