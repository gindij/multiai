import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
from multi_ai.services.comparator import Comparator
from multi_ai.config import (
    OPENAI_DEFAULT_MODEL,
    ANTHROPIC_DEFAULT_MODEL,
    GEMINI_DEFAULT_MODEL,
)


@pytest.fixture
def mock_models():
    with patch("multi_ai.services.comparator.OpenAIModel") as mock_openai, patch(
        "multi_ai.services.comparator.AnthropicModel"
    ) as mock_anthropic, patch(
        "multi_ai.services.comparator.GeminiModel"
    ) as mock_gemini, patch(
        "multi_ai.services.comparator.Judge"
    ) as mock_judge:

        # Setup model instances
        mock_openai_instance = AsyncMock()
        mock_anthropic_instance = AsyncMock()
        mock_gemini_instance = AsyncMock()
        mock_judge_instance = AsyncMock()

        # Configure mock returns
        mock_openai.return_value = mock_openai_instance
        mock_anthropic.return_value = mock_anthropic_instance
        mock_gemini.return_value = mock_gemini_instance
        mock_judge.return_value = mock_judge_instance

        # Return all mocks
        return {
            "openai": mock_openai_instance,
            "anthropic": mock_anthropic_instance,
            "gemini": mock_gemini_instance,
            "judge": mock_judge_instance,
        }


@pytest.fixture
def comparator():
    with patch("multi_ai.models.openai_model.OpenAIModel") as mock_openai, patch(
        "multi_ai.models.anthropic_model.AnthropicModel"
    ) as mock_anthropic, patch(
        "multi_ai.models.gemini_model.GeminiModel"
    ) as mock_gemini, patch(
        "multi_ai.services.judge.Judge"
    ) as mock_judge:
        return Comparator(use_blending=False)


