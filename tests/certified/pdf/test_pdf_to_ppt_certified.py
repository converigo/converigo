"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to PPT Converter
STATUS: DEVELOPMENT (Not yet certified)

Basic test coverage for PDF→PPTX converter.
Ready for stability testing before certification.
"""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from app.core.settings import settings
from reportlab.pdfgen import canvas
from pptx import Presentation

from app.main import app
from app.plugins.registry import registry


def _resolve_public_output_path(response) -> Path:
    payload = response.json()
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    output_path = settings.OUTPUT_DIR / conversion_id / filename
    assert output_path.exists(), f"Expected output file not found: {output_path}"
    return output_path


def create_simple_pdf() -> BytesIO:
    """Create a simple valid PDF."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, "PDF to PPTX test")
    pdf_canvas.save()
    buffer.seek(0)
    return buffer


def test_pdf_to_ppt_plugin_discovered():
    """TEST 001: Plugin is properly registered."""
    plugin = registry.get_plugin("pdf", "pptx")
    assert plugin is not None
    assert plugin.slug == "pdf-to-ppt"
    assert "pptx" in plugin.target_formats


def test_pdf_to_ppt_conversion_success():
    """TEST 002: PDF converts to PPTX successfully."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "pptx"},
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_pdf_to_ppt_output_exists():
    """TEST 003: Output PPTX file is created."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "pptx"},
    )
    
    output_path = _resolve_public_output_path(response)
    assert output_path.exists()
    
    output_path.unlink(missing_ok=True)


def test_pdf_to_ppt_extension_correct():
    """TEST 004: Output file has correct PPTX extension."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "pptx"},
    )
    
    filename = response.json()["filename"]
    assert filename.endswith(".pptx")
    
    output_path = _resolve_public_output_path(response)
    assert output_path.suffix == ".pptx"
    output_path.unlink(missing_ok=True)


def test_pdf_to_ppt_not_corrupted():
    """TEST 005: Output PPTX file is valid and not corrupted."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "pptx"},
    )
    
    output_path = _resolve_public_output_path(response)
    
    # File must be readable as valid PPTX
    try:
        presentation = Presentation(str(output_path))
        assert presentation is not None
        assert len(presentation.slides) > 0
    except Exception as e:
        raise AssertionError(f"Output PPTX is corrupted: {e}")
    finally:
        output_path.unlink(missing_ok=True)
