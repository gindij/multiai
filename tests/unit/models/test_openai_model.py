import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from multi_ai.models.openai_model import OpenAIModel
from multi_ai.config import OPENAI_DEFAULT_MODEL


@pytest.fixture
def mock_openai_client():
    with patch("openai.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Setup chat completions mock structure
        mock_completion = MagicMock()
        mock_client.chat.completions.create.return_value = mock_completion

        # Setup response structure
        mock_message = MagicMock()
        mock_message.content = "This is a test response from OpenAI"
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]

        yield mock_client


@pytest.fixture
def openai_model(mock_openai_client):
    return OpenAIModel(api_key="test_openai_key")


class TestOpenAIModel:

    def test_initialization(self, mock_openai_client):
        """Test that the OpenAI model initializes correctly."""
        model = OpenAIModel(api_key="test_openai_key")
        assert model.api_key == "test_openai_key"
        assert model.provider_name == "OpenAI"
        assert model.client == mock_openai_client

    def test_initialization_from_env(self, monkeypatch, mock_openai_client):
        """Test initialization using environment variable."""
        monkeypatch.setenv("OPENAI_API_KEY", "env_test_key")
        model = OpenAIModel()
        assert model.api_key == "env_test_key"

    @pytest.mark.asyncio
    async def test_execute_query(self, openai_model, mock_openai_client):
        """Test that _execute_query calls the OpenAI API correctly."""
        prompt = "Test prompt for OpenAI"
        model_name = "gpt-4-turbo"

        result = await openai_model._execute_query(prompt, model_name)

        # Check that the API was called with the right parameters
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=openai_model.timeout,
        )

        # Check the result is what we expect
        assert result == "This is a test response from OpenAI"

    @pytest.mark.asyncio
    async def test_execute_query_default_model(self, openai_model, mock_openai_client):
        """Test that _execute_query uses the default model when none is specified."""
        prompt = "Test prompt for OpenAI"

        result = await openai_model._execute_query(prompt)

        # Check that the API was called with the default model
        mock_openai_client.chat.completions.create.assert_called_once_with(
            model=OPENAI_DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=openai_model.timeout,
        )

    @pytest.mark.asyncio
    async def test_query_integration(self, openai_model, mock_openai_client):
        """Test the full query method from the parent class using the OpenAI implementation."""
        prompt = "Test prompt for OpenAI"
        model_name = "gpt-4-turbo"

        result = await openai_model.query(prompt, model_name)

        assert result["provider"] == "OpenAI"
        assert result["model"] == model_name
        assert result["response"] == "This is a test response from OpenAI"
        assert result["success"] is True
