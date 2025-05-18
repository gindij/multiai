import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock, ANY
import os
from multi_ai.services.judge import Judge
from multi_ai.config import JUDGE_DEFAULT_PROVIDER, JUDGE_DEFAULT_MODEL


@pytest.fixture
def mock_openai_model():
    with patch("multi_ai.services.judge.OpenAIModel") as mock_model:
        mock_instance = AsyncMock()
        mock_model.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def judge(mock_openai_model):
    return Judge(model_provider="openai", model_name="gpt-4-turbo")


@pytest.fixture
def sample_responses():
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


class TestJudge:

    def test_initialization_custom(self, mock_openai_model):
        """Test initialization with custom values."""
        judge = Judge(
            model_provider="openai", model_name="gpt-4-turbo", blend_responses=True
        )

        assert judge.model_provider == "openai"
        assert judge.model_name == "gpt-4-turbo"
        assert judge.blend_responses is True

    def test_initialization_env_vars(self, monkeypatch):
        """Test initialization from environment variables."""
        monkeypatch.setenv("JUDGE_MODEL_PROVIDER", "openai")
        monkeypatch.setenv("JUDGE_MODEL", "custom-model")

        with patch("multi_ai.services.judge.OpenAIModel") as mock_model:
            mock_instance = MagicMock()
            mock_model.return_value = mock_instance

            judge = Judge()

            assert judge.model_provider == "openai"
            assert judge.model_name == "custom-model"

    def test_initialization_unsupported_provider(self):
        """Test initialization with unsupported provider."""
        with pytest.raises(ValueError) as e:
            Judge(model_provider="unsupported")

        assert "Unsupported judge model provider: unsupported" in str(e.value)

    def test_anonymize_responses(self, judge, sample_responses):
        """Test response anonymization."""
        with patch("random.shuffle") as mock_shuffle:
            # Make shuffle predictable for testing
            mock_shuffle.side_effect = lambda x: x.sort(reverse=True)

            anonymized, provider_map = judge._anonymize_responses(sample_responses)

            # Check anonymized responses
            assert len(anonymized) == 3
            assert anonymized[0]["provider"] == "Provider 1"
            assert anonymized[0]["model"] == "Model 1"

            # Check provider map is correct
            assert provider_map[0][1] == "Google Gemini"
            assert provider_map[1][1] == "Anthropic"
            assert provider_map[2][1] == "OpenAI"

    def test_create_evaluation_prompt_select_mode(self, judge, sample_responses):
        """Test creating evaluation prompt in selection mode."""
        prompt = judge._create_evaluation_prompt(
            "Test prompt", sample_responses, blend_mode=False
        )

        # Check key elements in prompt
        assert "Original prompt: Test prompt" in prompt
        assert "Model responses:" in prompt
        assert "Response 1: OpenAI (gpt-4)" in prompt
        assert "Response 2: Anthropic (claude-3-opus)" in prompt
        assert "Response 3: Google Gemini (gemini-pro)" in prompt
        assert "Provide a brief explanation" in prompt
        assert "Identify the number of the best response" in prompt
        assert '{"explanation": "Your explanation here", "selection": N}' in prompt

    def test_create_evaluation_prompt_blend_mode(self, judge, sample_responses):
        """Test creating evaluation prompt in blending mode."""
        prompt = judge._create_evaluation_prompt(
            "Test prompt", sample_responses, blend_mode=True
        )

        # Check key elements in prompt
        assert "Original prompt: Test prompt" in prompt
        assert "Model responses:" in prompt
        assert "Response 1: OpenAI (gpt-4)" in prompt
        assert "Response 2: Anthropic (claude-3-opus)" in prompt
        assert "Response 3: Google Gemini (gemini-pro)" in prompt
        assert "Provide a brief explanation" in prompt
        assert "Assign a weight between 0 and 10" in prompt
        assert (
            '{"explanation": "Your explanation here", "weights": [X, Y, Z]}' in prompt
        )

    def test_parse_selected_index(self, judge):
        """Test parsing the selected index from judge responses."""
        # Test direct number
        index, explanation = judge._parse_selected_index("2")
        assert index == 1  # Zero-indexed
        assert (
            explanation == "Selected based on overall quality assessment."
        )  # Default explanation

        # Test with surrounding text
        index, explanation = judge._parse_selected_index("The best response is 3.")
        assert index == 2  # Zero-indexed
        assert explanation == "Selected based on overall quality assessment."

        # Test with quotes
        index, explanation = judge._parse_selected_index("'1'")
        assert index == 0  # Zero-indexed
        assert explanation == "Selected based on overall quality assessment."

        # Test with JSON format containing explanation
        index, explanation = judge._parse_selected_index(
            '{"selection": 2, "explanation": "Response 2 is more detailed and accurate"}'
        )
        assert index == 1  # Zero-indexed
        assert explanation == "Response 2 is more detailed and accurate"

        # Test invalid input
        index, explanation = judge._parse_selected_index("None of them are good")
        assert index is None
        assert (
            explanation == "Selected based on overall quality assessment."
        )  # Default explanation

    def test_parse_weights(self, judge):
        """Test parsing weights from judge responses."""
        # Test valid JSON without explanation
        valid_json = '{"weights": [8, 5, 2]}'
        weights, explanation = judge._parse_weights(valid_json, 3)
        assert weights == [8, 5, 2]
        assert (
            explanation
            == "Weights assigned based on quality assessment across multiple criteria."
        )  # Default explanation

        # Test JSON with explanation
        json_with_explanation = '{"weights": [8, 5, 2], "explanation": "OpenAI response was more accurate and comprehensive"}'
        weights, explanation = judge._parse_weights(json_with_explanation, 3)
        assert weights == [8, 5, 2]
        assert explanation == "OpenAI response was more accurate and comprehensive"

        # Test JSON with surrounding text
        text_with_json = 'Here are my weights: {"weights": [9, 4, 7]}'
        weights, explanation = judge._parse_weights(text_with_json, 3)
        assert weights == [9, 4, 7]
        assert (
            explanation
            == "Weights assigned based on quality assessment across multiple criteria."
        )

        # Test plain numbers
        plain_numbers = "7 6 3"
        weights, explanation = judge._parse_weights(plain_numbers, 3)
        assert weights == [7.0, 6.0, 3.0]
        assert (
            explanation
            == "Weights assigned based on quality assessment across multiple criteria."
        )

        # Test invalid input - fallback to equal weights
        invalid_input = "I can't decide"
        expected_equal_weights = [1 / 3, 1 / 3, 1 / 3]
        weights, explanation = judge._parse_weights(invalid_input, 3)
        assert len(weights) == 3
        assert all(
            abs(w - expected_equal_weights[i]) < 0.01 for i, w in enumerate(weights)
        )
        assert (
            explanation
            == "Weights assigned based on quality assessment across multiple criteria."
        )

    @pytest.mark.asyncio
    async def test_evaluate_single_response(self, judge, mock_openai_model):
        """Test evaluation with a single response."""
        responses = [
            {
                "provider": "OpenAI",
                "model": "gpt-4",
                "response": "Single response",
                "success": True,
            }
        ]

        result = await judge.evaluate("Test prompt", responses)

        # Model should not be called for single response
        mock_openai_model.query.assert_not_called()

        # Check result
        assert result["result"] == "Single response"
        assert result["method"] == "single"
        assert result["success"] is True
        assert "explanation" in result
        assert (
            result["explanation"]
            == "Only one successful response was available, so it was selected automatically."
        )

    @pytest.mark.asyncio
    async def test_evaluate_selection_mode(
        self, judge, sample_responses, mock_openai_model
    ):
        """
        Test evaluation in selection mode.

        This test verifies that the Judge can properly:
        1. Anonymize responses to prevent bias
        2. Send them to a judge model for evaluation
        3. Parse the response to select the best response
        4. Return the selected response with appropriate metadata

        Since the anonymization process includes randomization, this test mocks
        the anonymization process to make it deterministic for testing.
        """

        # Mock _anonymize_responses to get predictable results
        original_anonymize = judge._anonymize_responses

        # Create a fake anonymization that preserves order
        def fake_anonymize(responses):
            anonymized = []
            provider_map = {}

            for i, resp in enumerate(responses):
                anonymized.append(
                    {
                        "provider": f"Provider {i+1}",
                        "model": f"Model {i+1}",
                        "response": resp["response"],
                        "success": resp["success"],
                    }
                )
                provider_map[i] = (i, resp["provider"], resp["model"])

            return anonymized, provider_map

        # Patch the method and execute within the context
        with patch.object(judge, "_anonymize_responses", side_effect=fake_anonymize):
            # Setup judge to always select the OpenAI response (index 0) with explanation
            mock_openai_model.query.return_value = {
                "provider": "OpenAI",
                "model": "gpt-4-turbo",
                "response": '{"selection": 1, "explanation": "Response 1 is more accurate and detailed"}',  # Select first response with explanation
                "success": True,
            }

            # Execute the evaluate method within the patch context
            result = await judge.evaluate("Test prompt", sample_responses)

        # Check judge was called
        mock_openai_model.query.assert_called_once()
        assert (
            mock_openai_model.query.call_args[0][0] is not None
        )  # Should have a prompt
        assert mock_openai_model.query.call_args[1]["model"] == "gpt-4-turbo"

        # Check result
        assert result["result"] == "Response from OpenAI model"
        assert result["best_response"]["provider"] == "OpenAI"
        assert result["method"] == "select"
        assert result["success"] is True
        assert "explanation" in result
        assert result["explanation"] == "Response 1 is more accurate and detailed"

    @pytest.mark.asyncio
    async def test_evaluate_selection_judge_failed(
        self, judge, sample_responses, mock_openai_model
    ):
        """Test evaluation when judge fails."""
        # Setup judge to fail
        mock_openai_model.query.return_value = {
            "provider": "OpenAI",
            "model": "gpt-4-turbo",
            "error": "Judge API error",
            "success": False,
        }

        result = await judge.evaluate("Test prompt", sample_responses)

        # Should fallback to first response
        assert result["result"] == "Response from OpenAI model"
        assert result["best_response"]["provider"] == "OpenAI"
        assert result["method"] == "fallback"
        assert result["success"] is True
        assert "explanation" in result
        assert (
            result["explanation"]
            == "The judge model encountered an error. Defaulting to the first available response."
        )

    @pytest.mark.asyncio
    async def test_evaluate_blend_mode(
        self, judge, sample_responses, mock_openai_model
    ):
        """Test evaluation in blend mode."""
        # Switch to blend mode
        judge.blend_responses = True

        # Setup judge response with weights and explanation
        mock_openai_model.query.return_value = {
            "provider": "OpenAI",
            "model": "gpt-4-turbo",
            "response": '{"weights": [7, 5, 3], "explanation": "OpenAI provided the most accurate information, Anthropic had good structure, and Gemini had unique insights"}',
            "success": True,
        }

        # Setup blend response
        mock_openai_model.query.side_effect = [
            # First call for weights
            {
                "provider": "OpenAI",
                "model": "gpt-4-turbo",
                "response": '{"weights": [7, 5, 3], "explanation": "OpenAI provided the most accurate information, Anthropic had good structure, and Gemini had unique insights"}',
                "success": True,
            },
            # Second call for blending
            {
                "provider": "OpenAI",
                "model": "gpt-4-turbo",
                "response": "Blended response combining all three models",
                "success": True,
            },
        ]

        result = await judge.evaluate("Test prompt", sample_responses)

        # Check judge was called twice
        assert mock_openai_model.query.call_count == 2

        # Check result
        assert result["result"] == "Blended response combining all three models"
        assert "weights" in result
        assert len(result["weights"]) == 3
        assert result["method"] == "blend"
        assert result["success"] is True
        assert "explanation" in result
        assert (
            result["explanation"]
            == "OpenAI provided the most accurate information, Anthropic had good structure, and Gemini had unique insights"
        )
