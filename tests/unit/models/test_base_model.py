import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from multi_ai.models.base_model import BaseModel

# Test constants
TEST_API_KEY = "test-api-key-123"
TEST_ENV_VAR = "TEST_API_KEY"
TEST_PROMPT = "Test prompt for the model"
TEST_MODEL = "test-model-v1"


@pytest.fixture
def base_model():
    """
    Create a base model instance for testing.
    
    This fixture creates a BaseModel instance with necessary mocking:
    - Patches the initialize_client method to avoid real API initialization
    - Provides a concrete implementation of the abstract _execute_query method
    - Sets up a predictable success response for testing
    
    Returns:
        A configured BaseModel instance ready for testing
    """
    with patch.object(BaseModel, 'initialize_client'):
        model = BaseModel(api_key=TEST_API_KEY)
        # Since BaseModel._execute_query is abstract, provide a concrete implementation for testing
        model._execute_query = AsyncMock(return_value="Test response")
        return model


class TestBaseModel:
    
    def test_init_with_direct_api_key(self):
        """
        Test initialization with a directly provided API key.
        
        Verifies that when an API key is provided directly to the constructor,
        it is correctly stored in the model instance and the provider name is set.
        """
        with patch.object(BaseModel, 'initialize_client'):
            model = BaseModel(api_key=TEST_API_KEY)
            assert model.api_key == TEST_API_KEY, "API key should be stored directly"
            assert model.provider_name == "Base", "Default provider name should be 'Base'"
    
    def test_init_with_env_var(self, monkeypatch):
        """
        Test initialization with an environment variable.
        
        Verifies that when no API key is provided but an environment variable name is,
        the model correctly retrieves the API key from the environment.
        
        Args:
            monkeypatch: pytest fixture that allows modifying environment variables
        """
        # Set up the environment variable
        env_api_key = "env_test_key_value"
        monkeypatch.setenv(TEST_ENV_VAR, env_api_key)
        
        # Create model with only the environment variable name
        with patch.object(BaseModel, 'initialize_client'):
            model = BaseModel(env_var_name=TEST_ENV_VAR)
            
            # Verify the API key was retrieved from environment
            assert model.api_key == env_api_key, "API key should be retrieved from environment"
    
    @pytest.mark.asyncio
    async def test_query_success(self, base_model):
        """
        Test successful query execution.
        
        Verifies that the query method correctly:
        1. Calls the underlying _execute_query method with the right parameters
        2. Wraps the response in the expected success response format
        3. Includes all required metadata fields
        
        Args:
            base_model: The fixture providing a pre-configured BaseModel instance
        """
        # Call the query method with test parameters
        result = await base_model.query(TEST_PROMPT, TEST_MODEL)
        
        # Verify the result structure and content
        assert result["provider"] == "Base", "Provider name should be included"
        assert result["model"] == TEST_MODEL, "Model name should match the input"
        assert result["response"] == "Test response", "Response should match mock return value"
        assert result["success"] is True, "Success flag should be True for successful queries"
        
        # Verify the underlying _execute_query was called correctly
        base_model._execute_query.assert_called_once_with(TEST_PROMPT, TEST_MODEL)
    
    @pytest.mark.asyncio
    async def test_query_failure(self, base_model):
        """
        Test query execution with an exception.
        
        Verifies that when the underlying _execute_query method raises an exception:
        1. The exception is caught and handled gracefully
        2. The response is properly formatted as an error response
        3. The error message from the exception is included
        4. The success flag is set to False
        
        Args:
            base_model: The fixture providing a pre-configured BaseModel instance
        """
        # Configure the mock to raise an exception
        error_message = "API error: rate limit exceeded"
        base_model._execute_query = AsyncMock(side_effect=Exception(error_message))
        
        # Call the query method
        result = await base_model.query(TEST_PROMPT, TEST_MODEL)
        
        # Verify the error response structure and content
        assert result["provider"] == "Base", "Provider name should be included even in errors"
        assert result["model"] == TEST_MODEL, "Model name should match the input"
        assert result["error"] == error_message, "Error message should match the exception"
        assert result["success"] is False, "Success flag should be False for errors"
    
    @pytest.mark.asyncio
    async def test_execute_query_raises_not_implemented(self):
        """
        Test that _execute_query raises NotImplementedError if not overridden.
        
        This test verifies the abstract method pattern is enforced:
        - The base class's _execute_query method should raise NotImplementedError
        - The error message should be clear about what needs to be implemented
        
        This ensures subclasses are forced to implement the method.
        """
        # Create a model with the base implementation (no mock override)
        with patch.object(BaseModel, 'initialize_client'):
            # Explicitly provide an API key to avoid the env_var_name=None issue
            model = BaseModel(api_key=TEST_API_KEY, env_var_name=TEST_ENV_VAR)
            
            # Since this is a coroutine function, we need to await it
            # and check that it raises the right exception
            with pytest.raises(NotImplementedError) as excinfo:
                await model._execute_query(TEST_PROMPT, TEST_MODEL)
                
            # Verify the error message is informative
            assert str(excinfo.value) == "Subclasses must implement _execute_query"