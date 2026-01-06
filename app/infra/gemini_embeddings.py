from concurrent.futures import ThreadPoolExecutor
from typing import List
from google import genai
from google.genai import types

from app.domain.embeddings import EmbeddingProvider
import asyncio

class GeminiEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        self.executor = ThreadPoolExecutor()

    async def embed(self, text: str) -> List[float]:
        """Genera embedding de un texto y devuelve lista de floats"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=[text],
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
        )
        return result.embeddings[0].values

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings de varios textos a la vez"""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            self.executor,
            lambda: self.client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=768)
            )
        )
        return [e.values for e in result.embeddings]
