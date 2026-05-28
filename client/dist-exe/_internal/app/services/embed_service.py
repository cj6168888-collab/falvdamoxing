"""
Embedding service for vectorizing text and calculating similarity.

DashScope is used when configured. Without an API key, the service returns a
stable deterministic placeholder vector so dev/test behavior is reproducible.
"""

from __future__ import annotations

import hashlib
import logging
import math
from typing import List

from app.config import settings

try:
    import dashscope
    from dashscope import TextEmbedding

    HAS_DASHSCOPE = True
except ImportError:
    dashscope = None
    TextEmbedding = None
    HAS_DASHSCOPE = False


logger = logging.getLogger(__name__)


class EmbeddingService:
    """Text embedding service."""

    def __init__(self):
        self.model = None
        self.local_model = None
        self._initialized = False
        self.embedding_type = None

    def _ensure_initialized(self):
        """Lazy initialization."""
        if self._initialized:
            return

        self._initialized = True
        if HAS_DASHSCOPE and settings.dashscope_api_key:
            dashscope.api_key = settings.dashscope_api_key
            self.embedding_type = "dashscope"
            logger.info("Using DashScope embedding API.")
        else:
            self.embedding_type = "placeholder"
            logger.info("Embedding API is not configured; using deterministic placeholder embeddings.")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Convert texts to vectors."""
        self._ensure_initialized()
        if self.embedding_type == "dashscope":
            return self._embed_dashscope(texts)

        return [self._embed_deterministic_placeholder(text) for text in texts]

    def _embed_deterministic_placeholder(
        self,
        text: str,
        dimensions: int = 1024,
    ) -> List[float]:
        """Return a stable lightweight embedding for dev/test environments."""
        values = []
        seed = text.encode("utf-8", errors="ignore")
        counter = 0

        while len(values) < dimensions:
            digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            for byte in digest:
                values.append((byte / 127.5) - 1.0)
                if len(values) == dimensions:
                    break
            counter += 1

        return values

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Use a local model when one is explicitly attached."""
        if self.local_model is None:
            return [[0.0] * 1024 for _ in texts]

        embeddings = self.local_model.encode(texts)
        return embeddings.tolist()

    def _embed_dashscope(self, texts: List[str]) -> List[List[float]]:
        """Use DashScope embedding API."""
        try:
            response = TextEmbedding.call(
                model=TextEmbedding.Models.text_embedding_v1,
                input=texts,
            )
            if response.status_code == 200:
                return [item["embedding"] for item in response.output["embeddings"]]

            raise RuntimeError(f"API error: {response.message}")
        except Exception:
            logger.exception("DashScope embedding failed; returning zero vectors.")
            return [[0.0] * 1536 for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        """Convert a single query to a vector."""
        embeddings = self.embed([query])
        return embeddings[0] if embeddings else []

    def similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity for two vectors."""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


embedding_service = EmbeddingService()
