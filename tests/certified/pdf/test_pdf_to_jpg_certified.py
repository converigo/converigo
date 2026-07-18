"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to JPG Converter
STATUS: DEVELOPMENT (Not yet certified)

Basic test coverage for PDF→JPG converter.
Ready for stability testing before certification.
"""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from app.core.settings import settings
from reportlab.pdfgen import canvas
from PIL import Image

from app.main import app
from app.plugins.registry import registry


def create_simple_pdf() -> BytesIO:
    """Create a simple valid PDF."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, "PDF to JPG test")
    pdf_canvas.save()
    buffer.seek(0)
    return buffer


def test_pdf_to_jpg_plugin_discovered():
    """TEST 001: Plugin is properly registered."""
    plugin = registry.get_plugin("pdf", "jpg")
    assert plugin is not None
    assert plugin.slug == "pdf-to-jpg"
    assert "jpg" in plugin.target_formats or "jpeg" in plugin.target_formats


def test_pdf_to_jpg_conversion_success():
    """TEST 002: PDF converts to JPG successfully."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "jpg"},
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_pdf_to_jpg_output_exists():
    """TEST 003: Output JPG file is created."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "jpg"},
    )
    
    filename = response.json()["filename"]
    output_path = settings.OUTPUT_DIR / "document" / filename
    assert output_path.exists()
    
    output_path.unlink(missing_ok=True)


def test_pdf_to_jpg_extension_correct():
    """TEST 004: Output file has correct JPG extension."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "jpg"},
    )
    
    filename = response.json()["filename"]
    assert filename.endswith((".jpg", ".jpeg"))
    
    output_path = settings.OUTPUT_DIR / "document" / filename
    assert output_path.suffix.lower() in {".jpg", ".jpeg"}
    output_path.unlink(missing_ok=True)


def test_pdf_to_jpg_not_corrupted():
    """TEST 005: Output JPG file is valid and not corrupted."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "jpg"},
    )
    
    filename = response.json()["filename"]
    output_path = settings.OUTPUT_DIR / "document" / filename
    
    # File must be readable as valid image
    try:
        with Image.open(str(output_path)) as image:
            assert image is not None
            assert image.format.lower() == "jpeg"
    except Exception as e:
        raise AssertionError(f"Output JPG is corrupted: {e}")
    finally:
        output_path.unlink(missing_ok=True)
