from app.services import rag_service as rag_module
from app.core.tenant_context import TenantContext
from app.services.ai_audit_service import build_retrieval_audit_payload


def test_rag_service_degrades_when_chromadb_unavailable(monkeypatch):
    monkeypatch.setattr(rag_module, "CHROMADB_AVAILABLE", False)
    monkeypatch.setattr(rag_module, "CHROMADB_IMPORT_ERROR", ImportError("missing chromadb"))

    service = rag_module.RAGService(audit_recorder=None)

    assert service.is_available is False
    assert service.add_document(case_id=1, doc_id=2, text="contract text") == ""
    assert service.search("contract", case_id=1) == []
    assert service.get_context("contract", case_id=1) == ""
    assert service.delete_case_documents(case_id=1) is None


def test_rag_service_degrades_when_chromadb_initialization_fails(monkeypatch):
    class FailingChroma:
        @staticmethod
        def PersistentClient(path):
            raise RuntimeError("cannot open vector store")

    monkeypatch.setattr(rag_module, "CHROMADB_AVAILABLE", True)
    monkeypatch.setattr(rag_module, "chromadb", FailingChroma)

    service = rag_module.RAGService(audit_recorder=None)

    assert service.is_available is False
    assert service.search("contract", case_id=1) == []


def test_rag_search_post_filters_and_audits_tenant_scope(monkeypatch):
    class FakeCollection:
        def __init__(self):
            self.where = None

        def query(self, **kwargs):
            self.where = kwargs["where"]
            return {
                "ids": [["chunk-a", "chunk-b", "chunk-c"]],
                "documents": [["tenant a text", "tenant b text", "other case text"]],
                "metadatas": [[
                    {"case_id": 1, "tenant_id": "tenant-a", "doc_id": 10, "doc_type": "contract"},
                    {"case_id": 1, "tenant_id": "tenant-b", "doc_id": 20, "doc_type": "contract"},
                    {"case_id": 2, "tenant_id": "tenant-a", "doc_id": 30, "doc_type": "contract"},
                ]],
                "distances": [[0.1, 0.2, 0.3]],
            }

    collection = FakeCollection()
    audits = []
    service = object.__new__(rag_module.RAGService)
    service.chroma_client = object()
    service.collection = collection
    service._audit_recorder = lambda **kwargs: audits.append(kwargs)

    monkeypatch.setattr(rag_module.embedding_service, "embed_query", lambda query: [0.1])
    TenantContext.set_tenant("tenant-a")
    try:
        results = service.search("contract", case_id=1)
    finally:
        TenantContext.clear()

    assert collection.where == {"$and": [{"case_id": 1}, {"tenant_id": "tenant-a"}]}
    assert [result["metadata"]["doc_id"] for result in results] == [10]
    assert audits[0]["case_id"] == 1
    assert [result["metadata"]["doc_id"] for result in audits[0]["results"]] == [10]


def test_build_retrieval_audit_payload_records_case_tenant_and_sources():
    TenantContext.set_tenant("tenant-a")
    TenantContext.set_user("user-a")
    try:
        payload = build_retrieval_audit_payload(
            query="How should we answer?",
            case_id=7,
            results=[
                {"id": "chunk-1", "metadata": {"doc_id": 11}},
                {"id": "chunk-2", "metadata": {"doc_id": 11}},
                {"id": "chunk-3", "metadata": {"doc_id": 12}},
            ],
            purpose="rag_search",
        )
    finally:
        TenantContext.clear()

    assert payload["tenant_id"] == "tenant-a"
    assert payload["user_id"] == "user-a"
    assert payload["case_id"] == 7
    assert payload["retrieved_document_ids"] == [11, 12]
    assert payload["retrieved_chunk_ids"] == ["chunk-1", "chunk-2", "chunk-3"]
    assert payload["source_count"] == 3
    assert payload["query_hash"] != "How should we answer?"
