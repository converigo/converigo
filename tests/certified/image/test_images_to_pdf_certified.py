"""
PROJECT: CONVERIGO
TEST SUITE: Certified Images to PDF Converter (VAR-10 / Batch 3)
STATUS: CERTIFIED (Batch 3 evidence run — pending PC merge-gate approval)

Certified-level coverage for the Images to PDF converter (Pillow, HPND/MIT-CMU).

Pipeline: Pillow -> genuine single multi-image PDF output.
Verification: multi-file upload via /convert (operation=images-to-pdf),
page count, valid PDF output, not-a-copy check, download pipeline,
single-file & invalid input honest-error handling, per-source-format
real-file coverage (png/webp/bmp/tiff/gif) at plugin level.
"""

from __future__ import annotations

import asyncio
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from pypdf import PdfReader

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR


def _make_image(fmt: str, color: tuple) -> BytesIO:
    """Create a small valid real image file in the requested format."""
    buffer = BytesIO()
    img = Image.new("RGB", (64, 48), color)
    img.save(buffer, format=fmt)
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
def test_images_to_pdf_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("png", "pdf", slug="images-to-pdf")
    assert plugin is not None
    assert plugin.slug == "images-to-pdf"
    for source in ("png", "webp", "bmp", "tiff", "gif"):
        assert source in plugin.source_formats, source
    assert plugin.target_formats == ["pdf"]
    assert hasattr(plugin, "merge"), "merge() method missing on ImagesToPDFPlugin"


@pytest.mark.certified
def test_images_to_pdf_registered_for_all_sources() -> None:
    """TEST 002: (png/webp/bmp/tiff/gif -> pdf) all resolve to this plugin."""
    plugin = registry.get_plugin("png", "pdf", slug="images-to-pdf")
    for source in ("png", "webp", "bmp", "tiff", "gif"):
        resolved = registry.get_plugin(source, "pdf")
        assert resolved is plugin, f"{source} -> pdf did not resolve to images-to-pdf"
    # jpg/jpeg must still resolve to the dedicated jpg-to-pdf plugin.
    assert registry.get_plugin("jpg", "pdf").slug == "jpg-to-pdf"


@pytest.mark.certified
def test_images_to_pdf_produces_real_combined_pdf() -> None:
    """TEST 003: Multiple images are genuinely combined into one PDF."""
    client = TestClient(app)
    first = _make_image("PNG", (200, 30, 30))
    second = _make_image("BMP", (30, 200, 30))
    third = _make_image("GIF", (30, 30, 200))

    response = client.post(
        "/convert",
        files=[
            ("file", ("one.png", first, "image/png")),
            ("file", ("two.bmp", second, "image/bmp")),
            ("file", ("three.gif", third, "image/gif")),
        ],
        data={"target_format": "pdf", "operation": "images-to-pdf"},
    )

    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("target_format") == "pdf"
    assert payload.get("download_path"), payload

    output_path = _resolve_public_output_path(response)
    try:
        with open(output_path, "rb") as handle:
            merged_bytes = handle.read()
        assert merged_bytes.startswith(b"%PDF-"), "Not a PDF header"
        first.seek(0)
        assert merged_bytes != first.read(), "Output is a byte copy of the first input"

        reader = PdfReader(str(output_path))
        assert len(reader.pages) == 3, f"Expected 3 pages, got {len(reader.pages)}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_images_to_pdf_download_served() -> None:
    """TEST 004: The combined PDF is downloadable through /download."""
    client = TestClient(app)
    first = _make_image("PNG", (10, 10, 10))
    second = _make_image("WEBP", (240, 240, 10))

    response = client.post(
        "/convert",
        files=[
            ("file", ("one.png", first, "image/png")),
            ("file", ("two.webp", second, "image/webp")),
        ],
        data={"target_format": "pdf", "operation": "images-to-pdf"},
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
def test_images_to_pdf_rejects_single_file() -> None:
    """TEST 005: images-to-pdf operation requires at least 2 files (honest error)."""
    client = TestClient(app)
    single = _make_image("PNG", (1, 2, 3))

    response = client.post(
        "/convert",
        files=[("file", ("one.png", single, "image/png"))],
        data={"target_format": "pdf", "operation": "images-to-pdf"},
    )
    assert response.status_code == 400, response.text
    assert "at least 2" in response.json().get("detail", "").lower()


@pytest.mark.certified
def test_images_to_pdf_rejects_non_image_input() -> None:
    """TEST 006: Invalid image input is rejected honestly (no fake output)."""
    client = TestClient(app)
    garbage = BytesIO(b"this is not a real image")

    response = client.post(
        "/convert",
        files=[
            ("file", ("a.png", garbage, "image/png")),
            ("file", ("b.png", garbage, "image/png")),
        ],
        data={"target_format": "pdf", "operation": "images-to-pdf"},
    )
    assert response.status_code in (400, 415, 422, 500), response.text


@pytest.mark.certified
@pytest.mark.parametrize("fmt", ["PNG", "WEBP", "BMP", "TIFF", "GIF"])
def test_images_to_pdf_real_file_per_source_format(tmp_path: Path, fmt: str) -> None:
    """TEST 007: Real files per source format merge into a valid 2-page PDF."""
    plugin = registry.get_plugin("png", "pdf", slug="images-to-pdf")
    first = tmp_path / f"one.{fmt.lower()}"
    second = tmp_path / f"two.{fmt.lower()}"
    Image.new("RGB", (48, 48), (180, 20, 20)).save(first, format=fmt)
    Image.new("RGB", (48, 48), (20, 180, 20)).save(second, format=fmt)
    assert first.exists() and second.exists()

    output = asyncio.run(
        plugin.merge([first, second], output_dir=tmp_path / "out")
    )
    assert output.exists(), "merge() did not produce output"
    with open(output, "rb") as handle:
        header = handle.read(5)
    assert header == b"%PDF-", f"Not a PDF header: {header!r}"
    reader = PdfReader(str(output))
    assert len(reader.pages) == 2, f"Expected 2 pages for {fmt}, got {len(reader.pages)}"