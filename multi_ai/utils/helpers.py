import os
import json
from typing import Dict, Any

def load_env_file(filepath: str = ".env") -> None:
    """Load environment variables from a .env file if it exists."""
    if not os.path.exists(filepath):
        return
        
    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
                
            key, value = line.split("=", 1)
            os.environ[key] = value

def format_response(data: Dict[str, Any], include_details: bool = False) -> Dict[str, Any]:
    """Format the response data for API output."""
    if not include_details:
        # Simple response with just the result
        return {
            "result": data.get("result", ""),
            "success": data.get("success", False),
        }
    
    # Detailed response with evaluation information
    return {
        "result": data.get("result", ""),
        "success": data.get("success", False),
        "details": {
            k: v for k, v in data.items() 
            if k not in ["result", "success"]
        }
    }

def save_to_file(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
        
def create_default_env_file(output_path: str = ".env") -> None:
    """Create a default .env file if it doesn't exist."""
    if os.path.exists(output_path):
        return
        
    # Create a minimal .env file
    default_content = """# OpenAI API Key
OPENAI_API_KEY=

# Anthropic API Key
ANTHROPIC_API_KEY=

# Google AI (Gemini) API Key
GEMINI_API_KEY=

# Judge model settings
JUDGE_MODEL_PROVIDER=openai
JUDGE_MODEL=gpt-4o-2024-11-20

# Server settings
HOST=0.0.0.0
PORT=8000
"""
    with open(output_path, "w") as f:
        f.write(default_content)