"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF Merge Converter (DOC-27 / Sub-batch B)
STATUS: DEVELOPMENT (certification pending evidence review)

Certified-level coverage for the PDF Merge converter (pypdf, BSD-3-Clause).

Pipeline: pypdf -> genuinely merged PDF output.
Verification: multi-file upload via /convert, page count, page ordering,
valid PDF output, download pipeline, invalid input handling.
"""

from __future__ import annotations

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
    """Create a small valid multi-page PDF whose pages are labelled."""
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
def test_pdf_merge_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-merge")
    assert plugin is not None
    assert plugin.slug == "pdf-merge"
    assert "pdf" in plugin.source_formats
    assert "pdf" in plugin.target_formats
    assert hasattr(plugin, "merge"), "merge() method missing on PDFMergePlugin"


@pytest.mark.certified
def test_pdf_merge_produces_real_merged_pdf() -> None:
    """TEST 002: Multiple PDFs are genuinely merged with correct page count."""
    client = TestClient(app)
    first = _make_pdf("alpha", 2)
    second = _make_pdf("beta", 3)

    response = client.post(
        "/convert",
        files=[
            ("file", ("alpha.pdf", first, "application/pdf")),
            ("file", ("beta.pdf", second, "application/pdf")),
        ],
        data={"target_format": "pdf", "operation": "pdf-merge"},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload

    output_path = _resolve_public_output_path(response)
    try:
        reader = PdfReader(str(output_path))
        # 2 pages + 3 pages == 5 pages
        assert len(reader.pages) == 5, f"Expected 5 merged pages, got {len(reader.pages)}"
        # Output must not be a byte-for-byte copy of either input.
        with open(output_path, "rb") as handle:
            merged_bytes = handle.read()
        first.seek(0)
        second.seek(0)
        assert merged_bytes != first.read(), "Merged output is a copy of first input"
        assert merged_bytes != second.read(), "Merged output is a copy of second input"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_merge_preserves_page_order() -> None:
    """TEST 003: Page ordering follows the upload order."""
    client = TestClient(app)
    first = _make_pdf("alpha", 2)
    second = _make_pdf("beta", 1)

    response = client.post(
        "/convert",
        files=[
            ("file", ("alpha.pdf", first, "application/pdf")),
            ("file", ("beta.pdf", second, "application/pdf")),
        ],
        data={"target_format": "pdf", "operation": "pdf-merge"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        reader = PdfReader(str(output_path))
        assert len(reader.pages) == 3, f"Expected 3 merged pages, got {len(reader.pages)}"
        page_texts = [page.extract_text() or "" for page in reader.pages]
        assert any("alpha-page-1" in text for text in page_texts), page_texts
        assert any("alpha-page-2" in text for text in page_texts), page_texts
        assert any("beta-page-1" in text for text in page_texts), page_texts
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_merge_output_is_valid_pdf() -> None:
    """TEST 004: Output file is a real, parseable PDF."""
    client = TestClient(app)
    first = _make_pdf("alpha", 1)
    second = _make_pdf("beta", 1)

    response = client.post(
        "/convert",
        files=[
            ("file", ("alpha.pdf", first, "application/pdf")),
            ("file", ("beta.pdf", second, "application/pdf")),
        ],
        data={"target_format": "pdf", "operation": "pdf-merge"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        with open(output_path, "rb") as handle:
            header = handle.read(5)
        assert header == b"%PDF-", f"Not a PDF header: {header!r}"
        reader = PdfReader(str(output_path))
        assert reader.pages, "Merged PDF has no pages"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_merge_download_served() -> None:
    """TEST 005: The merged PDF is downloadable through /download."""
    client = TestClient(app)
    first = _make_pdf("alpha", 1)
    second = _make_pdf("beta", 1)

    response = client.post(
        "/convert",
        files=[
            ("file", ("alpha.pdf", first, "application/pdf")),
            ("file", ("beta.pdf", second, "application/pdf")),
        ],
        data={"target_format": "pdf", "operation": "pdf-merge"},
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
def test_pdf_merge_rejects_single_file() -> None:
    """TEST 006: pdf-merge requires at least two input files (honest error)."""
    client = TestClient(app)
    single = _make_pdf("alpha", 1)

    response = client.post(
        "/convert",
        files=[("file", ("alpha.pdf", single, "application/pdf"))],
        data={"target_format": "pdf", "operation": "pdf-merge"},
    )
    assert response.status_code == 400, response.text
    assert "at least 2" in response.json().get("detail", "").lower()


@pytest.mark.certified
def test_pdf_merge_rejects_non_pdf_input() -> None:
    """TEST 007: Invalid PDF input is rejected honestly (no fake output)."""
    client = TestClient(app)
    fake_pdf = BytesIO(b"this is not a real pdf")

    response = client.post(
        "/convert",
        files=[
            ("file", ("a.pdf", fake_pdf, "application/pdf")),
            ("file", ("b.pdf", fake_pdf, "application/pdf")),
        ],
        data={"target_format": "pdf", "operation": "pdf-merge"},
    )
    assert response.status_code in (400, 422, 500), response.text

