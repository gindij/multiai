"""
Configuration settings for the multi-AI application.
"""

from typing import Dict, Any

# Default models for each provider
OPENAI_DEFAULT_MODEL: str = "gpt-4.1-2025-04-14"
ANTHROPIC_DEFAULT_MODEL: str = "claude-3-7-sonnet-latest"
GEMINI_DEFAULT_MODEL: str = "gemini-2.5-pro-preview-05-06"

# Model used for judging responses
JUDGE_DEFAULT_PROVIDER: str = "openai"
JUDGE_DEFAULT_MODEL: str = "o3-2025-04-16"

# Default server settings
DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = 8000

# Available models by provider
AVAILABLE_MODELS: Dict[str, Dict[str, Any]] = {
    "openai": {
        "default": OPENAI_DEFAULT_MODEL,
        "models": [
            {"id": "gpt-4.1-2025-04-14", "name": "GPT-4.1", "context_length": 128000},
            {"id": "gpt-4o-2024-11-20", "name": "GPT-4o", "context_length": 128000},
            {"id": "o3-2025-04-16", "name": "o3", "context_length": 128000},
        ],
    },
    "anthropic": {
        "default": ANTHROPIC_DEFAULT_MODEL,
        "models": [
            {
                "id": "claude-3-opus-latest",
                "name": "Claude 3 Opus",
                "context_length": 200000,
            },
            {
                "id": "claude-3-7-sonnet-latest",
                "name": "Claude 3 Sonnet",
                "context_length": 200000,
            },
            {
                "id": "claude-3-5-haiku-latest",
                "name": "Claude 3 Haiku",
                "context_length": 200000,
            },
        ],
    },
    "gemini": {
        "default": GEMINI_DEFAULT_MODEL,
        "models": [
            {
                "id": "gemini-2.5-pro-preview-05-06",
                "name": "Gemini Pro",
                "context_length": 32768,
            },
        ],
    },
}

# Application settings
DEFAULT_TIMEOUT: int = 60  # seconds
