import anthropic
from typing import Optional
from .base_model import BaseModel
from ..config import ANTHROPIC_DEFAULT_MODEL

class AnthropicModel(BaseModel):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key, "ANTHROPIC_API_KEY")
        self.provider_name = "Anthropic"
        
    def initialize_client(self) -> None:
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
    async def _execute_query(self, prompt: str, model: str = ANTHROPIC_DEFAULT_MODEL) -> str:
        response = self.client.messages.create(
            model=model,
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.content[0].text