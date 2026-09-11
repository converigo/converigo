"""
PROJECT: CONVERIGO
TEST SUITE: Certified WEBP to JPG Converter (IMG-28 / Batch 5)
STATUS: CERTIFIED (Batch 5 evidence run — pending PC merge-gate approval)

Certified-level coverage for the WEBP -> JPG converter
(WEBPToJPGPlugin delegating to ImageEngine/Pillow — mirrors the already
certified webp-to-png pipeline).

Verification: real-file sample (tests/sample.webp), engine-level and
plugin-level conversion, HTTP upload -> convert -> download pipeline,
valid JPEG output, single output file, honest error for wrong input.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.core.settings import settings
from app.engines.image_engine import ImageEngine
from app.main import app
from app.plugins.registry import registry

SAMPLE_WEBP = Path("tests/sample.webp")
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


def _make_real_webp(tmp_path: Path) -> Path:
    webp = tmp_path / "batch5_sample.webp"
    Image.new("RGB", (220, 140), (30, 120, 220)).save(webp, format="WEBP")
    assert webp.exists()
    return webp


def _convert(client, filename: str = "sample.webp"):
    assert SAMPLE_WEBP.exists(), f"Sample file is missing: {SAMPLE_WEBP}"
    with SAMPLE_WEBP.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "image/webp")},
            data={"target_format": "jpg", "operation": "webp-to-jpg"},
        )


@pytest.mark.certified
def test_webp_to_jpg_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("webp", "jpg", slug="webp-to-jpg")
    assert plugin is not None
    assert plugin.slug == "webp-to-jpg"
    assert plugin.engine == "image"
    assert "webp" in plugin.source_formats
    assert "jpg" in plugin.target_formats
    assert "jpeg" in plugin.target_formats


@pytest.mark.certified
def test_webp_to_jpg_engine_conversion(tmp_path: Path) -> None:
    """TEST 002: ImageEngine produces a real JPEG file from a WEBP sample."""
    src = _make_real_webp(tmp_path)
    engine = ImageEngine()
    out_path = asyncio.run(
        engine.convert(source_path=src, target_format="jpg", temp_dir=tmp_path)
    )
    assert out_path.exists(), "Output jpg not created"
    assert out_path.stat().st_size > 0, "Output jpg is empty"
    assert out_path.suffix.lower() in {".jpg", ".jpeg"}
    with Image.open(str(out_path)) as image:
        assert image.format.lower() == "jpeg"


@pytest.mark.certified
def test_webp_to_jpg_conversion_success():
    """TEST 003: HTTP conversion succeeds and returns a download path."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


@pytest.mark.certified
def test_webp_to_jpg_output_is_valid_jpeg():
    """TEST 004: Output file is a valid, non-corrupted JPEG image."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    output_path = _resolve_public_output_path(response)
    try:
        with Image.open(str(output_path)) as image:
            assert image.format.lower() == "jpeg"
    except Exception as exc:
        raise AssertionError(f"Output JPEG is corrupted: {exc}")
    finally:
        output_path.unlink(missing_ok=True)


@pytest.mark.certified
def test_webp_to_jpg_download_served():
    """TEST 005: The converted JPEG is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"
    assert download_resp.content[:3] == b"\xff\xd8\xff", "Downloaded file is not a JPEG"
    assert "attachment" in download_resp.headers.get("content-disposition", "")

    _resolve_public_output_path(response).unlink(missing_ok=True)


@pytest.mark.certified
def test_webp_to_jpg_single_output_file():
    """TEST 006: Exactly one JPG output file is produced per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = [
        p
        for pattern in ("*.jpg", "*.jpeg")
        for p in (OUTPUT_DIR / conversion_id).glob(pattern)
    ]
    assert len(files) == 1, f"Expected exactly one JPG output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


@pytest.mark.certified
def test_webp_to_jpg_rejects_non_image_input():
    """TEST 007: Non-image input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "jpg", "operation": "webp-to-jpg"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body

