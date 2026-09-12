"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to PNG Converter (Batch 2)
STATUS: CERTIFIED (Batch 2 evidence run — pending PC merge-gate approval)

Certified-level coverage for the PDF -> PNG converter
(PDFToPNGPlugin: PyMuPDF/fitz page render, already in requirements).

Verification: real-file sample (tests/sample.pdf), plugin-level conversion,
HTTP upload -> convert -> download pipeline, valid PNG output that is NOT
a byte copy of the input, honest error for wrong input.
"""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from reportlab.pdfgen import canvas

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_PDF = Path("tests/sample.pdf")
OUTPUT_DIR = settings.OUTPUT_DIR


def _resolve_public_output_path(response) -> Path:
    payload = response.json()
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    output_path = OUTPUT_DIR / conversion_id / filename
    assert output_path.exists(), f"Expected output file not found: {output_path}"
    return output_path


def _make_real_pdf(tmp_path: Path) -> Path:
    pdf = tmp_path / "batch2_sample.pdf"
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, "PDF to PNG Batch 2 sample")
    pdf_canvas.save()
    pdf.write_bytes(buffer.getvalue())
    assert pdf.exists()
    return pdf


def _convert(client, filename: str = "sample.pdf"):
    assert SAMPLE_PDF.exists(), f"Sample file is missing: {SAMPLE_PDF}"
    with SAMPLE_PDF.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "application/pdf")},
            data={"target_format": "png", "operation": "pdf-to-png"},
        )


@pytest.mark.certified
def test_pdf_to_png_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("pdf", "png", slug="pdf-to-png")
    assert plugin is not None
    assert plugin.slug == "pdf-to-png"
    assert plugin.engine == "document"
    assert "pdf" in plugin.source_formats
    assert "png" in plugin.target_formats


@pytest.mark.certified
def test_pdf_to_png_plugin_produces_real_png(tmp_path: Path) -> None:
    """TEST 002: Plugin produces a real PNG image from a PDF sample."""
    plugin = registry.get_plugin("pdf", "png", slug="pdf-to-png")
    src = _make_real_pdf(tmp_path)
    output = asyncio.run(
        plugin.convert(src, "png", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.exists(), "Output png not created"
    assert output.stat().st_size > 0, "Output png is empty"
    assert output.suffix.lower() == ".png"
    assert output.read_bytes() != src.read_bytes(), "Output is a byte copy of the input"
    with Image.open(str(output)) as image:
        assert image.format == "PNG"


@pytest.mark.certified
def test_pdf_to_png_conversion_success():
    """TEST 003: HTTP conversion succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_pdf_to_png_output_is_valid_png():
    """TEST 004: Output file is a valid, non-corrupted PNG image."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        with Image.open(str(output_path)) as image:
            assert image.format == "PNG"
            image.verify()
    except Exception as exc:
        raise AssertionError(f"Output PNG is corrupted: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_to_png_download_served():
    """TEST 005: The converted PNG is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert download_resp.content.startswith(b"\x89PNG"), "Downloaded file is not a PNG"
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_to_png_single_output_file():
    """TEST 006: Exactly one PNG output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = list((OUTPUT_DIR / conversion_id).glob("*.png"))
    assert len(files) == 1, f"Expected exactly one PNG output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_to_png_rejects_non_pdf_input():
    """TEST 007: Non-PDF input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "png", "operation": "pdf-to-png"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body
