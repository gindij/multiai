import os
from typing import Dict, Any, Optional
from ..config import DEFAULT_TIMEOUT

class BaseModel:
    def __init__(self, api_key: Optional[str] = None, env_var_name: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get(env_var_name)
        self.provider_name = "Base"
        self.timeout = DEFAULT_TIMEOUT
        self.initialize_client()
        
    def initialize_client(self) -> None:
        """Initialize the API client - to be implemented by subclasses"""
        pass
        
    async def query(self, prompt: str, model: str) -> Dict[str, Any]:
        """Query the model with the given prompt"""
        try:
            response_text = await self._execute_query(prompt, model)
            return {
                "provider": self.provider_name,
                "model": model,
                "response": response_text,
                "success": True,
            }
        except Exception as e:
            return {
                "provider": self.provider_name,
                "model": model,
                "error": str(e),
                "success": False,
            }
            
    async def _execute_query(self, prompt: str, model: str) -> str:
        """Execute the actual API call - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement _execute_query")