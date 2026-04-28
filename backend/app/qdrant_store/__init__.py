from app.qdrant_store.store import QdrantStore
from app.core.config import settings

qdrant_store = QdrantStore(url=settings.qdrant_url)

__all__ = ["QdrantStore", "qdrant_store"]
