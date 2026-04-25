from openai import AsyncOpenAI
from app.llm_gateway.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """Handles both 'openai' and 'openai_compatible' provider types.

    For local vLLM: pass api_key="none" and base_url="http://vllm:8001/v1".
    For cloud OpenAI: pass real api_key, leave base_url=None.
    For other OpenAI-compatible APIs (Kimi, DeepSeek, etc.): set base_url.
    """

    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,  # type: ignore[arg-type]
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""
