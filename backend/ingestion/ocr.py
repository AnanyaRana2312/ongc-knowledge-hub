"""
backend/ingestion/ocr.py
-------------------------
OCR (Optical Character Recognition) utilities for image and scanned PDF ingestion.
"""

import logging
from pathlib import Path
from typing import List, Union

from langchain_core.documents import Document
from PIL import Image
from pypdf import PdfReader

from backend.api.config import settings

logger = logging.getLogger(__name__)


class TesseractMissingError(RuntimeError):
    """Raised when the Tesseract OCR binary is missing or not configured."""
    pass


def _configure_tesseract() -> None:
    """Configures the pytesseract cmd path if set in settings."""
    try:
        import pytesseract
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
    except ImportError:
        raise ImportError(
            "The 'pytesseract' package is not installed. "
            "Please install it using 'pip install pytesseract Pillow'."
        )


def is_scanned_pdf(file_path: str, min_chars_per_page: int = 50) -> bool:
    """
    Check if a PDF file is scanned (i.e. contains mostly images and very little selectable text).

    Args:
        file_path: Path to the PDF file.
        min_chars_per_page: Minimum character count per page threshold.

    Returns:
        True if the PDF is scanned / has minimal text, False otherwise.
    """
    path = Path(file_path)
    try:
        reader = PdfReader(str(path))
        num_pages = len(reader.pages)
        if num_pages == 0:
            return True  # Empty PDF is treated as scanned/empty

        total_chars = 0
        pages_to_check = min(5, num_pages)
        for i in range(pages_to_check):
            page = reader.pages[i]
            text = page.extract_text() or ""
            total_chars += len(text.strip())

        avg_chars = total_chars / pages_to_check
        logger.info(
            f"PDF {path.name}: total_chars={total_chars} (first {pages_to_check} pages), "
            f"avg_chars_per_page={avg_chars:.1f} (threshold={min_chars_per_page})"
        )
        return avg_chars < min_chars_per_page
    except Exception as e:
        logger.warning(f"Error checking if PDF is scanned: {e}")
        return False


def ocr_image(image: Union[str, Path, Image.Image]) -> str:
    """
    Perform OCR on a single image file or Pillow Image object.

    Args:
        image: A file path (str/Path) or a PIL Image object.

    Returns:
        The extracted text as a string.

    Raises:
        TesseractMissingError: If Tesseract executable is not found.
    """
    _configure_tesseract()
    import pytesseract

    img = None
    should_close = False

    try:
        if isinstance(image, (str, Path)):
            img = Image.open(str(image))
            should_close = True
        else:
            img = image

        # Run pytesseract OCR
        try:
            text = pytesseract.image_to_string(img)
            return text.strip()
        except pytesseract.TesseractNotFoundError as e:
            msg = (
                "Tesseract OCR binary not found. Please install Tesseract on your system "
                "(Windows: https://github.com/UB-Mannheim/tesseract/wiki) and add it to your system PATH, "
                "or set TESSERACT_CMD in your .env file."
            )
            logger.error(msg)
            raise TesseractMissingError(msg) from e
        except Exception as e:
            logger.error(f"Error executing OCR via pytesseract: {e}")
            raise RuntimeError(f"OCR execution failed: {e}") from e
    finally:
        if should_close and img:
            img.close()


def ocr_pdf(file_path: str) -> List[Document]:
    """
    Perform OCR on a scanned PDF file by converting pages to images or extracting page images,
    running OCR, and returning them as LangChain Documents.

    Args:
        file_path: Path to the scanned PDF file.

    Returns:
        List of LangChain Document objects, one per page.
    """
    path = Path(file_path)
    docs: List[Document] = []

    # Check if pdf2image is available
    has_pdf2image = False
    try:
        import pdf2image
        has_pdf2image = True
    except ImportError:
        logger.info("pdf2image is not installed. Falling back to pypdf image extraction.")

    if has_pdf2image:
        try:
            # We try to convert pdf pages to images
            images = pdf2image.convert_from_path(str(path))
            for i, img in enumerate(images):
                logger.info(f"OCRing page {i+1}/{len(images)} of PDF '{path.name}' via pdf2image...")
                text = ocr_image(img)
                if text:
                    docs.append(
                        Document(
                            page_content=text,
                            metadata={
                                "source": path.name,
                                "type": "pdf",
                                "page": i + 1,
                                "loader": "ocr_pdf2image",
                            },
                        )
                    )
            return docs
        except Exception as e:
            logger.warning(
                f"pdf2image conversion failed: {e}. Falling back to pypdf image extraction."
            )

    # Fallback: Extract embedded images via pypdf
    try:
        reader = PdfReader(str(path))
        for i, page in enumerate(reader.pages):
            page_text_parts = []
            images_on_page = page.images
            if images_on_page:
                logger.info(
                    f"Extracting and OCRing {len(images_on_page)} image(s) on page {i+1} of '{path.name}'..."
                )
                for img_file in images_on_page:
                    try:
                        img = img_file.image
                        text = ocr_image(img)
                        if text:
                            page_text_parts.append(text)
                    except Exception as img_err:
                        logger.warning(
                            f"Failed to OCR embedded image on page {i+1} of '{path.name}': {img_err}"
                        )

            # Combine all OCR'd text parts from the page
            page_text = "\n\n".join(page_text_parts).strip()
            if page_text:
                docs.append(
                    Document(
                        page_content=page_text,
                        metadata={
                            "source": path.name,
                            "type": "pdf",
                            "page": i + 1,
                            "loader": "ocr_pypdf_fallback",
                        },
                    )
                )

        if not docs:
            logger.warning(f"No text extracted via OCR fallback from scanned PDF '{path.name}'")

        return docs
    except Exception as e:
        logger.error(f"Fallback pypdf OCR failed for '{path.name}': {e}")
        raise RuntimeError(f"Failed to perform OCR on PDF '{path.name}': {e}") from e
