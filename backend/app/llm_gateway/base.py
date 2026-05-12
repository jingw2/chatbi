from __future__ import annotations
from abc import ABC, abstractmethod

# Providers that speak the OpenAI Chat Completions API (cloud or self-hosted).
# Each entry maps a provider name to its default base URL.
# "openai" and "openai_compatible" use the SDK default / user-supplied URL.
PROVIDER_DEFAULT_BASE_URLS: dict[str, str] = {
    "deepseek": "https://api.deepseek.com/v1",
    "qwen":     "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "kimi":     "https://api.moonshot.cn/v1",
    "glm":      "https://open.bigmodel.cn/api/paas/v4",
    "minimax":  "https://api.minimax.chat/v1",
    "gemini":   "https://generativelanguage.googleapis.com/v1beta/openai/",
}

_OPENAI_COMPATIBLE = frozenset(PROVIDER_DEFAULT_BASE_URLS) | {"openai", "openai_compatible"}


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
        provider_type: one of the ModelProvider enum values
        model_name:    model identifier string
        api_key:       API key (pass "none" for local vLLM)
        base_url:      override endpoint URL; empty string = use provider default
    """
    from app.llm_gateway.openai_provider import OpenAIProvider
    from app.llm_gateway.anthropic_provider import AnthropicProvider

    if provider_type in _OPENAI_COMPATIBLE:
        effective_url = base_url or PROVIDER_DEFAULT_BASE_URLS.get(provider_type) or None
        return OpenAIProvider(
            model=model_name,
            api_key=api_key or "none",
            base_url=effective_url,
        )
    if provider_type == "anthropic":
        return AnthropicProvider(
            model=model_name,
            api_key=api_key,
            base_url=base_url or None,
        )
    raise ValueError(
        f"Unknown provider type: {provider_type!r}. "
        f"Supported: {sorted(_OPENAI_COMPATIBLE | {'anthropic'})}"
    )
