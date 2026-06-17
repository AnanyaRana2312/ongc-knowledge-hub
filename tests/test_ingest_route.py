import os
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import status

from backend.api.main import app
from backend.ingestion.ocr import TesseractMissingError

client = TestClient(app)


@patch("backend.api.routes.ingest.run_ingestion_pipeline")
def test_ingest_document_success(mock_run_pipeline):
    # Mock pipeline returns success summary (simulating background run success)
    mock_run_pipeline.return_value = {
        "filename": "test.txt",
        "domain": "safety",
        "num_chunks": 3,
        "status": "success",
        "loaders": ["txt"]
    }

    file_content = b"This is safety document content for ONGC operations."
    
    # Run request using FastAPI TestClient
    response = client.post(
        "/ingest/",
        files={"file": ("test.txt", file_content, "text/plain")},
        params={"domain": "safety"}
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["domain"] == "safety"
    assert data["status"] == "processing"
    assert "processed in the background" in data["message"]

    # Verify run_ingestion_pipeline was called correctly in the background task
    mock_run_pipeline.assert_called_once()
    args = mock_run_pipeline.call_args[0]
    assert "data\\temp\\test.txt" in args[0] or "data/temp/test.txt" in args[0]
    assert args[1] == "safety"

    # Verify temp file was cleaned up by background task cleanup helper
    temp_path = os.path.join("data", "temp", "test.txt")
    assert not os.path.exists(temp_path)


@patch("backend.api.routes.ingest.run_ingestion_pipeline")
def test_ingest_document_unsupported_format(mock_run_pipeline):
    # Format validation is synchronous, returns 400 immediately
    response = client.post(
        "/ingest/",
        files={"file": ("malicious.exe", b"binarycontent", "application/octet-stream")},
        params={"domain": "safety"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file type" in response.json()["detail"]
    mock_run_pipeline.assert_not_called()

    # Verify temp file was not created or was cleaned up
    temp_path = os.path.join("data", "temp", "malicious.exe")
    assert not os.path.exists(temp_path)


@patch("backend.api.routes.ingest.run_ingestion_pipeline")
def test_ingest_document_tesseract_missing(mock_run_pipeline):
    # Simulate pipeline throwing TesseractMissingError in the background task
    mock_run_pipeline.side_effect = TesseractMissingError("Tesseract OCR binary not found.")

    response = client.post(
        "/ingest/",
        files={"file": ("scanned.pdf", b"pdfcontent", "application/pdf")},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_run_pipeline.assert_called_once()

    # Verify temp file was cleaned up by background task cleanup helper
    temp_path = os.path.join("data", "temp", "scanned.pdf")
    assert not os.path.exists(temp_path)


@patch("backend.api.routes.ingest.run_ingestion_pipeline")
def test_ingest_document_generic_error(mock_run_pipeline):
    # Simulate pipeline throwing arbitrary unexpected error in the background task
    mock_run_pipeline.side_effect = RuntimeError("Database connection timed out.")

    response = client.post(
        "/ingest/",
        files={"file": ("test.docx", b"docxcontent", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    mock_run_pipeline.assert_called_once()

    # Verify temp file was cleaned up by background task cleanup helper
    temp_path = os.path.join("data", "temp", "test.docx")
    assert not os.path.exists(temp_path)
