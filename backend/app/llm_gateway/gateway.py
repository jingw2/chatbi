from __future__ import annotations
from app.llm_gateway.base import LLMProvider, build_provider
from app.core.config import settings


def _messages(system: str | None, user: str) -> list[dict[str, str]]:
    """Build an OpenAI-style messages list from optional system + user strings."""
    msgs: list[dict[str, str]] = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": user})
    return msgs


class LLMGateway:
    """Unified interface to all three LLM model roles.

    Each role (intent / text_to_sql / base) is backed by an independent
    LLMProvider instance configured from settings. Callers pass optional
    providers for testing — omit them in production to use settings.
    """

    def __init__(
        self,
        intent_provider: LLMProvider | None = None,
        text_to_sql_provider: LLMProvider | None = None,
        base_provider: LLMProvider | None = None,
    ):
        self._intent: LLMProvider = intent_provider or build_provider(
            settings.intent_model_provider,
            settings.intent_model_name,
            settings.intent_model_api_key,
            settings.intent_model_base_url,
        )
        self._text_to_sql: LLMProvider = text_to_sql_provider or build_provider(
            settings.text_to_sql_provider,
            settings.text_to_sql_model_name,
            settings.text_to_sql_api_key,
            settings.text_to_sql_base_url,
        )
        self._base: LLMProvider = base_provider or build_provider(
            settings.base_model_provider,
            settings.base_model_name,
            settings.base_model_api_key,
            settings.base_model_base_url,
        )

    async def intent(self, user_prompt: str, system: str | None = None) -> str:
        """Classify user intent. Typically returns one of:
        data_query | definition | clarify | fixed_workflow | chitchat
        """
        return await self._intent.complete(_messages(system, user_prompt))

    async def text_to_sql(self, user_prompt: str, system: str | None = None) -> str:
        """Generate SQL from a natural-language query + schema context prompt."""
        return await self._text_to_sql.complete(_messages(system, user_prompt))

    async def base(self, user_prompt: str, system: str | None = None) -> str:
        """Generate natural-language insights and decision suggestions."""
        return await self._base.complete(_messages(system, user_prompt))


# Module-level singleton — created once at import time using settings.
# Query engine imports this directly:
#   from app.llm_gateway import llm_gateway
llm_gateway = LLMGateway()
