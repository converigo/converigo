"""
PROJECT: CONVERIGO
TEST SUITE: Certified JPG to PDF Converter (DOC-04 / Batch 5)
STATUS: CERTIFIED (Batch 5 evidence run — pending PC merge-gate approval)

Certified-level coverage for the JPG -> PDF converter
(JPGToPDFPlugin: ReportLab + Pillow, both already in requirements).

Verification: real-file sample (tests/sample.jpg), plugin-level conversion,
HTTP upload -> convert -> download pipeline, valid single-page PDF output
that is NOT a byte copy of the input, honest error for wrong input.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_JPG = Path("tests/sample.jpg")
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


def _make_real_jpg(tmp_path: Path) -> Path:
    jpg = tmp_path / "batch5_sample.jpg"
    Image.new("RGB", (320, 200), (180, 40, 40)).save(jpg, format="JPEG", quality=90)
    assert jpg.exists()
    return jpg


def _convert(client, filename: str = "sample.jpg"):
    assert SAMPLE_JPG.exists(), f"Sample file is missing: {SAMPLE_JPG}"
    with SAMPLE_JPG.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "image/jpeg")},
            data={"target_format": "pdf", "operation": "jpg-to-pdf"},
        )


@pytest.mark.certified
def test_jpg_to_pdf_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("jpg", "pdf", slug="jpg-to-pdf")
    assert plugin is not None
    assert plugin.slug == "jpg-to-pdf"
    assert plugin.engine == "document"
    assert "jpg" in plugin.source_formats
    assert "jpeg" in plugin.source_formats
    assert "pdf" in plugin.target_formats


@pytest.mark.certified
def test_jpg_to_pdf_plugin_produces_real_pdf(tmp_path: Path) -> None:
    """TEST 002: Plugin produces a real single-page PDF from a JPG sample."""
    plugin = registry.get_plugin("jpg", "pdf", slug="jpg-to-pdf")
    src = _make_real_jpg(tmp_path)
    output = asyncio.run(
        plugin.convert(src, "pdf", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.exists(), "Output pdf not created"
    assert output.stat().st_size > 0, "Output pdf is empty"
    assert output.suffix.lower() == ".pdf"
    assert output.read_bytes() != src.read_bytes(), "Output is a byte copy of the input"
    reader = PdfReader(str(output))
    assert len(reader.pages) == 1, f"Expected 1 page, got {len(reader.pages)}"


@pytest.mark.certified
def test_jpg_to_pdf_conversion_success():
    """TEST 003: HTTP conversion succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_jpg_to_pdf_output_is_valid_pdf():
    """TEST 004: Output file is a valid, non-corrupted PDF document."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        reader = PdfReader(str(output_path))
        assert len(reader.pages) == 1
    except Exception as exc:
        raise AssertionError(f"Output PDF is corrupted: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_jpg_to_pdf_download_served():
    """TEST 005: The converted PDF is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert download_resp.content.startswith(b"%PDF-"), "Downloaded file is not a PDF"
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_jpg_to_pdf_single_output_file():
    """TEST 006: Exactly one PDF output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = list((OUTPUT_DIR / conversion_id).glob("*.pdf"))
    assert len(files) == 1, f"Expected exactly one PDF output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_jpg_to_pdf_rejects_non_image_input():
    """TEST 007: Non-image input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "pdf", "operation": "jpg-to-pdf"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body

