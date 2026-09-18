"""
PROJECT: CONVERIGO
TEST SUITE: Certified Batch JPG to WEBP Converter (VAR-02 / Sub-batch C)
STATUS: DEVELOPMENT (certification pending evidence review)

Certified-level coverage for the Batch JPG to WEBP converter
(Pillow, MIT).

Pipeline: Multi-JPG upload -> Pillow WEBP conversion -> ZIP of WEBP files.
Verification: plugin discovery, single-file conversion, batch ZIP output,
valid WEBP inside ZIP, download pipeline, invalid input handling.
"""

from __future__ import annotations

import zipfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR


def _make_jpg(size: tuple[int, int] = (100, 100)) -> BytesIO:
    """Create a small valid JPG image in memory."""
    buffer = BytesIO()
    img = Image.new("RGB", size, color=(255, 0, 0))
    img.save(buffer, "JPEG")
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
def test_batch_jpg_to_webp_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("jpg", "webp", slug="batch-jpg-to-webp")
    assert plugin is not None
    assert plugin.slug == "batch-jpg-to-webp"
    assert "jpg" in plugin.source_formats
    assert "webp" in plugin.target_formats
    assert hasattr(plugin, "merge"), "merge() method missing on BatchJPGToWEBPPlugin"


@pytest.mark.certified
def test_batch_jpg_to_webp_single_file_via_api() -> None:
    """TEST 002: Single-file conversion succeeds and returns a WEBP download."""
    client = TestClient(app)
    img = _make_jpg()

    response = client.post(
        "/convert",
        files={"file": ("photo.jpg", img, "image/jpeg")},
        data={"target_format": "webp", "operation": "batch-jpg-to-webp"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_batch_jpg_to_webp_batch_produces_zip() -> None:
    """TEST 004: Multiple JPGs produce a ZIP with WEBP files."""
    client = TestClient(app)
    first = _make_jpg()
    second = _make_jpg()

    response = client.post(
        "/convert",
        files=[
            ("file", ("first.jpg", first, "image/jpeg")),
            ("file", ("second.jpg", second, "image/jpeg")),
        ],
        data={"target_format": "webp", "operation": "batch-jpg-to-webp"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        assert output_path.suffix.lower() == ".zip", f"Expected .zip, got {output_path.suffix}"
        assert zipfile.is_zipfile(str(output_path)), "Output is not a valid ZIP"
        with zipfile.ZipFile(str(output_path), "r") as archive:
            names = archive.namelist()
            webp_names = [n for n in names if n.lower().endswith(".webp")]
            assert len(webp_names) == 2, f"Expected 2 WEBPs, got {len(webp_names)}: {names}"
            # Verify each inner file is a valid WEBP
            for name in webp_names:
                img_bytes = archive.read(name)
                assert img_bytes.startswith(b"RIFF"), f"Inner file {name} is not a WEBP: {img_bytes[:4]!r}"
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_batch_jpg_to_webp_download_served() -> None:
    """TEST 005: The output (single or ZIP) is downloadable through /download."""
    client = TestClient(app)
    img = _make_jpg()

    response = client.post(
        "/convert",
        files={"file": ("photo.jpg", img, "image/jpeg")},
        data={"target_format": "webp", "operation": "batch-jpg-to-webp"},
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
def test_batch_jpg_to_webp_rejects_non_image_input() -> None:
    """TEST 006: Non-image input is rejected (honest error)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "webp", "operation": "batch-jpg-to-webp"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body


@pytest.mark.certified
def test_batch_jpg_to_webp_single_output_is_valid_webp() -> None:
    """TEST 003: Single-file output is a valid WEBP image."""
    client = TestClient(app)
    img = _make_jpg()

    response = client.post(
        "/convert",
        files={"file": ("photo.jpg", img, "image/jpeg")},
        data={"target_format": "webp", "operation": "batch-jpg-to-webp"},
    )
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        with Image.open(str(output_path)) as image:
            assert image.format.lower() == "webp"
    finally:
        output_path.unlink(missing_ok=True)
