from __future__ import annotations

from app.embedding.service import EmbeddingService

_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        from app.core.config import settings
        _embedding_service = EmbeddingService(
            model_name=settings.embedding_model_name,
            reranker_name=settings.reranker_model_name,
        )
    return _embedding_service


# Backwards-compatible alias — resolved lazily on first access
class _LazyProxy:
    def __getattr__(self, name: str):
        return getattr(get_embedding_service(), name)


embedding_service = _LazyProxy()

__all__ = ["EmbeddingService", "embedding_service", "get_embedding_service"]
