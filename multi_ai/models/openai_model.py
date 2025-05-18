import openai
from typing import Optional
from .base_model import BaseModel
from ..config import OPENAI_DEFAULT_MODEL


class OpenAIModel(BaseModel):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key, "OPENAI_API_KEY")
        self.provider_name = "OpenAI"

    def initialize_client(self) -> None:
        self.client = openai.OpenAI(api_key=self.api_key)

    async def _execute_query(
        self, prompt: str, model: str = OPENAI_DEFAULT_MODEL
    ) -> str:
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            timeout=self.timeout,
        )
        return response.choices[0].message.content
