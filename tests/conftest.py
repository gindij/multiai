import os
import pytest
from typing import Dict, Any, List, Tuple
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


# Add project root to Python path to find modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


# Configure pytest-asyncio
def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    This ensures async tests are properly recognized and executed.
    """
    config.addinivalue_line("markers", "asyncio: mark test as async")


@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Set up environment variables for testing.

    This fixture runs automatically for all tests and manages API keys
    by setting test values before tests and restoring original values afterward.

    The keys set are:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    - GEMINI_API_KEY
    """
    # Save existing environment variables to restore them later
    env_backup = {}
    for key in ["OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY"]:
        env_backup[key] = os.environ.get(key)

    # Set dummy API keys for testing - these will be used by model classes
    os.environ["OPENAI_API_KEY"] = "test-openai-key"
    os.environ["ANTHROPIC_API_KEY"] = "test-anthropic-key"
    os.environ["GEMINI_API_KEY"] = "test-gemini-key"

    yield

    # Restore original environment variables to avoid affecting other tests
    for key, val in env_backup.items():
        if val is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = val


@pytest.fixture
def openai_response() -> Dict[str, Any]:
    """
    Sample OpenAI model response.

    Returns a dictionary containing a successful response from an OpenAI model,
    formatted according to the application's expected response structure.
    Used for testing response handling without calling the actual API.
    """
    return {
        "provider": "OpenAI",
        "model": "gpt-4",
        "response": "This is a test response from OpenAI.",
        "success": True,
    }


@pytest.fixture
def anthropic_response() -> Dict[str, Any]:
    """
    Sample Anthropic model response.

    Returns a dictionary containing a successful response from an Anthropic model,
    formatted according to the application's expected response structure.
    Used for testing response handling without calling the actual API.
    """
    return {
        "provider": "Anthropic",
        "model": "claude-3-opus",
        "response": "This is a test response from Anthropic.",
        "success": True,
    }


@pytest.fixture
def gemini_response() -> Dict[str, Any]:
    """
    Sample Gemini model response.

    Returns a dictionary containing a successful response from a Google Gemini model,
    formatted according to the application's expected response structure.
    Used for testing response handling without calling the actual API.
    """
    return {
        "provider": "Google Gemini",
        "model": "gemini-pro",
        "response": "This is a test response from Google Gemini.",
        "success": True,
    }


@pytest.fixture
def failed_response() -> Dict[str, Any]:
    """
    Sample failed model response.

    Returns a dictionary representing a failed API call to a model,
    with appropriate error message and success=False flag.
    Used for testing error handling without triggering actual API errors.
    """
    return {
        "provider": "OpenAI",
        "model": "gpt-4",
        "error": "API error: rate limit exceeded",
        "success": False,
    }


@pytest.fixture
def comparison_result() -> Dict[str, Any]:
    """
    Sample comparison result from the Comparator service.

    Returns a dictionary representing the result of comparing multiple model responses,
    where a single best response was selected (not blended).

    This fixture is useful for testing downstream components that process the
    Comparator's output without needing to run the actual comparison logic.
    """
    return {
        "result": "This is a test response from OpenAI.",
        "best_response": {
            "provider": "OpenAI",
            "model": "gpt-4",
            "response": "This is a test response from OpenAI.",
            "success": True,
        },
        "method": "select",  # Indicates a single response was selected (not blended)
        "reason": "Selected response 1",
        "judge_response": "1",  # Raw judge output (selected first response)
        "success": True,
    }


@pytest.fixture
def blended_result() -> Dict[str, Any]:
    """
    Sample blended result from the Comparator service.

    Returns a dictionary representing the result of comparing multiple model responses,
    where responses were weighted and blended into a single response.

    Features:
    - Contains the blended response text in 'result'
    - Includes weights assigned to each model response
    - Contains the original responses that were blended
    - Has metadata about the blending process

    This fixture is useful for testing downstream components that process the
    Comparator's output in blending mode without running the actual comparison logic.
    """
    return {
        "result": "This is a blended response combining insights from multiple models.",
        "weights": [0.6, 0.3, 0.1],  # Normalized weights used for blending
        "responses": [
            {
                "provider": "OpenAI",
                "model": "gpt-4",
                "response": "This is a test response from OpenAI.",
                "success": True,
            },
            {
                "provider": "Anthropic",
                "model": "claude-3-opus",
                "response": "This is a test response from Anthropic.",
                "success": True,
            },
            {
                "provider": "Google Gemini",
                "model": "gemini-pro",
                "response": "This is a test response from Google Gemini.",
                "success": True,
            },
        ],
        "method": "blend",  # Indicates responses were blended together
        "judge_response": '{"weights": [6, 3, 1]}',  # Raw judge output with weights
        "success": True,
    }


@pytest.fixture
def mock_model_instance():
    """
    Creates a mock model instance that can be used for testing.

    This mock has standard methods implemented with AsyncMock to allow
    tests to verify calls and provide custom return values without
    requiring real API calls.
    """
    mock = AsyncMock()
    # Set default successful response
    mock.query.return_value = {
        "provider": "TestProvider",
        "model": "test-model",
        "response": "This is a test response",
        "success": True,
    }
    return mock


@pytest.fixture
def sample_responses():
    """
    A list of sample responses from different AI providers.

    Used to test functionality that needs to handle multiple model responses,
    such as the Judge and Comparator services.
    """
    return [
        {
            "provider": "OpenAI",
            "model": "gpt-4",
            "response": "Response from OpenAI model",
            "success": True,
        },
        {
            "provider": "Anthropic",
            "model": "claude-3-opus",
            "response": "Response from Anthropic model",
            "success": True,
        },
        {
            "provider": "Google Gemini",
            "model": "gemini-pro",
            "response": "Response from Google Gemini model",
            "success": True,
        },
    ]
