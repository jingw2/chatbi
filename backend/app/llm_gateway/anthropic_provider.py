from anthropic import AsyncAnthropic
from app.llm_gateway.base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Wraps the Anthropic Messages API.

    The Anthropic API treats 'system' as a top-level parameter, not a message
    role. This provider extracts any system-role messages from the messages list
    and passes them via the `system` kwarg. If no system message is present,
    the `system` kwarg is omitted entirely (Anthropic rejects system="").
    """

    def __init__(self, model: str, api_key: str, base_url: str | None = None):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        init_kwargs: dict = {"api_key": api_key}
        if base_url:
            init_kwargs["base_url"] = base_url
        self.client = AsyncAnthropic(**init_kwargs)

    async def complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        user_messages = [m for m in messages if m["role"] != "system"]

        create_kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": user_messages,
        }
        if system_parts:
            create_kwargs["system"] = "\n\n".join(system_parts)

        response = await self.client.messages.create(**create_kwargs)
        return response.content[0].text
