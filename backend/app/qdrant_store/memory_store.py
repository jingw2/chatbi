"""In-memory vector store — drop-in replacement for QdrantStore in lite mode.

Uses cosine similarity over numpy arrays. No external dependencies beyond numpy.
Suitable for small-to-medium datasets (< 100k vectors).
"""
from __future__ import annotations

import numpy as np


class InMemoryVectorStore:
    """In-memory vector store with the same interface as QdrantStore."""

    def __init__(self):
        # {collection_name: {id: {"vector": np.array, "payload": dict}}}
        self._collections: dict[str, dict[str, dict]] = {}

    async def ensure_collection(self, name: str) -> None:
        if name not in self._collections:
            self._collections[name] = {}

    async def upsert(self, collection: str, points: list[dict]) -> None:
        if not points:
            return
        if collection not in self._collections:
            self._collections[collection] = {}
        for p in points:
            self._collections[collection][p["id"]] = {
                "vector": np.array(p["vector"], dtype=np.float32),
                "payload": p["payload"],
            }

    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 20,
        filter_: dict | None = None,
    ) -> list[dict]:
        if collection not in self._collections:
            return []

        query_vec = np.array(vector, dtype=np.float32)
        query_norm = np.linalg.norm(query_vec)
        if query_norm == 0:
            return []
        query_vec = query_vec / query_norm

        candidates = []
        for point_id, data in self._collections[collection].items():
            # Apply filter
            if filter_:
                match = all(
                    data["payload"].get(k) == v for k, v in filter_.items()
                )
                if not match:
                    continue

            doc_vec = data["vector"]
            doc_norm = np.linalg.norm(doc_vec)
            if doc_norm == 0:
                continue
            score = float(np.dot(query_vec, doc_vec / doc_norm))
            candidates.append({"id": point_id, "score": score, "payload": data["payload"]})

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]

    async def delete(self, collection: str, ids: list[str]) -> None:
        if collection not in self._collections:
            return
        for point_id in ids:
            self._collections[collection].pop(point_id, None)
