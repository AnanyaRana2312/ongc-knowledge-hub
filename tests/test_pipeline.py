import pytest
from unittest.mock import MagicMock, patch
from langchain_core.documents import Document

from backend.ingestion.pipeline import run_ingestion_pipeline


@patch("pathlib.Path.exists", return_value=False)
def test_run_ingestion_pipeline_file_not_found(mock_exists):
    with pytest.raises(FileNotFoundError):
        run_ingestion_pipeline("nonexistent.txt", "safety")


@patch("pathlib.Path.exists", return_value=True)
@patch("backend.ingestion.pipeline.is_scanned_pdf")
@patch("backend.ingestion.pipeline.load_document")
@patch("backend.ingestion.pipeline.chunk_documents")
@patch("backend.ingestion.pipeline.add_documents_to_store")
def test_run_ingestion_pipeline_standard_success(
    mock_add_store, mock_chunk, mock_load, mock_is_scanned, mock_exists
):
    mock_is_scanned.return_value = False
    mock_load.return_value = [
        Document(page_content="Standard document text", metadata={"type": "txt"})
    ]
    mock_chunk.return_value = [
        Document(page_content="Standard document text", metadata={"type": "txt"})
    ]

    result = run_ingestion_pipeline("dummy.txt", "drilling")

    mock_load.assert_called_once_with("dummy.txt")
    mock_chunk.assert_called_once()
    mock_add_store.assert_called_once()

    # Check if domain was propagated to chunks
    stored_chunks = mock_add_store.call_args[0][0]
    assert stored_chunks[0].metadata["domain"] == "drilling"

    assert result["filename"] == "dummy.txt"
    assert result["domain"] == "drilling"
    assert result["num_chunks"] == 1
    assert result["status"] == "success"
    assert "txt" in result["loaders"]


@patch("pathlib.Path.exists", return_value=True)
@patch("backend.ingestion.pipeline.is_scanned_pdf")
@patch("backend.ingestion.pipeline.ocr_pdf")
@patch("backend.ingestion.pipeline.chunk_documents")
@patch("backend.ingestion.pipeline.add_documents_to_store")
def test_run_ingestion_pipeline_ocr_success(
    mock_add_store, mock_chunk, mock_ocr, mock_is_scanned, mock_exists
):
    mock_is_scanned.return_value = True
    mock_ocr.return_value = [
        Document(page_content="OCR extracted text", metadata={"loader": "ocr_pypdf_fallback"})
    ]
    mock_chunk.return_value = [
        Document(page_content="OCR extracted text", metadata={"loader": "ocr_pypdf_fallback"})
    ]

    # Suffix needs to be .pdf to trigger scanned check routing logic
    result = run_ingestion_pipeline("scanned.pdf", "safety")

    mock_is_scanned.assert_called_once_with("scanned.pdf")
    mock_ocr.assert_called_once_with("scanned.pdf")
    mock_chunk.assert_called_once()
    mock_add_store.assert_called_once()

    assert result["filename"] == "scanned.pdf"
    assert result["domain"] == "safety"
    assert result["num_chunks"] == 1
    assert result["status"] == "success"
    assert "ocr_pypdf_fallback" in result["loaders"]


@patch("pathlib.Path.exists", return_value=True)
@patch("backend.ingestion.pipeline.is_scanned_pdf")
@patch("backend.ingestion.pipeline.load_document")
def test_run_ingestion_pipeline_empty_doc(mock_load, mock_is_scanned, mock_exists):
    mock_is_scanned.return_value = False
    mock_load.return_value = []

    result = run_ingestion_pipeline("empty.txt", "safety")

    assert result["status"] == "warning_empty"
    assert result["num_chunks"] == 0
