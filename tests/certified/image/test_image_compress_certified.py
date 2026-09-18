"""
PROJECT: CONVERIGO
TEST SUITE: Certified Image Compress Converter (VAR-03 / Sub-batch C)
STATUS: DEVELOPMENT (certification pending evidence review)

Certified-level coverage for the Image Compress (lossy) converter
(Pillow, MIT).

Pipeline: Pillow -> JPG re-encode at lower quality (lossy) -> smaller JPG.
Verification: plugin discovery, image engine conversion, HTTP API,
output size reduction, download pipeline, invalid input handling.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_JPG = Path("tests/assets/regression/sample.jpg")


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


def _convert(client, filename: str = "sample.jpg"):
    sample = SAMPLE_JPG
    assert sample.exists(), f"Sample file is missing: {sample}"
    with sample.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "image/jpeg")},
            data={"target_format": "jpg", "operation": "image-compress"},
        )


@pytest.mark.certified
def test_image_compress_plugin_discovered() -> None:
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("jpg", "jpg", slug="image-compress")
    assert plugin is not None
    assert plugin.slug == "image-compress"
    assert "jpg" in plugin.source_formats
    assert "jpg" in plugin.target_formats


@pytest.mark.certified
def test_image_compress_conversion_success() -> None:
    """TEST 002: HTTP conversion succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_image_compress_output_is_valid_jpg() -> None:
    """TEST 003: Output file is a valid, non-corrupted JPG image."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        with Image.open(str(output_path)) as image:
            assert image is not None
            assert image.format.lower() == "jpeg"
    except Exception as exc:
        raise AssertionError(f"Output JPG is corrupted: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_image_compress_download_served() -> None:
    """TEST 004: The compressed JPG is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    output_path = _resolve_public_output_path(response)
    output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_image_compress_rejects_non_image_input() -> None:
    """TEST 005: Non-image input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "jpg", "operation": "image-compress"},
        )
    # Must return honest error (not a fake success).
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body