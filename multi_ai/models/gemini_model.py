from google import genai
from typing import Optional
import asyncio
from .base_model import BaseModel
from ..config import GEMINI_DEFAULT_MODEL


class GeminiModel(BaseModel):
    def __init__(self, api_key: Optional[str] = None) -> None:
        super().__init__(api_key, "GEMINI_API_KEY")
        self.provider_name = "Google Gemini"
        self.initialize_client()

    def initialize_client(self) -> None:
        self.client = genai.client.Client(api_key=self.api_key)

    async def _execute_query(
        self, prompt: str, model: str = GEMINI_DEFAULT_MODEL
    ) -> str:
        try:
            # Run in thread pool to prevent blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None, self._run_gemini_query, prompt, model
            )
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            raise

    def _run_gemini_query(self, prompt: str, model: str) -> str:
        response = self.client.models.generate_content(contents=prompt, model=model)
        return response.text
