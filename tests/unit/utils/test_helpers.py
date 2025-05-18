import os
import json
import pytest
import tempfile
from unittest.mock import patch, mock_open
from multi_ai.utils.helpers import (
    load_env_file,
    format_response,
    save_to_file,
    create_default_env_file
)


class TestLoadEnvFile:
    
    def test_file_not_exists(self):
        """Test load_env_file when the file doesn't exist."""
        with patch("os.path.exists", return_value=False):
            # Should return silently without error
            load_env_file("nonexistent.env")
    
    def test_load_valid_env_file(self, monkeypatch):
        """Test loading a valid env file."""
        env_content = """
        # This is a comment
        KEY1=value1
        KEY2=value2
        
        # Another comment
        KEY3=value with spaces
        """
        
        # Create a patch for open that returns our env content
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                load_env_file(".env")
                
                # Check that the environment variables were set
                assert os.environ.get("KEY1") == "value1"
                assert os.environ.get("KEY2") == "value2"
                assert os.environ.get("KEY3") == "value with spaces"
    
    def test_env_file_with_comments_and_empty_lines(self, monkeypatch):
        """Test loading an env file with comments and empty lines."""
        env_content = """
        # Comment line
        
        KEY1=value1
        # Another comment
        KEY2=value2
        """
        
        with patch("builtins.open", mock_open(read_data=env_content)):
            with patch("os.path.exists", return_value=True):
                load_env_file(".env")
                
                # Check that only the actual variables were set
                assert os.environ.get("KEY1") == "value1"
                assert os.environ.get("KEY2") == "value2"
                assert os.environ.get("# Comment line") is None


class TestFormatResponse:
    
    def test_simple_response(self):
        """Test formatting a simple response without details."""
        data = {
            "result": "Test result",
            "success": True,
            "best_response": {"provider": "OpenAI"},  # This should be filtered out
            "method": "select"  # This should be filtered out
        }
        
        formatted = format_response(data, include_details=False)
        
        assert formatted == {
            "result": "Test result",
            "success": True
        }
    
    def test_detailed_response(self):
        """Test formatting a detailed response with all details included."""
        data = {
            "result": "Test result",
            "success": True,
            "best_response": {"provider": "OpenAI"},
            "method": "select",
            "judge_response": "Judge explanation",
            "weights": [0.7, 0.3]
        }
        
        formatted = format_response(data, include_details=True)
        
        assert formatted == {
            "result": "Test result",
            "success": True,
            "details": {
                "best_response": {"provider": "OpenAI"},
                "method": "select",
                "judge_response": "Judge explanation",
                "weights": [0.7, 0.3]
            }
        }
    
    def test_missing_fields(self):
        """Test formatting a response with missing fields."""
        data = {}
        
        formatted = format_response(data, include_details=True)
        
        assert formatted == {
            "result": "",
            "success": False,
            "details": {}
        }


class TestSaveToFile:
    
    def test_save_to_file(self):
        """Test saving data to a file."""
        data = {"key": "value", "nested": {"inner": "data"}}
        
        # Use mock_open to mock the file write operation
        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            save_to_file("test.json", data)
        
        # Check that open was called with correct arguments
        mock_file.assert_called_once_with("test.json", "w")
        
        # Get the file handle that was returned from open
        handle = mock_file()
        
        # Don't check for exact number of write calls, just check content
        expected_json = json.dumps(data, indent=2)
        # Using a more flexible assertion that doesn't rely on number of calls
        write_calls = [call[0][0] for call in handle.write.call_args_list]
        write_data = ''.join(write_calls)
        assert expected_json == write_data


class TestCreateDefaultEnvFile:
    
    def test_create_default_env_file_file_exists(self):
        """Test that create_default_env_file does nothing when the file exists."""
        with patch("os.path.exists", return_value=True):
            with patch("builtins.open") as mock_open:
                create_default_env_file(".env")
                
                # Check that open was not called
                mock_open.assert_not_called()
    
    def test_create_default_env_file_new_file(self):
        """Test creating a default env file when it doesn't exist."""
        with patch("os.path.exists", return_value=False):
            mock_file = mock_open()
            with patch("builtins.open", mock_file):
                create_default_env_file(".env")
                
                # Check that open was called with correct arguments
                mock_file.assert_called_once_with(".env", "w")
                
                # Get the file handle
                handle = mock_file()
                
                # Check that write was called and the content includes expected lines
                assert handle.write.call_count == 1
                
                # Check that important keys are in the default content
                written_content = handle.write.call_args[0][0]
                assert "OPENAI_API_KEY=" in written_content
                assert "ANTHROPIC_API_KEY=" in written_content
                assert "GEMINI_API_KEY=" in written_content
                assert "JUDGE_MODEL_PROVIDER=openai" in written_content