class TestComparator:

    def test_initialization(self, mock_models):
        """Test that the Comparator initializes correctly."""
        with patch("multi_ai.services.comparator.Judge") as mock_judge:
            # Create a new instance with the mock we can directly observe
            comparator = Comparator(use_blending=True)

            # Check models are set up
            assert "openai" in comparator.models
            assert "anthropic" in comparator.models
            assert "gemini" in comparator.models

            # Check judge is initialized with blending
            mock_judge.assert_called_once_with(blend_responses=True)

    @pytest.mark.asyncio
    async def test_query_with_fallback_success(self, comparator):
        """Test successful query with fallback."""
        # Create a direct mock for the model's query method
        model_mock = AsyncMock()
        model_mock.query.return_value = {
            "provider": "OpenAI",
            "model": "gpt-4",
            "response": "Test response from OpenAI",
            "success": True,
        }

        # Replace the model in the comparator
        comparator.models["openai"] = model_mock

        result = await comparator._query_with_fallback("openai", "gpt-4", "Test prompt")

        model_mock.query.assert_called_once_with("Test prompt", "gpt-4")
        assert result["provider"] == "OpenAI"
        assert result["model"] == "gpt-4"
        assert result["response"] == "Test response from OpenAI"
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_query_with_fallback_error(self, comparator):
        """Test query with fallback handling an error."""
        # Create a direct mock for the model's query method
        model_mock = AsyncMock()
        model_mock.query.side_effect = Exception("API error")

        # Replace the model in the comparator
        comparator.models["openai"] = model_mock

        result = await comparator._query_with_fallback("openai", "gpt-4", "Test prompt")

        model_mock.query.assert_called_once_with("Test prompt", "gpt-4")
        assert result["provider"] == "openai"
        assert result["model"] == "gpt-4"
        assert "Query failed: API error" in result["error"]
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_compare_default_models(self, comparator):
        """Test compare using default models."""
        # Setup responses
        openai_response = {
            "provider": "OpenAI",
            "model": OPENAI_DEFAULT_MODEL,
            "response": "OpenAI response",
            "success": True,
        }
        anthropic_response = {
            "provider": "Anthropic",
            "model": ANTHROPIC_DEFAULT_MODEL,
            "response": "Anthropic response",
            "success": True,
        }
        gemini_response = {
            "provider": "Google Gemini",
            "model": GEMINI_DEFAULT_MODEL,
            "response": "Gemini response",
            "success": True,
        }

        # Create direct mocks for the models
        openai_mock = AsyncMock()
        anthropic_mock = AsyncMock()
        gemini_mock = AsyncMock()
        judge_mock = AsyncMock()

        openai_mock.query.return_value = openai_response
        anthropic_mock.query.return_value = anthropic_response
        gemini_mock.query.return_value = gemini_response

        # Replace the models in the comparator
        comparator.models["openai"] = openai_mock
        comparator.models["anthropic"] = anthropic_mock
        comparator.models["gemini"] = gemini_mock
        comparator.judge = judge_mock

        # Setup judge response
        judge_mock.evaluate.return_value = {
            "result": "OpenAI response",
            "best_response": openai_response,
            "method": "select",
            "success": True,
        }

        # Call compare
        result = await comparator.compare("Test prompt")

        # Verify models were queried with default models
        openai_mock.query.assert_called_once_with("Test prompt", OPENAI_DEFAULT_MODEL)
        anthropic_mock.query.assert_called_once_with(
            "Test prompt", ANTHROPIC_DEFAULT_MODEL
        )
        gemini_mock.query.assert_called_once_with("Test prompt", GEMINI_DEFAULT_MODEL)

        # Verify judge was called with all responses
        judge_mock.evaluate.assert_called_once()

        # Check result
        assert result["result"] == "OpenAI response"
        assert result["best_response"] == openai_response
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_compare_custom_models(self, comparator):
        """Test compare with custom model configurations."""
        # Setup model configs
        model_configs = {"openai": "gpt-4-turbo", "anthropic": "claude-3-opus-20240229"}

        # Setup responses
        openai_response = {
            "provider": "OpenAI",
            "model": "gpt-4-turbo",
            "response": "OpenAI response",
            "success": True,
        }
        anthropic_response = {
            "provider": "Anthropic",
            "model": "claude-3-opus-20240229",
            "response": "Anthropic response",
            "success": True,
        }

        # Create direct mocks for the models
        openai_mock = AsyncMock()
        anthropic_mock = AsyncMock()
        judge_mock = AsyncMock()

        openai_mock.query.return_value = openai_response
        anthropic_mock.query.return_value = anthropic_response

        # Replace the models in the comparator
        comparator.models["openai"] = openai_mock
        comparator.models["anthropic"] = anthropic_mock
        comparator.judge = judge_mock

        # Setup judge response
        judge_mock.evaluate.return_value = {
            "result": "Anthropic response",
            "best_response": anthropic_response,
            "method": "select",
            "success": True,
        }

        # Call compare
        result = await comparator.compare("Test prompt", model_configs)

        # Verify only specified models were queried
        openai_mock.query.assert_called_once_with("Test prompt", "gpt-4-turbo")
        anthropic_mock.query.assert_called_once_with(
            "Test prompt", "claude-3-opus-20240229"
        )

        # Check result
        assert result["result"] == "Anthropic response"
        assert result["best_response"] == anthropic_response
        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_compare_all_responses_failed(self, comparator, mock_models):
        """Test compare when all responses fail."""
        # Make all model calls fail
        mock_models["openai"].query.side_effect = Exception("OpenAI API error")
        mock_models["anthropic"].query.side_effect = Exception("Anthropic API error")
        mock_models["gemini"].query.side_effect = Exception("Gemini API error")

        # Call compare
        result = await comparator.compare("Test prompt")

        # Verify result
        assert result["success"] is False
        assert "All models failed to respond" in result["result"]
        assert mock_models["judge"].evaluate.call_count == 0

    @pytest.mark.asyncio
    async def test_compare_some_responses_failed(self, comparator):
        """Test compare when some responses fail but others succeed."""
        # Setup responses
        openai_response = {
            "provider": "OpenAI",
            "model": OPENAI_DEFAULT_MODEL,
            "response": "OpenAI response",
            "success": True,
        }

        # Create direct mocks for the models
        openai_mock = AsyncMock()
        anthropic_mock = AsyncMock()
        gemini_mock = AsyncMock()
        judge_mock = AsyncMock()

        openai_mock.query.return_value = openai_response
        anthropic_mock.query.side_effect = Exception("Anthropic API error")
        gemini_mock.query.side_effect = Exception("Gemini API error")

        # Replace the models in the comparator
        comparator.models["openai"] = openai_mock
        comparator.models["anthropic"] = anthropic_mock
        comparator.models["gemini"] = gemini_mock
        comparator.judge = judge_mock

        # Setup judge response
        judge_mock.evaluate.return_value = {
            "result": "OpenAI response",
            "best_response": openai_response,
            "method": "single",
            "reason": "Only one successful response available",
            "success": True,
        }

        # Call compare
        result = await comparator.compare("Test prompt")

        # Verify judge was called with only successful responses
        judge_mock.evaluate.assert_called_once()

        # Check result
        assert result["success"] is True
        assert result["result"] == "OpenAI response"
        assert result["method"] == "single"
