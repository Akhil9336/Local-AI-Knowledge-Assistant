import pytest
from rag.document_loader import PageText
from rag.text_splitter import split_pages


def test_chunks_obey_size_overlap_and_pages():
    chunks = split_pages([PageText("abcdefghij", 2)], chunk_size=6, overlap=2)
    assert [c.text for c in chunks] == ["abcdef", "efghij"]
    assert all(c.page == 2 for c in chunks)


def test_chunking_rejects_invalid_overlap():
    with pytest.raises(ValueError):
        split_pages([PageText("x")], chunk_size=4, overlap=4)
