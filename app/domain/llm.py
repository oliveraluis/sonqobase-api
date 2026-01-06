from typing import Protocol, Optional


class LLMProvider(Protocol):
    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str: ...