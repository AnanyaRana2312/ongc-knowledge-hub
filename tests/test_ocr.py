import sys
from unittest.mock import MagicMock

# Mock pdf2image at the very top before any ingestion code is imported
# This avoids ModuleNotFoundError when running tests in environments where pdf2image is not installed.
mock_pdf2image = MagicMock()
sys.modules["pdf2image"] = mock_pdf2image

import pytest
from unittest.mock import patch
from PIL import Image

from langchain_core.documents import Document
from backend.ingestion.ocr import (
    is_scanned_pdf,
    ocr_image,
    ocr_pdf,
    TesseractMissingError,
)
from backend.api.config import settings


@pytest.fixture
def mock_pdf_reader_text():
    """Mock PdfReader representing a digital PDF with text."""
    mock_reader = MagicMock()
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "This is a digital PDF page with plenty of text to ensure it passes the character threshold heuristic check."
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "Another page containing a lot of information, which should easily be recognized as digital rather than scanned."
    mock_reader.pages = [mock_page_1, mock_page_2]
    return mock_reader


@pytest.fixture
def mock_pdf_reader_scanned():
    """Mock PdfReader representing a scanned PDF with minimal text."""
    mock_reader = MagicMock()
    mock_page_1 = MagicMock()
    mock_page_1.extract_text.return_value = "  "
    mock_page_2 = MagicMock()
    mock_page_2.extract_text.return_value = "OCR"
    mock_reader.pages = [mock_page_1, mock_page_2]
    return mock_reader


def test_is_scanned_pdf_digital(mock_pdf_reader_text):
    with patch("backend.ingestion.ocr.PdfReader", return_value=mock_pdf_reader_text):
        assert not is_scanned_pdf("dummy.pdf")


def test_is_scanned_pdf_scanned(mock_pdf_reader_scanned):
    with patch("backend.ingestion.ocr.PdfReader", return_value=mock_pdf_reader_scanned):
        assert is_scanned_pdf("dummy.pdf")


def test_is_scanned_pdf_empty():
    mock_reader = MagicMock()
    mock_reader.pages = []
    with patch("backend.ingestion.ocr.PdfReader", return_value=mock_reader):
        assert is_scanned_pdf("dummy.pdf")


def test_is_scanned_pdf_exception():
    with patch("backend.ingestion.ocr.PdfReader", side_effect=Exception("Read error")):
        assert not is_scanned_pdf("dummy.pdf")


@patch("pytesseract.image_to_string")
def test_ocr_image_success(mock_image_to_string):
    mock_image_to_string.return_value = "Extracted OCR text"
    img = Image.new("RGB", (100, 100))
    result = ocr_image(img)
    assert result == "Extracted OCR text"
    mock_image_to_string.assert_called_once_with(img)


@patch("pytesseract.image_to_string")
def test_ocr_image_tesseract_not_found(mock_image_to_string):
    import pytesseract
    mock_image_to_string.side_effect = pytesseract.TesseractNotFoundError()
    img = Image.new("RGB", (100, 100))
    
    with pytest.raises(TesseractMissingError) as exc_info:
        ocr_image(img)
        
    assert "Tesseract OCR binary not found" in str(exc_info.value)


@patch("pytesseract.image_to_string")
@patch("PIL.Image.open")
def test_ocr_image_filepath(mock_image_open, mock_image_to_string):
    mock_img_obj = MagicMock()
    mock_image_open.return_value = mock_img_obj
    mock_image_to_string.return_value = "File OCR text"

    result = ocr_image("dummy_path.png")
    assert result == "File OCR text"
    mock_image_open.assert_called_once_with("dummy_path.png")
    mock_img_obj.close.assert_called_once()


@patch("pytesseract.image_to_string")
def test_ocr_image_dynamic_config(mock_image_to_string):
    mock_image_to_string.return_value = "Configured OCR text"
    img = Image.new("RGB", (100, 100))
    
    # Temporarily set configuration
    original_cmd = settings.tesseract_cmd
    settings.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    try:
        import pytesseract
        ocr_image(img)
        assert pytesseract.pytesseract.tesseract_cmd == r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    finally:
        settings.tesseract_cmd = original_cmd


@patch("pdf2image.convert_from_path")
@patch("backend.ingestion.ocr.ocr_image")
def test_ocr_pdf_pdf2image_success(mock_ocr_image, mock_convert):
    mock_convert.return_value = [MagicMock(spec=Image.Image), MagicMock(spec=Image.Image)]
    mock_ocr_image.side_effect = ["Page 1 Text", "Page 2 Text"]

    docs = ocr_pdf("dummy.pdf")
    
    assert len(docs) == 2
    assert docs[0].page_content == "Page 1 Text"
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["loader"] == "ocr_pdf2image"
    assert docs[1].page_content == "Page 2 Text"
    assert docs[1].metadata["page"] == 2


@patch("pdf2image.convert_from_path", side_effect=Exception("pdf2image failed"))
@patch("backend.ingestion.ocr.ocr_image")
def test_ocr_pdf_fallback_pypdf_success(mock_ocr_image, mock_convert):
    # Setup mock PdfReader with page images
    mock_reader = MagicMock()
    
    mock_image_file = MagicMock()
    mock_image_file.image = MagicMock(spec=Image.Image)
    
    mock_page = MagicMock()
    mock_page.images = [mock_image_file]
    mock_reader.pages = [mock_page]
    
    mock_ocr_image.return_value = "Fallback OCR extracted text"
    
    with patch("backend.ingestion.ocr.PdfReader", return_value=mock_reader):
        docs = ocr_pdf("dummy.pdf")
        
    assert len(docs) == 1
    assert docs[0].page_content == "Fallback OCR extracted text"
    assert docs[0].metadata["page"] == 1
    assert docs[0].metadata["loader"] == "ocr_pypdf_fallback"
