from __future__ import annotations
from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.0,
    ) -> str:
        """Send messages to the LLM and return the text response."""
        ...


def build_provider(
    provider_type: str,
    model_name: str,
    api_key: str,
    base_url: str,
) -> LLMProvider:
    """Instantiate the correct LLMProvider from config values.

    Args:
        provider_type: "openai" | "openai_compatible" | "anthropic"
        model_name:    model identifier string
        api_key:       API key (pass "none" for local vLLM)
        base_url:      override endpoint URL (empty string = use SDK default)
    """
    from app.llm_gateway.openai_provider import OpenAIProvider
    from app.llm_gateway.anthropic_provider import AnthropicProvider

    if provider_type in ("openai", "openai_compatible"):
        return OpenAIProvider(
            model=model_name,
            api_key=api_key or "none",
            base_url=base_url or None,
        )
    elif provider_type == "anthropic":
        return AnthropicProvider(
            model=model_name,
            api_key=api_key,
            base_url=base_url or None,
        )
    else:
        raise ValueError(
            f"Unknown provider type: {provider_type!r}. "
            "Expected 'openai', 'openai_compatible', or 'anthropic'."
        )
