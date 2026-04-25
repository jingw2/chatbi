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


# ── OpenAIProvider ─────────────────────────────────────────────────────────────

class TestOpenAIProvider:
    @pytest.mark.asyncio
    async def test_complete_returns_message_content(self):
        with patch("app.llm_gateway.openai_provider.AsyncOpenAI") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="SELECT 1"))]
                )
            )
            from app.llm_gateway.openai_provider import OpenAIProvider
            provider = OpenAIProvider(model="gpt-4o", api_key="sk-key")
            result = await provider.complete([{"role": "user", "content": "Write SQL"}])
        assert result == "SELECT 1"

    @pytest.mark.asyncio
    async def test_complete_uses_configured_model_name(self):
        with patch("app.llm_gateway.openai_provider.AsyncOpenAI") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="ok"))]
                )
            )
            from app.llm_gateway.openai_provider import OpenAIProvider
            provider = OpenAIProvider(
                model="Qwen2.5-Coder-32B-Instruct",
                api_key="none",
                base_url="http://vllm:8001/v1",
            )
            await provider.complete([{"role": "user", "content": "hi"}])
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "Qwen2.5-Coder-32B-Instruct"

    @pytest.mark.asyncio
    async def test_complete_passes_messages_verbatim(self):
        with patch("app.llm_gateway.openai_provider.AsyncOpenAI") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="ok"))]
                )
            )
            from app.llm_gateway.openai_provider import OpenAIProvider
            provider = OpenAIProvider(model="gpt-4o", api_key="sk-key")
            msgs = [
                {"role": "system", "content": "You are a SQL expert"},
                {"role": "user", "content": "Write a query"},
            ]
            await provider.complete(msgs)
            call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == msgs

    @pytest.mark.asyncio
    async def test_complete_none_content_returns_empty_string(self):
        with patch("app.llm_gateway.openai_provider.AsyncOpenAI") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content=None))]
                )
            )
            from app.llm_gateway.openai_provider import OpenAIProvider
            provider = OpenAIProvider(model="gpt-4o", api_key="sk-key")
            result = await provider.complete([{"role": "user", "content": "hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_base_url_passed_to_client(self):
        with patch("app.llm_gateway.openai_provider.AsyncOpenAI") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                return_value=MagicMock(
                    choices=[MagicMock(message=MagicMock(content="ok"))]
                )
            )
            from app.llm_gateway.openai_provider import OpenAIProvider
            OpenAIProvider(
                model="Qwen2.5-7B-Instruct",
                api_key="none",
                base_url="http://vllm:8001/v1",
            )
            _, init_kwargs = MockCls.call_args
        assert init_kwargs.get("base_url") == "http://vllm:8001/v1"


# ── AnthropicProvider ──────────────────────────────────────────────────────────

class TestAnthropicProvider:
    @pytest.mark.asyncio
    async def test_complete_returns_first_content_text(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(
                    content=[MagicMock(text="Sales dropped 10%")]
                )
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant")
            result = await provider.complete([{"role": "user", "content": "Analyze"}])
        assert result == "Sales dropped 10%"

    @pytest.mark.asyncio
    async def test_system_message_extracted_and_passed_as_system_param(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[MagicMock(text="ok")])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant")
            await provider.complete([
                {"role": "system", "content": "You are a BI analyst"},
                {"role": "user", "content": "Summarize sales"},
            ])
            call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "You are a BI analyst"
        assert call_kwargs["messages"] == [{"role": "user", "content": "Summarize sales"}]

    @pytest.mark.asyncio
    async def test_no_system_message_omits_system_kwarg(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[MagicMock(text="ok")])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant")
            await provider.complete([{"role": "user", "content": "Hello"}])
            call_kwargs = mock_client.messages.create.call_args.kwargs
        assert "system" not in call_kwargs

    @pytest.mark.asyncio
    async def test_custom_base_url_passed_to_client_constructor(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[MagicMock(text="ok")])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            AnthropicProvider(
                model="claude-sonnet-4-6",
                api_key="sk-ant",
                base_url="http://my-proxy/anthropic",
            )
            _, init_kwargs = MockCls.call_args
        assert init_kwargs.get("base_url") == "http://my-proxy/anthropic"

    @pytest.mark.asyncio
    async def test_no_base_url_does_not_pass_base_url_kwarg(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[MagicMock(text="ok")])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant", base_url=None)
            _, init_kwargs = MockCls.call_args
        assert "base_url" not in init_kwargs

    @pytest.mark.asyncio
    async def test_complete_empty_content_returns_empty_string(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant")
            result = await provider.complete([{"role": "user", "content": "hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_multiple_system_messages_joined_with_double_newline(self):
        with patch("app.llm_gateway.anthropic_provider.AsyncAnthropic") as MockCls:
            mock_client = MagicMock()
            MockCls.return_value = mock_client
            mock_client.messages.create = AsyncMock(
                return_value=MagicMock(content=[MagicMock(text="ok")])
            )
            from app.llm_gateway.anthropic_provider import AnthropicProvider
            provider = AnthropicProvider(model="claude-sonnet-4-6", api_key="sk-ant")
            await provider.complete([
                {"role": "system", "content": "Be concise"},
                {"role": "system", "content": "Use metric units"},
                {"role": "user", "content": "Tell me the distance"},
            ])
            call_kwargs = mock_client.messages.create.call_args.kwargs
        assert call_kwargs["system"] == "Be concise\n\nUse metric units"
        assert call_kwargs["messages"] == [{"role": "user", "content": "Tell me the distance"}]


# ── _messages helper ───────────────────────────────────────────────────────────

class TestMessagesHelper:
    def test_user_only_produces_single_user_message(self):
        from app.llm_gateway.gateway import _messages
        result = _messages(None, "hello")
        assert result == [{"role": "user", "content": "hello"}]

    def test_system_plus_user_produces_two_messages_in_order(self):
        from app.llm_gateway.gateway import _messages
        result = _messages("Be concise", "hello")
        assert result == [
            {"role": "system", "content": "Be concise"},
            {"role": "user", "content": "hello"},
        ]

    def test_empty_system_omits_system_message(self):
        from app.llm_gateway.gateway import _messages
        result = _messages("", "hello")
        assert result == [{"role": "user", "content": "hello"}]


# ── LLMGateway ────────────────────────────────────────────────────────────────

class TestLLMGateway:
    def _mock_provider(self, return_value: str):
        provider = MagicMock()
        provider.complete = AsyncMock(return_value=return_value)
        return provider

    @pytest.mark.asyncio
    async def test_intent_delegates_to_intent_provider(self):
        from app.llm_gateway.gateway import LLMGateway
        intent_p = self._mock_provider("data_query")
        gw = LLMGateway(
            intent_provider=intent_p,
            text_to_sql_provider=self._mock_provider(""),
            base_provider=self._mock_provider(""),
        )
        result = await gw.intent("上周华东区出库量")
        assert result == "data_query"
        intent_p.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_text_to_sql_delegates_to_sql_provider(self):
        from app.llm_gateway.gateway import LLMGateway
        sql_p = self._mock_provider("SELECT * FROM orders WHERE region = '华东'")
        gw = LLMGateway(
            intent_provider=self._mock_provider(""),
            text_to_sql_provider=sql_p,
            base_provider=self._mock_provider(""),
        )
        result = await gw.text_to_sql("上周出库量 for 华东")
        assert result == "SELECT * FROM orders WHERE region = '华东'"
        sql_p.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_base_delegates_to_base_provider(self):
        from app.llm_gateway.gateway import LLMGateway
        base_p = self._mock_provider("Sales in 华东 dropped 10% week-over-week.")
        gw = LLMGateway(
            intent_provider=self._mock_provider(""),
            text_to_sql_provider=self._mock_provider(""),
            base_provider=base_p,
        )
        result = await gw.base("生成洞察", system="You are a BI analyst")
        assert result == "Sales in 华东 dropped 10% week-over-week."
        base_p.complete.assert_called_once()

    @pytest.mark.asyncio
    async def test_system_prompt_prepended_to_messages(self):
        from app.llm_gateway.gateway import LLMGateway
        intent_p = self._mock_provider("data_query")
        gw = LLMGateway(
            intent_provider=intent_p,
            text_to_sql_provider=self._mock_provider(""),
            base_provider=self._mock_provider(""),
        )
        await gw.intent("question", system="Classify the intent")
        messages_arg = intent_p.complete.call_args.args[0]
        assert messages_arg[0] == {"role": "system", "content": "Classify the intent"}
        assert messages_arg[1] == {"role": "user", "content": "question"}

    @pytest.mark.asyncio
    async def test_each_role_uses_independent_provider(self):
        from app.llm_gateway.gateway import LLMGateway
        intent_p = self._mock_provider("intent_result")
        sql_p = self._mock_provider("sql_result")
        base_p = self._mock_provider("base_result")
        gw = LLMGateway(
            intent_provider=intent_p,
            text_to_sql_provider=sql_p,
            base_provider=base_p,
        )
        i = await gw.intent("q")
        s = await gw.text_to_sql("q")
        b = await gw.base("q")
        assert i == "intent_result"
        assert s == "sql_result"
        assert b == "base_result"
        intent_p.complete.assert_called_once()
        sql_p.complete.assert_called_once()
        base_p.complete.assert_called_once()

    def test_singleton_is_llmgateway_instance(self):
        from app.llm_gateway import llm_gateway, LLMGateway
        assert isinstance(llm_gateway, LLMGateway)
