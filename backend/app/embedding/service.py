from __future__ import annotations

try:
    from FlagEmbedding import FlagModel, FlagReranker  # type: ignore[import]
except Exception:
    FlagModel = None  # type: ignore[assignment,misc]
    FlagReranker = None  # type: ignore[assignment,misc]


class EmbeddingService:
    """Wraps FlagEmbedding bge-m3 (embed) and bge-reranker-v2-m3 (rerank).

    Models are lazy-loaded on first use so import-time cost is zero.
    FlagEmbedding is optional (requirements-ml.txt). If not installed,
    calling embed() or rerank() raises ImportError with a clear message.
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        reranker_name: str = "BAAI/bge-reranker-v2-m3",
    ):
        self._model_name = model_name
        self._reranker_name = reranker_name
        self._model = None
        self._reranker = None

    def _get_model(self):
        if self._model is None:
            if FlagModel is None:
                raise ImportError(
                    "FlagEmbedding is not installed. "
                    "Run: pip install -r requirements-ml.txt"
                )
            self._model = FlagModel(self._model_name, use_fp16=True)
        return self._model

    def _get_reranker(self):
        if self._reranker is None:
            if FlagReranker is None:
                raise ImportError(
                    "FlagEmbedding is not installed. "
                    "Run: pip install -r requirements-ml.txt"
                )
            self._reranker = FlagReranker(self._reranker_name, use_fp16=True)
        return self._reranker

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed texts using bge-m3. Returns list of 1024-dim vectors."""
        model = self._get_model()
        vectors = model.encode(texts, batch_size=12, max_length=8192)
        return vectors.tolist()

    def rerank(self, query: str, passages: list[str]) -> list[float]:
        """Rerank passages by relevance to query. Returns normalized scores (0-1)."""
        reranker = self._get_reranker()
        pairs = [[query, p] for p in passages]
        return reranker.compute_score(pairs, normalize=True)
