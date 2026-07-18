"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to ODT Converter
STATUS: TESTING (Candidate for next certification)

Basic test coverage for PDF→ODT converter.
Candidate for certification after stability verification.
"""

from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from odf.opendocument import load

from app.main import app
from app.plugins.registry import registry


def create_simple_pdf() -> BytesIO:
    """Create a simple valid PDF."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, "PDF to ODT test")
    pdf_canvas.save()
    buffer.seek(0)
    return buffer


def test_pdf_to_odt_plugin_discovered():
    """TEST 001: Plugin is properly registered."""
    plugin = registry.get_plugin("pdf", "odt")
    assert plugin is not None
    assert plugin.slug == "pdf-to-odt"
    assert "odt" in plugin.target_formats


def test_pdf_to_odt_conversion_success():
    """TEST 002: PDF converts to ODT successfully."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "odt"},
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "success"


def test_pdf_to_odt_output_exists():
    """TEST 003: Output ODT file is created."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "odt"},
    )
    
    filename = response.json()["filename"]
    output_path = Path("outputs/document") / filename
    assert output_path.exists()
    
    output_path.unlink(missing_ok=True)


def test_pdf_to_odt_extension_correct():
    """TEST 004: Output file has correct ODT extension."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "odt"},
    )
    
    filename = response.json()["filename"]
    assert filename.endswith(".odt")
    
    output_path = Path("outputs/document") / filename
    assert output_path.suffix == ".odt"
    output_path.unlink(missing_ok=True)


def test_pdf_to_odt_not_corrupted():
    """TEST 005: Output ODT file is valid and not corrupted."""
    client = TestClient(app)
    simple_pdf = create_simple_pdf()
    
    response = client.post(
        "/convert",
        files={"file": ("test.pdf", simple_pdf, "application/pdf")},
        data={"target_format": "odt"},
    )
    
    filename = response.json()["filename"]
    output_path = Path("outputs/document") / filename
    
    # File must be readable as valid ODT
    try:
        doc = load(str(output_path))
        assert doc is not None
    except Exception as e:
        raise AssertionError(f"Output ODT is corrupted: {e}")
    finally:
        output_path.unlink(missing_ok=True)
