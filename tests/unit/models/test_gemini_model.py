import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from multi_ai.models.gemini_model import GeminiModel
from multi_ai.config import GEMINI_DEFAULT_MODEL


@pytest.fixture
def mock_genai_client():
    with patch("google.genai.client.Client") as mock_genai:
        mock_client = MagicMock()
        mock_genai.return_value = mock_client

        # Setup models mock structure
        mock_models = MagicMock()
        mock_client.models = mock_models

        # Setup response structure
        mock_response = MagicMock()
        mock_response.text = "This is a test response from Gemini"
        mock_models.generate_content.return_value = mock_response

        yield mock_client


@pytest.fixture
def gemini_model(mock_genai_client):
    return GeminiModel(api_key="test_gemini_key")


class TestGeminiModel:

    def test_initialization(self, mock_genai_client):
        """Test that the Gemini model initializes correctly."""
        model = GeminiModel(api_key="test_gemini_key")
        assert model.api_key == "test_gemini_key"
        assert model.provider_name == "Google Gemini"
        assert model.client == mock_genai_client

    def test_initialization_from_env(self, monkeypatch, mock_genai_client):
        """Test initialization using environment variable."""
        monkeypatch.setenv("GEMINI_API_KEY", "env_test_key")
        model = GeminiModel()
        assert model.api_key == "env_test_key"

    def test_run_gemini_query(self, gemini_model, mock_genai_client):
        """Test the synchronous Gemini query function."""
        prompt = "Test prompt for Gemini"
        model_name = "gemini-1.5-pro"

        result = gemini_model._run_gemini_query(prompt, model_name)

        # Check that the API was called with the right parameters
        gemini_model.client.models.generate_content.assert_called_once_with(
            contents=prompt, model=model_name
        )

        # Check the result is what we expect
        assert result == "This is a test response from Gemini"

    @pytest.mark.asyncio
    async def test_execute_query(self, gemini_model):
        """Test that _execute_query calls run_in_executor correctly."""
        prompt = "Test prompt for Gemini"
        model_name = "gemini-1.5-pro"

        # Mock the _run_gemini_query method
        gemini_model._run_gemini_query = MagicMock(
            return_value="This is a test response from Gemini"
        )

        # Call the method
        result = await gemini_model._execute_query(prompt, model_name)

        # Check the function was called with correct args
        gemini_model._run_gemini_query.assert_called_once_with(prompt, model_name)

        # Check the result is what we expect
        assert result == "This is a test response from Gemini"

    @pytest.mark.asyncio
    async def test_execute_query_default_model(self, gemini_model):
        """Test that _execute_query uses the default model when none is specified."""
        prompt = "Test prompt for Gemini"

        # Mock the _run_gemini_query method
        gemini_model._run_gemini_query = MagicMock(
            return_value="This is a test response from Gemini"
        )

        # Call the method without specifying a model
        result = await gemini_model._execute_query(prompt)

        # Check the function was called with the default model
        gemini_model._run_gemini_query.assert_called_once_with(
            prompt, GEMINI_DEFAULT_MODEL
        )

    @pytest.mark.asyncio
    async def test_execute_query_error_handling(self, gemini_model):
        """Test that _execute_query properly handles errors."""
        prompt = "Test prompt for Gemini"

        # Mock the _run_gemini_query method to raise an exception
        gemini_model._run_gemini_query = MagicMock(side_effect=Exception("API error"))

        # Check that the exception is propagated
        with pytest.raises(Exception) as e:
            await gemini_model._execute_query(prompt)

        assert str(e.value) == "API error"

    @pytest.mark.asyncio
    async def test_query_integration(self, gemini_model):
        """Test the full query method from the parent class using the Gemini implementation."""
        prompt = "Test prompt for Gemini"
        model_name = "gemini-1.5-pro"

        # Mock the _execute_query method
        gemini_model._execute_query = AsyncMock(
            return_value="This is a test response from Gemini"
        )

        result = await gemini_model.query(prompt, model_name)

        assert result["provider"] == "Google Gemini"
        assert result["model"] == model_name
        assert result["response"] == "This is a test response from Gemini"
        assert result["success"] is True
