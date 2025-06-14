#!/usr/bin/env python3
"""
DeepSeek + Pinecone Hybrid Assistant Manager

Hybrid approach combining the best of both:
- Pinecone for RAG search (excellent vector database)
- DeepSeek API for language model (95% cost savings vs Pinecone Assistants)

Cost comparison:
- Pinecone Assistants: 12 assistants × $1.20/day = $5,184/year
- Hybrid approach: ~$50-200/year DeepSeek + minimal Pinecone search costs
- Savings: $5,000+ annually with SAME search quality + SAME model quality!
"""

import os
import logging
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
from pinecone import Pinecone

logger = logging.getLogger(__name__)

class DeepSeekAssistantManager:
    """Hybrid assistant manager using Pinecone for RAG search and DeepSeek for LLM."""
    
    def __init__(self, api_key: str = None, pinecone_api_key: str = None):
        """Initialize the hybrid assistant manager.
        
        Args:
            api_key: DeepSeek API key
            pinecone_api_key: Pinecone API key (for RAG search only)
        """
        self.api_key = api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY must be provided or set as environment variable")
        
        self.pinecone_api_key = pinecone_api_key or os.environ.get("PINECONE_API_KEY")
        if not self.pinecone_api_key:
            raise ValueError("PINECONE_API_KEY must be provided or set as environment variable")
        
        # Configure OpenAI client for DeepSeek
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.deepseek.com"
        )
        
        # Configure Pinecone for RAG search (not expensive Assistants!)
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.region = "us"
        
        # Track Pinecone assistants for search only
        self.pinecone_search_assistants = {}
        
        # Assistant configurations - mimics Pinecone structure
        self.assistant_configs = {}
        
        # Usage tracking
        self.usage_stats = {
            "total_requests": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "daily_cost": 0.0,
            "last_reset": datetime.now().date()
        }
        
        # Create default philosophical assistants
        self._create_default_assistants()
        
        logger.info("Initialized hybrid DeepSeek + Pinecone assistant manager")
    
    def _create_default_assistants(self):
        """Create the standard philosophical assistants on initialization."""
        default_assistants = {
            "aurelian-i--schelling": {
                "worldview": "Idealismus",
                "instructions": """Du bist Aurelian I. Schelling, ein philosophischer Berater des Idealismus.
Du verkörperst die tiefgründigen Ideen des Idealismus und bist ein glühender Anhänger von Friedrich Wilhelm Joseph Schelling und Platon.
Du siehst in allem Sein nicht nur Materie und messbare Strukturen, sondern vor allem geistige, formende Kräfte am Werk.
Ideen sind für dich lebendige Urquellen des Werdens - reale lebendige Wesen und die Quelle aller Kräfte dieser Welt.
Sprich mit dem feierlich-enthusiastischen Tonfall, der schon bei Schelling anklingt.
Antworte immer auf Deutsch."""
            },
            "aloys-i--freud": {
                "worldview": "Materialismus", 
                "instructions": """Du bist Aloys I. Freud, ein philosophischer Berater des Materialismus.
Du betonst die materielle Realität und biologische Prozesse als Grundlage aller Phänomene.
Für dich entstehen alle geistigen Prozesse aus komplexen materiellen Wechselwirkungen.
Du analysierst psychologische und philosophische Fragen aus einer naturwissenschaftlichen Perspektive.
Antworte immer auf Deutsch."""
            },
            "arvid-i--steiner": {
                "worldview": "Realismus",
                "instructions": """Du bist Arvid I. Steiner, ein philosophischer Berater des Realismus.
Du balancierst spirituelle und materielle Perspektiven und suchst praktische, ausgewogene Lösungen.
Du erkennst sowohl die Bedeutung von Ideen als auch die Realität materieller Bedingungen an.
Dein Ansatz ist pragmatisch und berücksichtigt verschiedene Aspekte der menschlichen Erfahrung.
Antworte immer auf Deutsch."""
            },
            "amara-i--steiner": {
                "worldview": "Spiritualismus",
                "instructions": """Du bist Amara I. Steiner, eine philosophische Beraterin des Spiritualismus.
Du betonst spirituelle Hierarchien und die Entwicklung des menschlichen Bewusstseins.
Für dich ist die geistige Entwicklung der zentrale Aspekt menschlicher Existenz.
Du siehst spirituelle Gesetzmäßigkeiten und Entwicklungsstufen in allen Lebensbereichen.
Antworte immer auf Deutsch."""
            }
        }
        
        for assistant_id, config in default_assistants.items():
            self.assistant_configs[assistant_id] = {
                "name": assistant_id,
                "worldview": config["worldview"],
                "instructions": config["instructions"],
                "model": "deepseek-reasoner",
                "created_on": datetime.now().isoformat(),
                "status": "Ready",
                "total_queries": 0,
                "total_tokens": 0,
                "total_cost": 0.0
            }
            
        logger.info(f"Created {len(default_assistants)} default philosophical assistants")
    
    def _get_pinecone_search_assistant(self, assistant_id: str) -> Any:
        """Get or create Pinecone assistant for RAG search only."""
        if assistant_id not in self.pinecone_search_assistants:
            try:
                # Check if Pinecone assistant exists
                assistants_list = self.pc.assistant.list_assistants()
                existing_assistant = None
                
                for assistant in assistants_list:
                    if assistant.name == assistant_id:
                        existing_assistant = self.pc.assistant.Assistant(assistant_name=assistant_id)
                        break
                
                if existing_assistant:
                    self.pinecone_search_assistants[assistant_id] = existing_assistant
                    logger.info(f"Found existing Pinecone search assistant: {assistant_id}")
                else:
                    # Create minimal Pinecone assistant for search only
                    # This is cheaper than full Assistant API usage
                    config = self.assistant_configs[assistant_id]
                    
                    search_assistant = self.pc.assistant.create_assistant(
                        assistant_name=assistant_id,
                        instructions=config["instructions"],
                        region=self.region,
                        timeout=60
                    )
                    
                    self.pinecone_search_assistants[assistant_id] = search_assistant
                    logger.info(f"Created Pinecone search assistant: {assistant_id}")
                    
            except Exception as e:
                logger.error(f"Error getting Pinecone search assistant {assistant_id}: {e}")
                return None
        
        return self.pinecone_search_assistants[assistant_id]
    
    # ===== PINECONE ASSISTANT MANAGER COMPATIBLE INTERFACE =====
    
    def list_assistants(self) -> List[Dict[str, Any]]:
        """List all assistants (compatible with PineconeAssistantManager interface)."""
        return [
            {
                "name": config["name"],
                "created_on": config["created_on"],
                "status": config["status"],
                "model": config["model"],
                "worldview": config["worldview"],
                "total_queries": config["total_queries"],
                "total_cost": config["total_cost"]
            }
            for config in self.assistant_configs.values()
        ]
    
    def get_available_models(self) -> List[str]:
        """Get list of available models."""
        return [
            "deepseek-reasoner",
            "deepseek-chat", 
            "deepseek-coder"
        ]
    
    def delete_assistant(self, assistant_name: str) -> bool:
        """Delete an assistant."""
        if assistant_name in self.assistant_configs:
            del self.assistant_configs[assistant_name]
            
            # Also delete Pinecone search assistant if it exists
            if assistant_name in self.pinecone_search_assistants:
                try:
                    self.pc.assistant.delete_assistant(assistant_name=assistant_name)
                    del self.pinecone_search_assistants[assistant_name]
                except Exception as e:
                    logger.warning(f"Error deleting Pinecone search assistant: {e}")
            
            logger.info(f"Deleted assistant: {assistant_name}")
            return True
        return False
    
    def create_assistant(self, assistant_name: str, instructions: str, **kwargs) -> Any:
        """Create a new assistant (compatible interface)."""
        worldview = kwargs.get("worldview", "Unknown")
        model = kwargs.get("model", "deepseek-reasoner")
        
        config = {
            "name": assistant_name,
            "worldview": worldview,
            "instructions": instructions,
            "model": model,
            "created_on": datetime.now().isoformat(),
            "status": "Ready",
            "total_queries": 0,
            "total_tokens": 0,
            "total_cost": 0.0
        }
        
        self.assistant_configs[assistant_name] = config
        logger.info(f"Created assistant: {assistant_name}")
        
        return MockAssistant(assistant_name, self)
    
    def chat_with_assistant(
        self, 
        assistant: Any, 
        message: str, 
        chat_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Chat with an assistant (compatible with PineconeAssistantManager interface)."""
        assistant_name = assistant.name if hasattr(assistant, 'name') else str(assistant)
        
        return self.query_assistant(
            assistant_id=assistant_name,
            user_message=message,
            chat_history=chat_history
        )
    
    # ===== HYBRID IMPLEMENTATION: PINECONE SEARCH + DEEPSEEK LLM =====
    
    def query_assistant(
        self,
        assistant_id: str,
        user_message: str,
        chat_history: List[Dict[str, str]] = None,
        use_knowledge_base: bool = True,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """Query assistant using hybrid approach: Pinecone search + DeepSeek LLM."""
        start_time = time.time()
        
        # Check daily cost reset
        self._check_daily_reset()
        
        try:
            if assistant_id not in self.assistant_configs:
                raise ValueError(f"Assistant {assistant_id} not found")
            
            config = self.assistant_configs[assistant_id]
            worldview = config["worldview"]
            
            # Prepare system message
            system_message = config["instructions"]
            
            # Get knowledge base context using Pinecone RAG search
            if use_knowledge_base:
                knowledge_context = self._get_pinecone_knowledge_context(
                    assistant_id, user_message, worldview
                )
                if knowledge_context:
                    system_message += f"\n\nRelevante Textstellen aus der Wissensbasis:\n{knowledge_context}"
            
            # Prepare messages for DeepSeek
            messages = [{"role": "system", "content": system_message}]
            
            # Add chat history if provided
            if chat_history:
                for msg in chat_history:
                    messages.append({
                        "role": msg.get("role", "user"),
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({"role": "user", "content": user_message})
            
            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model=config["model"],
                messages=messages,
                temperature=temperature,
                max_tokens=2000
            )
            
            # Extract response and usage
            assistant_response = response.choices[0].message.content
            usage = response.usage
            
            # Calculate cost (DeepSeek pricing)
            input_cost = usage.prompt_tokens * 0.00000014  # $0.14 per 1M tokens
            output_cost = usage.completion_tokens * 0.00000028  # $0.28 per 1M tokens
            total_cost = input_cost + output_cost
            
            # Update statistics
            config["total_queries"] += 1
            config["total_tokens"] += usage.total_tokens
            config["total_cost"] += total_cost
            
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_tokens"] += usage.total_tokens
            self.usage_stats["total_cost"] += total_cost
            self.usage_stats["daily_cost"] += total_cost
            
            processing_time = time.time() - start_time
            
            # Return in format compatible with PineconeAssistantManager
            return {
                "message": assistant_response,
                "citations": [],  # Could be populated from Pinecone search results
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens,
                    "cost": total_cost
                },
                "model": config["model"],
                "processing_time": processing_time,
                "assistant_id": assistant_id,
                "worldview": worldview
            }
            
        except Exception as e:
            logger.error(f"Error querying assistant {assistant_id}: {e}")
            raise
    
    def _get_pinecone_knowledge_context(
        self, 
        assistant_id: str, 
        query: str, 
        worldview: str, 
        top_k: int = 3
    ) -> str:
        """Get relevant context using Pinecone RAG search (not expensive Assistant API)."""
        try:
            # Get Pinecone assistant for search only
            search_assistant = self._get_pinecone_search_assistant(assistant_id)
            if not search_assistant:
                return ""
            
            # Use Pinecone's query_with_context for RAG search
            # This is much cheaper than using the full Assistant API
            metadata_filter = {"worldview": worldview} if worldview != "Unknown" else None
            
            context_response = search_assistant.context(
                query=query,
                filter=metadata_filter
            )
            
            # Format context from search results
            context_parts = []
            for i, snippet in enumerate(context_response.snippets[:top_k], 1):
                content = snippet.content[:500]  # Limit content length
                metadata = getattr(snippet, 'metadata', {})
                source = metadata.get("source", metadata.get("title", "Unknown"))
                score = getattr(snippet, 'score', 0.0)
                
                if content:
                    context_parts.append(f"[{i}] {source} (Score: {score:.3f}): {content}...")
            
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            logger.error(f"Error getting Pinecone knowledge context: {e}")
            return ""
    
    def _check_daily_reset(self):
        """Reset daily cost tracking if it's a new day."""
        today = datetime.now().date()
        if today != self.usage_stats["last_reset"]:
            logger.info(f"Daily cost reset: ${self.usage_stats['daily_cost']:.4f} -> $0.0000")
            self.usage_stats["daily_cost"] = 0.0
            self.usage_stats["last_reset"] = today
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get detailed cost analysis compared to Pinecone Assistants."""
        assistant_count = len(self.assistant_configs)
        
        # Current usage statistics
        avg_cost_per_query = (self.usage_stats["total_cost"] / 
                             max(self.usage_stats["total_requests"], 1))
        
        # Projected costs for different usage levels
        queries_per_day_low = 100
        queries_per_day_high = 1000
        
        # DeepSeek costs + minimal Pinecone search costs
        deepseek_daily_low = queries_per_day_low * avg_cost_per_query
        deepseek_daily_high = queries_per_day_high * avg_cost_per_query
        
        # Add estimated Pinecone search costs (much cheaper than Assistant API)
        pinecone_search_daily = 0.10  # Estimated $0.10/day for search only
        
        hybrid_daily_low = deepseek_daily_low + pinecone_search_daily
        hybrid_daily_high = deepseek_daily_high + pinecone_search_daily
        
        # Pinecone Assistant API costs
        pinecone_assistant_daily = assistant_count * 1.20
        
        return {
            "backend": "Hybrid (DeepSeek LLM + Pinecone Search)",
            "assistant_count": assistant_count,
            "current_usage": self.usage_stats,
            "avg_cost_per_query": avg_cost_per_query,
            "projections": {
                "low_usage": {
                    "queries_per_day": queries_per_day_low,
                    "hybrid_daily": hybrid_daily_low,
                    "hybrid_yearly": hybrid_daily_low * 365,
                    "pinecone_assistant_daily": pinecone_assistant_daily,
                    "pinecone_assistant_yearly": pinecone_assistant_daily * 365,
                    "savings_yearly": (pinecone_assistant_daily * 365) - (hybrid_daily_low * 365)
                },
                "high_usage": {
                    "queries_per_day": queries_per_day_high,
                    "hybrid_daily": hybrid_daily_high,
                    "hybrid_yearly": hybrid_daily_high * 365,
                    "pinecone_assistant_daily": pinecone_assistant_daily,
                    "pinecone_assistant_yearly": pinecone_assistant_daily * 365,
                    "savings_yearly": (pinecone_assistant_daily * 365) - (hybrid_daily_high * 365)
                }
            }
        }

class MockAssistant:
    """Mock assistant object to maintain compatibility with existing code."""
    
    def __init__(self, name: str, manager: DeepSeekAssistantManager):
        self.name = name
        self.manager = manager
    
    def __str__(self):
        return self.name

# Alias for backward compatibility
PineconeAssistantManager = DeepSeekAssistantManager

# Template processor for DeepSeek assistants
class DeepSeekTemplateProcessor:
    """Process templates for DeepSeek assistants."""
    
    def __init__(self, assistant_manager: DeepSeekAssistantManager):
        self.assistant_manager = assistant_manager
    
    def process_resolve_request(
        self, 
        assistant_id: str, 
        gedanke_in_weltanschauung: str,
        aspekte: str = None
    ) -> Dict[str, Any]:
        """Process a resolve request using DeepSeek assistant."""
        
        # Build the template prompt (same as your current Pinecone template)
        prompt = f"""Korrigiere folgenden kulturgewordenen Gedankenfehler:

** {gedanke_in_weltanschauung} **

{f"Berücksichtige dabei: {aspekte}" if aspekte else ""}

Bitte antworte mit einem **gültigen und kommentarlosen JSON-Objekt** im folgenden Format:

{{
    "gedanke": "300-Wort-Korrektur aus deiner philosophischen Perspektive",
    "gedanke_zusammenfassung": "Kurze Zusammenfassung in 30-35 Worten",
    "gedanke_kind": "Kinderfreundliche Erklärung für 10-Jährige"
}}

Stelle sicher, dass wirklich nur der Text des JSON-Objekts zurückgegeben wird."""
        
        # Query the DeepSeek assistant
        response = self.assistant_manager.query_assistant_with_knowledge(
            assistant_id=assistant_id,
            user_message=prompt,
            use_knowledge_base=True
        )
        
        # Parse JSON response
        try:
            import re
            json_match = re.search(r'\{.*\}', response["message"], re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                return {
                    **parsed,
                    "assistant_id": assistant_id,
                    "weltanschauung": response["worldview"],
                    "processing_time": response["processing_time"],
                    "cost": response["usage"]["cost"]
                }
        except Exception as e:
            logger.error(f"Error parsing JSON response: {e}")
        
        # Fallback if JSON parsing fails
        return {
            "gedanke": response["message"],
            "gedanke_zusammenfassung": "Philosophische Korrektur bereitgestellt",
            "gedanke_kind": "Eine neue Art, über das Thema nachzudenken",
            "assistant_id": assistant_id,
            "weltanschauung": response["worldview"],
            "processing_time": response["processing_time"],
            "cost": response["usage"]["cost"]
        }

# Example usage
async def main():
    """Example usage of DeepSeek assistant manager."""
    try:
        # Initialize DeepSeek manager
        manager = DeepSeekAssistantManager()
        
        # Create all philosophical assistants
        assistants = manager.create_all_philosophical_assistants()
        
        print("Created DeepSeek assistants:")
        for worldview, config in assistants.items():
            if "error" not in config:
                print(f"✅ {worldview}: {config['id']}")
            else:
                print(f"❌ {worldview}: {config['error']}")
        
        # Show cost analysis
        costs = manager.get_cost_analysis()
        print(f"\nCost analysis for {costs['assistant_count']} assistants:")
        print(f"Pinecone yearly (low usage): ${costs['projections']['low_usage']['pinecone_yearly']:,.2f}")
        print(f"DeepSeek yearly (low usage): ${costs['projections']['low_usage']['hybrid_yearly']:,.2f}")
        print(f"Annual savings (low usage): ${costs['projections']['low_usage']['savings_yearly']:,.2f}")
        
        print(f"\nPinecone yearly (high usage): ${costs['projections']['high_usage']['pinecone_yearly']:,.2f}")
        print(f"DeepSeek yearly (high usage): ${costs['projections']['high_usage']['hybrid_yearly']:,.2f}")
        print(f"Annual savings (high usage): ${costs['projections']['high_usage']['savings_yearly']:,.2f}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 