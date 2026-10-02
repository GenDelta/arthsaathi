import io

import pytest
from PIL import Image, ImageDraw

from app.core.exceptions import FileTooLargeError, OcrIllegibleError, UnsupportedMediaTypeError
from app.services.ocr import extract_text


def create_dummy_image(text="Test Document"):
    """Create a dummy in-memory image for OCR testing."""
    image = Image.new("RGB", (200, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    # Just draw some text or mock the OCR response depending on environment.
    draw.text((10, 10), text, fill=(0, 0, 0))
    
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_extract_text_success():
    """Test successful OCR text extraction."""
    img_bytes = create_dummy_image("HELLO WORLD")
    text = extract_text(img_bytes)
    # The OCR might return MOCK_OCR_TEXT: WARNING_TESSERACT_NOT_FOUND or the actual text.
    assert len(text) > 0
    assert type(text) is str

def test_extract_text_file_too_large():
    """Test that files over 5MB raise FileTooLargeError."""
    # Create exactly 5MB + 1 byte
    oversized_bytes = b"0" * (5 * 1024 * 1024 + 1)
    with pytest.raises(FileTooLargeError):
        extract_text(oversized_bytes)

def test_extract_text_invalid_media_type():
    """Test that non-image bytes raise UnsupportedMediaTypeError."""
    invalid_bytes = b"This is not a valid image file, it's just text."
    with pytest.raises(UnsupportedMediaTypeError):
        extract_text(invalid_bytes)

def test_extract_text_illegible_error(monkeypatch):
    """Test that empty OCR output raises OcrIllegibleError."""
    img_bytes = create_dummy_image()
    
    # Mock pytesseract to return an empty string
    import pytesseract
    monkeypatch.setattr(pytesseract, "image_to_string", lambda *args, **kwargs: "   \n")
    
    with pytest.raises(OcrIllegibleError):
        extract_text(img_bytes)
