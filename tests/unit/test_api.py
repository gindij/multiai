import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from multi_ai.api import app, comparator, blending_comparator


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_comparators():
    with patch.object(comparator, 'compare', new_callable=AsyncMock) as mock_compare, \
         patch.object(blending_comparator, 'compare', new_callable=AsyncMock) as mock_blend_compare:
        
        # Setup default return values
        mock_compare.return_value = {
            "result": "Selected model response",
            "best_response": {"provider": "OpenAI", "model": "gpt-4"},
            "method": "select",
            "success": True
        }
        
        mock_blend_compare.return_value = {
            "result": "Blended response",
            "weights": [0.7, 0.3],
            "responses": [{"provider": "OpenAI"}, {"provider": "Anthropic"}],
            "method": "blend",
            "success": True
        }
        
        yield {
            "standard": mock_compare,
            "blending": mock_blend_compare
        }


class TestAPIEndpoints:
    
    def test_home_page(self, client):
        """Test that the home page endpoint returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Multi-AI Comparison" in response.text
    
    def test_list_models(self, client):
        """Test that the models endpoint returns the available models."""
        response = client.get("/models")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert "openai" in data["models"]
        assert "anthropic" in data["models"]
        assert "gemini" in data["models"]
    
    def test_compare_models_standard(self, client, mock_comparators):
        """Test the compare endpoint with standard (non-blending) mode."""
        request_data = {
            "prompt": "Test prompt",
            "models": {
                "openai": "gpt-4-turbo",
                "anthropic": "claude-3-opus-latest"
            },
            "blend": False,
            "include_details": True
        }
        
        response = client.post("/compare", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Selected model response"
        assert data["success"] is True
        assert "details" in data
        assert data["details"]["method"] == "select"
        
        # Check comparator was called correctly
        mock_comparators["standard"].assert_called_once_with(
            "Test prompt", 
            {
                "openai": "gpt-4-turbo",
                "anthropic": "claude-3-opus-latest"
            }
        )
        mock_comparators["blending"].assert_not_called()
    
    def test_compare_models_blending(self, client, mock_comparators):
        """Test the compare endpoint with blending mode."""
        request_data = {
            "prompt": "Test prompt",
            "models": {
                "openai": "gpt-4-turbo",
                "anthropic": "claude-3-opus-latest",
                "gemini": "gemini-2.5-pro-preview-05-06"
            },
            "blend": True,
            "include_details": True
        }
        
        response = client.post("/compare", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Blended response"
        assert data["success"] is True
        assert "details" in data
        assert data["details"]["method"] == "blend"
        assert "weights" in data["details"]
        
        # Check blending comparator was called correctly
        mock_comparators["standard"].assert_not_called()
        mock_comparators["blending"].assert_called_once_with(
            "Test prompt", 
            {
                "openai": "gpt-4-turbo",
                "anthropic": "claude-3-opus-latest",
                "gemini": "gemini-2.5-pro-preview-05-06"
            }
        )
    
    def test_compare_models_without_details(self, client, mock_comparators):
        """Test the compare endpoint without including details."""
        request_data = {
            "prompt": "Test prompt",
            "blend": False,
            "include_details": False
        }
        
        response = client.post("/compare", json=request_data)
        
        # Check response
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == "Selected model response"
        assert data["success"] is True
        assert data.get("details") is None  # Check details is None instead of not present
    
    def test_compare_models_error(self, client, mock_comparators):
        """Test error handling in the compare endpoint."""
        mock_comparators["standard"].side_effect = Exception("Test error")
        
        request_data = {
            "prompt": "Test prompt",
            "blend": False
        }
        
        response = client.post("/compare", json=request_data)
        
        # Check error response
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["detail"] == "Test error"