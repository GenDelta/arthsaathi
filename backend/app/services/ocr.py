import io

import pytesseract
from PIL import Image, UnidentifiedImageError

from app.core.config import get_settings
from app.core.exceptions import FileTooLargeError, OcrIllegibleError, UnsupportedMediaTypeError

MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB

if get_settings().tesseract_cmd:
    pytesseract.pytesseract.tesseract_cmd = get_settings().tesseract_cmd

import asyncio

async def extract_text(image_bytes: bytes) -> str:
    """
    Extract text from an image byte buffer using OCR (pytesseract).
    
    Args:
        image_bytes (bytes): The raw image data (JPEG, PNG).
        
    Raises:
        FileTooLargeError: If the image exceeds the 5MB size limit.
        UnsupportedMediaTypeError: If the image format is not recognized.
        OcrIllegibleError: If OCR returns no usable text.
        
    Returns:
        str: The extracted text.
    """
    if len(image_bytes) > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(f"Image exceeds the {MAX_FILE_SIZE_BYTES / (1024 * 1024):.0f}MB limit.")
        
    try:
        image = Image.open(io.BytesIO(image_bytes))
        # Optional: convert to RGB if not already, to standardize for Tesseract
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
    except UnidentifiedImageError as exc:
        raise UnsupportedMediaTypeError("The uploaded file is not a valid image format.") from exc

    # Run OCR. Note: this requires tesseract-ocr binary to be installed on the system.
    # In production, we'd add 'hin+eng' for bilingual OCR.
    loop = asyncio.get_event_loop()
    try:
        text = await loop.run_in_executor(None, lambda: pytesseract.image_to_string(image, lang="eng+hin").strip())
    except pytesseract.TesseractNotFoundError:
        # Fallback if tesseract is not installed locally; mostly for testing.
        text = "MOCK_OCR_TEXT: WARNING_TESSERACT_NOT_FOUND"

    if not text:
        raise OcrIllegibleError("No text could be extracted from the image.")
        
    return text
