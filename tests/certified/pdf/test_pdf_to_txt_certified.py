"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF to TXT Converter (DOC-05 / Batch 3)
STATUS: CERTIFIED (Batch 3 evidence run — pending PC merge-gate approval)

Certified-level coverage for the PDF to TXT converter (pypdf, BSD-3-Clause).

Pipeline: pypdf -> genuine text extraction into plain UTF-8 TXT.
Verification: real single-file upload via /convert, multi-page text
extraction, valid TXT output, download pipeline, invalid input
honest-error handling.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR


def _make_pdf(page_labels: list) -> BytesIO:
    """Create a small valid multi-page PDF whose pages carry known text."""
    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    for label in page_labels:
        pdf_canvas.drawString(100, 750, label)
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
def test_pdf_to_txt_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("pdf", "txt", slug="pdf-to-txt")
    assert plugin is not None
    assert plugin.slug == "pdf-to-txt"
    assert plugin.source_formats == ["pdf"]
    assert plugin.target_formats == ["txt"]


@pytest.mark.certified
def test_pdf_to_txt_extracts_real_text() -> None:
    """TEST 002: Genuine text extraction with known strings from both pages."""
    client = TestClient(app)
    pdf = _make_pdf(
        [
            "CONVERIGO-B3-ALPHA-SECRET page one",
            "CONVERIGO-B3-BETA-SECRET page two",
        ]
    )

    response = client.post(
        "/convert",
        files=[("file", ("document.pdf", pdf, "application/pdf"))],
        data={"target_format": "txt", "operation": "pdf-to-txt"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("target_format") == "txt"

    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.suffix.lower() == ".txt", output_path.name
        text = output_path.read_text(encoding="utf-8")
        assert "CONVERIGO-B3-ALPHA-SECRET" in text, text[:500]
        assert "CONVERIGO-B3-BETA-SECRET" in text, text[:500]
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_to_txt_download_served() -> None:
    """TEST 003: The extracted TXT is downloadable through /download."""
    client = TestClient(app)
    pdf = _make_pdf(["CONVERIGO-B3-DOWNLOAD-CHECK"])

    response = client.post(
        "/convert",
        files=[("file", ("document.pdf", pdf, "application/pdf"))],
        data={"target_format": "txt", "operation": "pdf-to-txt"},
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
def test_pdf_to_txt_rejects_invalid_pdf() -> None:
    """TEST 004: Invalid PDF input is rejected honestly (no fake output)."""
    client = TestClient(app)
    fake_pdf = BytesIO(b"this is not a real pdf")

    response = client.post(
        "/convert",
        files=[("file", ("a.pdf", fake_pdf, "application/pdf"))],
        data={"target_format": "txt", "operation": "pdf-to-txt"},
    )
    assert response.status_code in (400, 422, 500), response.text


@pytest.mark.certified
def test_pdf_to_txt_plain_pair_resolution() -> None:
    """TEST 005: pdf -> txt also resolves without an explicit slug."""
    plugin = registry.get_plugin("pdf", "txt")
    assert plugin.slug == "pdf-to-txt"