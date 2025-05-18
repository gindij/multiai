import pytest
from unittest.mock import patch, MagicMock
from multi_ai.models.anthropic_model import AnthropicModel
from multi_ai.config import ANTHROPIC_DEFAULT_MODEL


@pytest.fixture
def mock_anthropic_client():
    with patch("anthropic.Anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        # Setup messages mock structure
        mock_messages = MagicMock()
        mock_client.messages.create.return_value = mock_messages

        # Setup response structure
        mock_content = MagicMock()
        mock_content.text = "This is a test response from Anthropic"
        mock_messages.content = [mock_content]

        yield mock_client


@pytest.fixture
def anthropic_model(mock_anthropic_client):
    return AnthropicModel(api_key="test_anthropic_key")


class TestAnthropicModel:

    def test_initialization(self, mock_anthropic_client):
        """Test that the Anthropic model initializes correctly."""
        model = AnthropicModel(api_key="test_anthropic_key")
        assert model.api_key == "test_anthropic_key"
        assert model.provider_name == "Anthropic"
        assert model.client == mock_anthropic_client

    def test_initialization_from_env(self, monkeypatch, mock_anthropic_client):
        """Test initialization using environment variable."""
        monkeypatch.setenv("ANTHROPIC_API_KEY", "env_test_key")
        model = AnthropicModel()
        assert model.api_key == "env_test_key"

    @pytest.mark.asyncio
    async def test_execute_query(self, anthropic_model, mock_anthropic_client):
        """Test that _execute_query calls the Anthropic API correctly."""
        prompt = "Test prompt for Anthropic"
        model_name = "claude-3-opus-latest"

        result = await anthropic_model._execute_query(prompt, model_name)

        # Check that the API was called with the right parameters
        mock_anthropic_client.messages.create.assert_called_once_with(
            model=model_name,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        # Check the result is what we expect
        assert result == "This is a test response from Anthropic"

    @pytest.mark.asyncio
    async def test_execute_query_default_model(
        self, anthropic_model, mock_anthropic_client
    ):
        """Test that _execute_query uses the default model when none is specified."""
        prompt = "Test prompt for Anthropic"

        result = await anthropic_model._execute_query(prompt)

        # Check that the API was called with the default model
        mock_anthropic_client.messages.create.assert_called_once_with(
            model=ANTHROPIC_DEFAULT_MODEL,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

    @pytest.mark.asyncio
    async def test_query_integration(self, anthropic_model, mock_anthropic_client):
        """Test the full query method from the parent class using the Anthropic implementation."""
        prompt = "Test prompt for Anthropic"
        model_name = "claude-3-sonnet-latest"

        result = await anthropic_model.query(prompt, model_name)

        assert result["provider"] == "Anthropic"
        assert result["model"] == model_name
        assert result["response"] == "This is a test response from Anthropic"
        assert result["success"] is True
