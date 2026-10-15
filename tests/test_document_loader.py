import pytest
from rag.document_loader import load_document, stable_document_id


def test_text_and_markdown_extraction():
    assert load_document("a.txt", b"hello").text == "hello"
    assert load_document("b.md", b"# Title").text == "# Title"


def test_pdf_pages_and_page_metadata(monkeypatch):
    class FakePage:
        def extract_text(self):
            return "Page text"

    class FakeReader:
        is_encrypted = False
        pages = [FakePage(), FakePage()]

        def __init__(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("rag.document_loader.PdfReader", FakeReader)
    result = load_document("report.pdf", b"synthetic pdf")
    assert [page.page for page in result.pages] == [1, 2]
    assert result.text == "Page text\n\nPage text"


def test_scanned_pdf_reports_ocr_limitation(monkeypatch):
    class FakePage:
        def extract_text(self):
            return ""

    class FakeReader:
        is_encrypted = False
        pages = [FakePage()]

        def __init__(self, *_args, **_kwargs):
            pass

    monkeypatch.setattr("rag.document_loader.PdfReader", FakeReader)
    with pytest.raises(ValueError, match="OCR"):
        load_document("scan.pdf", b"synthetic pdf")


def test_empty_unsupported_and_scanned_pdf_errors():
    with pytest.raises(ValueError, match="empty"):
        load_document("empty.txt", b"")
    with pytest.raises(ValueError, match="Unsupported"):
        load_document("data.docx", b"text")


def test_stable_document_identifier():
    digest = "abc123"
    assert stable_document_id(digest, "Report.TXT") == stable_document_id(digest, "report.txt")
    assert stable_document_id(digest, "report.txt") != stable_document_id("changed", "report.txt")
