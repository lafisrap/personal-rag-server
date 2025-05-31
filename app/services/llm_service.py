"""
This module provides the LLM service used by the application.
It re-exports the llm_service singleton from the factory module,
which provides backward compatibility with existing code.
"""

from app.services.llm_service_factory import llm_service

# The llm_service instance is created by the factory based on the configured provider
# This maintains backward compatibility with existing code using this module
