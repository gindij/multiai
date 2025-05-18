import asyncio
from typing import List, Dict, Any, Optional
from ..models.openai_model import OpenAIModel
from ..models.anthropic_model import AnthropicModel
from ..models.gemini_model import GeminiModel
from ..config import (
    OPENAI_DEFAULT_MODEL,
    ANTHROPIC_DEFAULT_MODEL,
    GEMINI_DEFAULT_MODEL,
)
from .judge import Judge


class Comparator:
    """Main service to query multiple AI providers and compare their responses."""

    def __init__(self, use_blending: bool = False) -> None:
        """
        Initialize the comparator with model instances.

        Args:
            use_blending: Whether to blend responses using weights instead of selecting one
        """
        self.models = {
            "openai": OpenAIModel(),
            "anthropic": AnthropicModel(),
            "gemini": GeminiModel(),
        }
        self.judge = Judge(blend_responses=use_blending)

    async def compare(
        self,
        prompt: str,
        model_configs: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Query multiple AI providers and compare their responses.

        Args:
            prompt: The user's prompt to send to all models
            model_configs: Optional mapping of provider -> model name
                          (defaults to config settings if not provided)

        Returns:
            Dictionary containing the best/blended response and evaluation details
        """
        # Use default models if not specified
        if model_configs is None:
            model_configs = {
                "openai": OPENAI_DEFAULT_MODEL,
                "anthropic": ANTHROPIC_DEFAULT_MODEL,
                "gemini": GEMINI_DEFAULT_MODEL,
            }

        # Create tasks for querying each model
        tasks = []
        providers = []

        for provider, model in model_configs.items():
            if provider in self.models:
                task = self._query_with_fallback(provider, model, prompt)
                tasks.append(task)
                providers.append(provider)

        # Execute all queries concurrently
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Process responses
        processed_responses = []
        for i, response in enumerate(responses):
            provider = providers[i]

            # If response is an exception, log it
            if isinstance(response, Exception):
                print(f"Error from {provider}: {str(response)}")
            else:
                # Add the response to processed responses
                processed_responses.append(response)

        # Only keep successful responses
        successful_responses = [
            r for r in processed_responses if r.get("success", False)
        ]

        # Print debug info
        print(f"Received {len(successful_responses)} successful responses")

        # If no successful responses, return error
        if not successful_responses:
            return {
                "result": "All models failed to respond. Please try again.",
                "success": False,
            }

        # Let the judge evaluate the responses
        result = await self.judge.evaluate(prompt, successful_responses)

        return result

    async def _query_with_fallback(
        self, provider: str, model: str, prompt: str
    ) -> Dict[str, Any]:
        """Query a model with error handling and fallback."""
        try:
            return await self.models[provider].query(prompt, model)
        except Exception as e:
            # Return a structured error response instead of propagating the exception
            return {
                "provider": provider,
                "model": model,
                "error": f"Query failed: {str(e)}",
                "success": False,
            }
