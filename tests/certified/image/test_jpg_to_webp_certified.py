"""
PROJECT: CONVERIGO
TEST SUITE: Certified JPG to WEBP Converter (Sub-batch A / IMG-16)
STATUS: DEVELOPMENT (certification pending evidence review)

Certified-level coverage for the JPG -> WEBP converter (Pillow/ImageEngine, MIT).

Pipeline: ImageEngine (Pillow) -> WEBP output.
Verification: real-file sample (tests/assets/regression/sample.jpg), format
validation via PIL, HTTP download pipeline, error handling for bad format.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.settings import settings
from app.engines.image_engine import ImageEngine
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
            data={"target_format": "webp", "operation": "jpg-to-webp"},
        )


@pytest.mark.certified
def test_jpg_to_webp_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("jpg", "webp", slug="jpg-to-webp")
    assert plugin is not None
    assert plugin.slug == "jpg-to-webp"
    assert plugin.engine == "image"
    assert "webp" in plugin.target_formats
    assert "jpg" in plugin.source_formats


@pytest.mark.certified
@pytest.mark.asyncio
async def test_jpg_to_webp_engine_conversion(tmp_path: Path) -> None:
    """TEST 002: ImageEngine produces a real WEBP file from a JPG sample."""
    src = SAMPLE_JPG
    assert src.exists(), f"Sample file is missing: {src}"

    engine = ImageEngine()
    out_path = await engine.convert(source_path=src, target_format="webp", temp_dir=tmp_path)

    assert out_path.exists(), "Output webp not created"
    assert out_path.suffix.lower() == ".webp"
    assert out_path.stat().st_size > 0, "Output webp is empty"


@pytest.mark.certified
def test_jpg_to_webp_conversion_success():
    """TEST 003: HTTP conversion succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_jpg_to_webp_output_is_valid_webp():
    """TEST 004: Output file is a valid, non-corrupted WEBP image."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    try:
        with Image.open(str(output_path)) as image:
            assert image is not None
            assert image.format.lower() == "webp"
    except Exception as exc:
        raise AssertionError(f"Output WEBP is corrupted: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_jpg_to_webp_download_served():
    """TEST 005: The converted WEBP is downloadable through /download."""
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
def test_jpg_to_webp_single_output_file():
    """TEST 006: Exactly one WEBP output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    payload = response.json()
    conversion_id = Path(payload["download_path"].removeprefix("/download/")).parts[0]
    files = list((settings.OUTPUT_DIR / conversion_id).glob("*.webp"))
    assert len(files) == 1, f"Expected exactly one WEBP output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_jpg_to_webp_rejects_non_image_input():
    """TEST 007: Non-image input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "webp", "operation": "jpg-to-webp"},
        )
    # Must return honest error (not a fake success).
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body
