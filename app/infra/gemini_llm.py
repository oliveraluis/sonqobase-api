import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from google import genai
from google.genai import types
from app.domain.llm import LLMProvider

class GeminiLLMProvider(LLMProvider):
    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.executor = ThreadPoolExecutor()

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        loop = asyncio.get_event_loop()

        def _call():
            if system_prompt:
                config = types.GenerateContentConfig(system_instruction=system_prompt)
                response = self.client.models.generate_content(
                    model=self.model,
                    config=config,
                    contents=prompt
                )
            else:
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt
                )
            return response.text

        return await loop.run_in_executor(self.executor, _call)
