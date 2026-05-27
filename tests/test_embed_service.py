from app.services.embed_service import EmbeddingService


def test_placeholder_embeddings_are_deterministic(monkeypatch):
    service = EmbeddingService()
    service.embedding_type = "placeholder"
    service._initialized = True

    first = service.embed_query("same legal text")
    second = service.embed_query("same legal text")
    different = service.embed_query("different legal text")

    assert len(first) == 1024
    assert first == second
    assert first != different


def test_similarity_handles_zero_vectors():
    service = EmbeddingService()

    assert service.similarity([0.0, 0.0], [1.0, 2.0]) == 0.0
