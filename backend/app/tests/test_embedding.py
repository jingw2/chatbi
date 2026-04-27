import pytest
from unittest.mock import MagicMock, patch
import numpy as np


class TestEmbeddingService:
    def test_embed_calls_flag_model_encode(self):
        with patch("app.embedding.service.FlagModel") as MockFlagModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 1024, [0.2] * 1024])
            MockFlagModel.return_value = mock_model

            from app.embedding.service import EmbeddingService
            svc = EmbeddingService(model_name="BAAI/bge-m3")
            result = svc.embed(["text A", "text B"])

        assert len(result) == 2
        assert len(result[0]) == 1024
        mock_model.encode.assert_called_once_with(
            ["text A", "text B"], batch_size=12, max_length=8192
        )

    def test_embed_lazy_loads_model_on_first_call(self):
        with patch("app.embedding.service.FlagModel") as MockFlagModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 1024])
            MockFlagModel.return_value = mock_model

            from app.embedding.service import EmbeddingService
            svc = EmbeddingService(model_name="BAAI/bge-m3")
            MockFlagModel.assert_not_called()  # not loaded yet
            svc.embed(["hi"])
            MockFlagModel.assert_called_once()

    def test_embed_reuses_same_model_instance(self):
        with patch("app.embedding.service.FlagModel") as MockFlagModel:
            mock_model = MagicMock()
            mock_model.encode.return_value = np.array([[0.1] * 1024])
            MockFlagModel.return_value = mock_model

            from app.embedding.service import EmbeddingService
            svc = EmbeddingService(model_name="BAAI/bge-m3")
            svc.embed(["a"])
            svc.embed(["b"])
            assert MockFlagModel.call_count == 1

    def test_rerank_calls_flag_reranker_compute_score(self):
        with patch("app.embedding.service.FlagReranker") as MockReranker:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.9, 0.3, 0.7]
            MockReranker.return_value = mock_reranker

            from app.embedding.service import EmbeddingService
            svc = EmbeddingService(reranker_name="BAAI/bge-reranker-v2-m3")
            result = svc.rerank("query", ["p1", "p2", "p3"])

        assert result == [0.9, 0.3, 0.7]
        mock_reranker.compute_score.assert_called_once_with(
            [["query", "p1"], ["query", "p2"], ["query", "p3"]], normalize=True
        )

    def test_rerank_lazy_loads_reranker(self):
        with patch("app.embedding.service.FlagReranker") as MockReranker:
            mock_reranker = MagicMock()
            mock_reranker.compute_score.return_value = [0.5]
            MockReranker.return_value = mock_reranker

            from app.embedding.service import EmbeddingService
            svc = EmbeddingService()
            MockReranker.assert_not_called()
            svc.rerank("q", ["p"])
            MockReranker.assert_called_once()

    def test_embed_raises_import_error_when_flag_model_none(self):
        with patch("app.embedding.service.FlagModel", None):
            from app.embedding.service import EmbeddingService
            svc = EmbeddingService()
            with pytest.raises(ImportError, match="FlagEmbedding is not installed"):
                svc.embed(["text"])
