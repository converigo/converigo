"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF Split Converter (DOC-28 / Sub-batch B)
STATUS: DEVELOPMENT (certification pending evidence review)

Certified-level coverage for the PDF Split converter (pypdf, BSD-3-Clause).

Pipeline: pypdf -> genuine per-page split -> ZIP archive of page PDFs.
Verification: plugin discovery, single-file API conversion, ZIP contents,
page count, valid PDFs inside ZIP, download pipeline, invalid input handling.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader
from reportlab.pdfgen import canvas

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR


def _make_pdf(label: str, pages: int) -> BytesIO:
    """Create a small valid multi-page PDF."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    for page_num in range(1, pages + 1):
        pdf_canvas.drawString(100, 750, f"{label}-page-{page_num}")
        pdf_canvas.showPage()
    pdf_canvas.save()
    buffer.seek(0)
    return buffer


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


@pytest.mark.certified
def test_pdf_split_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-split")
    assert plugin is not None
    assert plugin.slug == "pdf-split"
    assert "pdf" in plugin.source_formats
    assert "pdf" in plugin.target_formats


@pytest.mark.certified
def test_pdf_split_converts_via_api() -> None:
    """TEST 002: HTTP split succeeds and returns a download path."""
    client = TestClient(app)
    pdf = _make_pdf("split-me", 3)

    response = client.post(
        "/convert",
        files={"file": ("input.pdf", pdf, "application/pdf")},
        data={"target_format": "pdf", "operation": "pdf-split"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_pdf_split_produces_zip_with_correct_page_count() -> None:
    """TEST 003: Split produces a ZIP containing one PDF per page."""
    client = TestClient(app)
    pdf = _make_pdf("split-me", 3)

    response = client.post(
        "/convert",
        files={"file": ("input.pdf", pdf, "application/pdf")},
        data={"target_format": "pdf", "operation": "pdf-split"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.suffix.lower() == ".zip", f"Expected .zip, got {output_path.suffix}"
        with zipfile.ZipFile(str(output_path), "r") as archive:
            names = archive.namelist()
            pdf_names = [n for n in names if n.lower().endswith(".pdf")]
            assert len(pdf_names) == 3, f"Expected 3 page PDFs, got {len(pdf_names)}: {pdf_names}"
            # Verify each inner PDF is valid
            for name in pdf_names:
                pdf_bytes = archive.read(name)
                assert pdf_bytes.startswith(b"%PDF-"), f"Inner file {name} is not a PDF: {pdf_bytes[:5]!r}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_split_output_is_zip() -> None:
    """TEST 004: Output file is a valid ZIP archive."""
    client = TestClient(app)
    pdf = _make_pdf("split-me", 2)

    response = client.post(
        "/convert",
        files={"file": ("input.pdf", pdf, "application/pdf")},
        data={"target_format": "pdf", "operation": "pdf-split"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.suffix.lower() == ".zip"
        assert zipfile.is_zipfile(str(output_path)), "Output is not a valid ZIP"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_split_download_served() -> None:
    """TEST 005: The split ZIP is downloadable through /download."""
    client = TestClient(app)
    pdf = _make_pdf("split-me", 1)

    response = client.post(
        "/convert",
        files={"file": ("input.pdf", pdf, "application/pdf")},
        data={"target_format": "pdf", "operation": "pdf-split"},
    )
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    output_path = _resolve_public_output_path(response)
    output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_split_rejects_empty_pdf() -> None:
    """TEST 006: PDF with no pages is rejected with an honest error."""
    client = TestClient(app)
    empty = _make_pdf("empty", 0)

    response = client.post(
        "/convert",
        files={"file": ("empty.pdf", empty, "application/pdf")},
        data={"target_format": "pdf", "operation": "pdf-split"},
    )
    assert response.status_code in (422, 500), response.text