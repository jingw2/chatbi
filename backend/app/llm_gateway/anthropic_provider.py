from app.llm_gateway.base import LLMProvider


class AnthropicProvider(LLMProvider):
    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url

    async def complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        raise NotImplementedError
