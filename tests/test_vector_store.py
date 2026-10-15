from types import SimpleNamespace
import pytest
from rag.vector_store import VectorStore


def test_empty_collection_and_document_lifecycle(tmp_path):
    store = VectorStore(tmp_path, "test-embed")
    assert store.search([0.0, 1.0]) == []
    chunks = [SimpleNamespace(text="alpha", chunk_number=0, page=3),
              SimpleNamespace(text="beta", chunk_number=1, page=None)]
    store.upsert_document("doc", "a.pdf", "hash", chunks, [[1.0, 0.0], [0.0, 1.0]])
    assert store.has_document("doc")
    assert store.documents()[0]["chunks"] == 2
    result = store.search([1.0, 0.0], top_k=1)
    assert result[0]["metadata"]["page"] == 3
    store.delete_document("doc")
    assert not store.has_document("doc")


def test_embedding_model_mismatch_is_explicit(tmp_path):
    VectorStore(tmp_path, "embed-a")
    with pytest.raises(ValueError, match="Clear the index"):
        VectorStore(tmp_path, "embed-b")


def test_reindex_replaces_old_chunks_after_upsert(tmp_path):
    store = VectorStore(tmp_path, "embed")
    first = [SimpleNamespace(text="old", chunk_number=0, page=None),
             SimpleNamespace(text="tail", chunk_number=1, page=None)]
    store.upsert_document("old-version", "same.txt", "oldhash", first, [[1., 0.], [0., 1.]])
    updated = [SimpleNamespace(text="updated", chunk_number=0, page=None)]
    store.upsert_document("new-version", "same.txt", "newhash", updated, [[1., 0.]])
    assert store.documents() == [{"document_id": "new-version", "filename": "same.txt", "chunks": 1}]
