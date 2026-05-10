from app.core.config import settings

if settings.is_lite:
    from app.qdrant_store.memory_store import InMemoryVectorStore
    qdrant_store = InMemoryVectorStore()
else:
    from app.qdrant_store.store import QdrantStore
    qdrant_store = QdrantStore(url=settings.qdrant_url)

__all__ = ["qdrant_store"]
