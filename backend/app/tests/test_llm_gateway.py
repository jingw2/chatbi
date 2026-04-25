import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ── build_provider factory ─────────────────────────────────────────────────────

class TestBuildProvider:
    def test_openai_type_returns_openai_provider(self):
        from app.llm_gateway.base import build_provider
        from app.llm_gateway.openai_provider import OpenAIProvider
        provider = build_provider("openai", "gpt-4o", "sk-key", "")
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4o"

    def test_openai_compatible_returns_openai_provider(self):
        from app.llm_gateway.base import build_provider
        from app.llm_gateway.openai_provider import OpenAIProvider
        provider = build_provider(
            "openai_compatible", "Qwen2.5-7B-Instruct", "none", "http://vllm:8001/v1"
        )
        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "Qwen2.5-7B-Instruct"

    def test_anthropic_type_returns_anthropic_provider(self):
        from app.llm_gateway.base import build_provider
        from app.llm_gateway.anthropic_provider import AnthropicProvider
        provider = build_provider(
            "anthropic", "claude-sonnet-4-6", "sk-ant-key", ""
        )
        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-sonnet-4-6"

    def test_unknown_provider_type_raises_value_error(self):
        from app.llm_gateway.base import build_provider
        with pytest.raises(ValueError, match="Unknown provider type"):
            build_provider("gemini", "gemini-pro", "key", "")
