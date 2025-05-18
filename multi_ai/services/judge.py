import os
import re
import json
import random
from typing import List, Dict, Any, Optional, Tuple
from ..models.openai_model import OpenAIModel
from ..config import JUDGE_DEFAULT_PROVIDER, JUDGE_DEFAULT_MODEL


class Judge:
    """A service for evaluating and ranking responses from multiple AI models."""

    def __init__(
        self,
        model_provider: Optional[str] = None,
        model_name: Optional[str] = None,
        blend_responses: bool = False,
    ) -> None:
        """
        Initialize the judge with the specified model provider and model name.

        Args:
            model_provider: The provider to use for judging
            model_name: The model name to use for judging
            blend_responses: Whether to blend responses using weights or select a single best response
        """
        self.model_provider = model_provider or os.environ.get(
            "JUDGE_MODEL_PROVIDER", JUDGE_DEFAULT_PROVIDER
        )
        self.model_name = model_name or os.environ.get(
            "JUDGE_MODEL", JUDGE_DEFAULT_MODEL
        )
        self.blend_responses = blend_responses

        # Currently only supporting OpenAI as judge
        if self.model_provider == "openai":
            self.model = OpenAIModel()
        else:
            raise ValueError(f"Unsupported judge model provider: {self.model_provider}")

    async def evaluate(
        self, prompt: str, responses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate responses from different models and select the best one or blend them.
        """
        # Filter out any failed responses
        successful_responses = [r for r in responses if r.get("success", False)]

        if not successful_responses:
            return {
                "result": None,
                "method": "none",
                "reason": "All model responses failed",
                "explanation": "No successful responses were received from any model.",
                "success": False,
            }

        if len(successful_responses) == 1:
            return {
                "result": successful_responses[0]["response"],
                "best_response": successful_responses[0],
                "method": "single",
                "reason": "Only one successful response available",
                "explanation": "Only one successful response was available, so it was selected automatically.",
                "success": True,
            }

        # Anonymize the responses to prevent model bias
        anonymized_responses, provider_map = self._anonymize_responses(
            successful_responses
        )

        # Create the evaluation prompt
        eval_prompt = self._create_evaluation_prompt(
            prompt, anonymized_responses, self.blend_responses
        )

        # Get the judge's decision
        judge_response = await self.model.query(eval_prompt, model=self.model_name)

        if not judge_response.get("success", False):
            # If judge fails, return the first successful response
            return {
                "result": successful_responses[0]["response"],
                "best_response": successful_responses[0],
                "method": "fallback",
                "reason": f"Judge failed: {judge_response.get('error', 'Unknown error')}",
                "explanation": "The judge model encountered an error. Defaulting to the first available response.",
                "success": True,
            }

        # Process the judge's response
        if self.blend_responses:
            # Parse weights from judge's response
            weights, explanation = self._parse_weights(
                judge_response["response"], len(successful_responses)
            )

            if not weights or sum(weights) == 0:
                # Fallback to first response if weights parsing fails
                return {
                    "result": successful_responses[0]["response"],
                    "best_response": successful_responses[0],
                    "method": "fallback",
                    "reason": "Could not parse valid weights",
                    "explanation": "Fallback to first available model due to weight parsing failure.",
                    "success": True,
                }

            # Normalize weights to sum to 1
            total = sum(weights)
            normalized_weights = [w / total for w in weights]

            # De-anonymize and get original responses and weights
            original_responses = []
            original_weights = []

            for anon_idx, (idx, provider, model) in provider_map.items():
                original_responses.append(successful_responses[idx])
                original_weights.append(normalized_weights[anon_idx])

            # Generate blended response
            blended_result = await self._blend_text_responses(
                prompt,
                original_responses,
                original_weights,
            )

            return {
                "result": blended_result,
                "weights": original_weights,
                "responses": original_responses,
                "method": "blend",
                "explanation": explanation,
                "judge_response": judge_response["response"],
                "success": True,
            }
        else:
            # Parse selected response index and explanation
            best_idx, explanation = self._parse_selected_index(
                judge_response["response"]
            )

            # Default to first response if parsing fails
            if best_idx is None or best_idx >= len(anonymized_responses):
                selected = successful_responses[0]
                method = "fallback"
                reason = "Could not parse valid selection"
                explanation = "Fallback to first available model due to selection parsing failure."
            else:
                # Map the anonymized index back to the original index
                original_idx = provider_map[best_idx][0]
                selected = successful_responses[original_idx]
                method = "select"
                reason = f"Selected response {best_idx+1}"

            return {
                "result": selected["response"],
                "best_response": selected,
                "method": method,
                "reason": reason,
                "explanation": explanation,
                "judge_response": judge_response["response"],
                "success": True,
            }

    def _anonymize_responses(
        self, responses: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[int, Tuple[int, str, str]]]:
        """
        Anonymize responses by removing provider information and shuffling order.
        Returns anonymized responses and a mapping from anonymized index to original index.
        """
        # Create a list of indices and shuffle
        indices = list(range(len(responses)))
        random.shuffle(indices)

        # Create anonymized responses
        anonymized = []
        # Map from anonymized index to (original_index, provider, model)
        provider_map = {}

        for anon_idx, orig_idx in enumerate(indices):
            resp = responses[orig_idx]
            anonymized.append(
                {
                    "provider": f"Provider {anon_idx+1}",  # Hide actual provider
                    "model": f"Model {anon_idx+1}",  # Hide actual model name
                    "response": resp["response"],
                    "success": resp["success"],
                }
            )
            provider_map[anon_idx] = (orig_idx, resp["provider"], resp["model"])

        return anonymized, provider_map

    def _create_evaluation_prompt(
        self,
        original_prompt: str,
        responses: List[Dict[str, Any]],
        blend_mode: bool = False,
    ) -> str:
        """Create a prompt for the judge model to evaluate responses."""
        prompt_parts = [
            "You are a fair and impartial judge evaluating responses from different AI models.",
            "You must evaluate each response solely on its quality and merit, not based on which model produced it.",
            f"Original prompt: {original_prompt}\n",
            "Model responses:",
        ]

        for i, response in enumerate(responses, 1):
            provider = response["provider"]
            model = response["model"]
            model_response = response["response"]

            prompt_parts.append(
                f"\n--- Response {i}: {provider} ({model}) ---\n{model_response}\n"
            )

        prompt_parts.append("\nEvaluate each response based on these criteria:")

        criteria = [
            "1. Accuracy: Is the information correct and reliable?",
            "2. Completeness: Does it fully address all aspects of the prompt?",
            "3. Clarity: Is it well-written, easy to understand, and well-structured?",
            "4. Usefulness: How practical and helpful is the response?",
            "5. Creativity: Where appropriate, does it show original thinking?",
            "6. Reasoning: Does it demonstrate logical thinking and good judgment?",
        ]
        prompt_parts.extend(criteria)

        prompt_parts.append(
            "\nIMPORTANT: All responses come from equally capable models. Judge each response strictly on its quality as presented here."
        )

        if blend_mode:
            prompt_parts.append("\nYOUR RESPONSE FORMAT:")
            prompt_parts.append(
                "1. Provide a brief explanation (1-2 sentences) of how you evaluated these responses."
            )
            prompt_parts.append(
                "2. Assign a weight between 0 and 10 to each response based on overall quality."
            )
            prompt_parts.append(
                'Format your response like this:\n{"explanation": "Your explanation here", "weights": [X, Y, Z]}'
            )
            prompt_parts.append(
                "Where X, Y, Z are numbers between 0 and 10 representing the quality of each response."
            )
        else:
            prompt_parts.append("\nYOUR RESPONSE FORMAT:")
            prompt_parts.append(
                "1. Provide a brief explanation (1-2 sentences) of why you selected the best response."
            )
            prompt_parts.append("2. Identify the number of the best response.")
            prompt_parts.append(
                'Format your response like this:\n{"explanation": "Your explanation here", "selection": N}'
            )
            prompt_parts.append(
                "Where N is the number of the best response (e.g., 1, 2, or 3)."
            )

        return "\n".join(prompt_parts)

    def _parse_selected_index(self, judge_text: str) -> Tuple[Optional[int], str]:
        """
        Parse the judge's response to determine the best model response index and explanation.
        Returns a tuple of (selected_index, explanation).
        """
        # Default explanation if parsing fails
        default_explanation = "Selected based on overall quality assessment."
        explanation = default_explanation

        try:
            # Try to extract JSON from the response
            match = re.search(r"\{.*\}", judge_text)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)

                # Extract the explanation if available
                if "explanation" in data and isinstance(data["explanation"], str):
                    explanation = data["explanation"]

                # Extract the selection
                if "selection" in data and isinstance(data["selection"], (int, str)):
                    # Convert to 0-indexed
                    return int(data["selection"]) - 1, explanation
        except:
            pass

        # Fallback to previous parsing method
        # Clean the response text and try to extract a number
        cleaned_text = judge_text.strip().replace("'", "").replace('"', "")

        try:
            # Try to convert the entire response to an integer
            response_idx = int(cleaned_text) - 1  # Convert to 0-indexed
            return response_idx, explanation
        except ValueError:
            # If that fails, search for digits in the text
            match = re.search(r"\b(\d+)\b", cleaned_text)
            if match:
                return int(match.group(1)) - 1, explanation  # Convert to 0-indexed

        return None, explanation

    def _parse_weights(
        self, judge_text: str, num_responses: int
    ) -> Tuple[List[float], str]:
        """
        Parse the weights and explanation from the judge's response.
        Returns a tuple of (weights, explanation).
        """
        # Default values
        default_weights = [1.0 / num_responses] * num_responses
        default_explanation = (
            "Weights assigned based on quality assessment across multiple criteria."
        )
        explanation = default_explanation

        try:
            # Try to extract JSON from the response
            match = re.search(r"\{.*\}", judge_text)
            if match:
                json_str = match.group(0)
                data = json.loads(json_str)

                # Extract the explanation if available
                if "explanation" in data and isinstance(data["explanation"], str):
                    explanation = data["explanation"]

                # Extract weights
                if "weights" in data and isinstance(data["weights"], list):
                    weights = data["weights"]

                    # Validate weights
                    if len(weights) == num_responses and all(
                        isinstance(w, (int, float)) for w in weights
                    ):
                        return weights, explanation
        except:
            pass

        # If we can't parse JSON, try to extract a list of numbers
        try:
            numbers = re.findall(r"[\d.]+", judge_text)
            if len(numbers) == num_responses:
                return [float(n) for n in numbers], explanation
        except:
            pass

        # If all else fails, create equal weights
        return default_weights, explanation

    async def _blend_text_responses(
        self,
        original_prompt: str,
        responses: List[Dict[str, Any]],
        weights: List[float],
    ) -> str:
        """Blend text responses by asking the judge model to create a unified response."""
        # Create a blending prompt
        blend_prompt = self._create_blending_prompt(original_prompt, responses, weights)

        # Ask the judge model to blend the responses
        blend_response = await self.model.query(blend_prompt, model=self.model_name)

        if not blend_response.get("success", False):
            # If blending fails, return the highest weighted response
            max_idx = weights.index(max(weights))
            return responses[max_idx]["response"]

        # Return the blended response
        return blend_response["response"]

    def _create_blending_prompt(
        self,
        original_prompt: str,
        responses: List[Dict[str, Any]],
        weights: List[float],
    ) -> str:
        """Create a prompt for blending multiple responses according to weights."""
        # Format weights as percentages
        weight_percentages = [f"{w*100:.1f}%" for w in weights]

        prompt_parts = [
            "You are an expert at synthesizing information from multiple sources.",
            f"Original prompt: {original_prompt}\n",
            "You will be given multiple responses to this prompt with assigned weights.",
            "Your task is to create a SINGLE COHERENT RESPONSE that:",
            "1. Incorporates content from all responses according to their weights",
            "2. Prioritizes information from higher-weighted responses",
            "3. Resolves any contradictions by favoring higher-weighted responses",
            "4. Maintains a consistent tone and style throughout",
            "5. Forms a complete, well-structured answer to the original prompt\n",
            "Responses with their weights:",
        ]

        for i, (response, weight_pct) in enumerate(
            zip([r["response"] for r in responses], weight_percentages), 1
        ):
            provider = responses[i - 1]["provider"]
            model = responses[i - 1]["model"]
            prompt_parts.append(
                f"\n--- Response {i} ({provider}, {model}, Weight: {weight_pct}) ---\n{response}\n"
            )

        prompt_parts.append(
            "\nNow, create a single coherent response that blends these sources according to their weights."
            "\nDo not mention the weights or that this is a blend in your response."
            "\nWrite in a natural, flowing style as if this was a single response from the beginning."
        )

        return "\n".join(prompt_parts)
