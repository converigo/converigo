"""
PROJECT: CONVERIGO
TEST SUITE: Certified PPTX to JPG Converter (PR-A2)
STATUS: DEVELOPMENT (Not yet certified — certification pending evidence review)

Basic test coverage for the PPTX -> JPG converter (first slide only).
Pipeline: python-pptx -> reportlab PDF -> PyMuPDF -> JPG.
"""

from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry


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


def _convert(client, filename: str, operation: str, target: str = "jpg"):
    sample = Path("tests/assets/regression") / filename
    assert sample.exists(), f"Sample file is missing: {sample}"
    with sample.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (sample.name, handle, "application/octet-stream")},
            data={"target_format": target, "operation": operation},
        )


def test_ppt_to_jpg_plugin_discovered():
    """TEST 001: Plugin is properly registered."""
    plugin = registry.get_plugin("pptx", "jpg", slug="ppt-to-jpg")
    assert plugin is not None
    assert plugin.slug == "ppt-to-jpg"
    assert "jpg" in plugin.target_formats or "jpeg" in plugin.target_formats


def test_ppt_to_jpg_conversion_success():
    """TEST 002: PPTX converts to JPG successfully."""
    client = TestClient(app)
    response = _convert(client, "sample.pptx", "ppt-to-jpg")
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success"
    assert payload.get("download_path"), payload


def test_ppt_to_jpg_output_exists_and_extension_correct():
    """TEST 003: Output JPG file is created with a correct .jpg extension."""
    client = TestClient(app)
    response = _convert(client, "sample.pptx", "ppt-to-jpg")
    assert response.status_code == 201, response.text

    output_path = _resolve_public_output_path(response)
    assert output_path.suffix.lower() in {".jpg", ".jpeg"}
    assert output_path.stat().st_size > 0, "Output JPG is empty"
    output_path.unlink(missing_ok=True)


def test_ppt_to_jpg_output_is_valid_jpeg():
    """TEST 004: Output JPG is a valid, non-corrupted JPEG image."""
    client = TestClient(app)
    response = _convert(client, "sample.pptx", "ppt-to-jpg")
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


def test_ppt_to_jpg_first_slide_only_single_output():
    """TEST 005: Exactly one JPG output file is produced (first slide only)."""
    client = TestClient(app)
    response = _convert(client, "sample.pptx", "ppt-to-jpg")
    assert response.status_code == 201, response.text

    payload = response.json()
    conversion_id = Path(payload["download_path"].removeprefix("/download/")).parts[0]
    files = list((settings.OUTPUT_DIR / conversion_id).glob("*.jpg"))
    assert len(files) == 1, f"Expected exactly one JPG output, got: {files}"
    files[0].unlink(missing_ok=True)


def test_ppt_to_jpg_download_served():
    """TEST 006: The converted JPG is downloadable through /download."""
    client = TestClient(app)
    response = _convert(client, "sample.pptx", "ppt-to-jpg")
    assert response.status_code == 201, response.text

    download_path = response.json()["download_path"]
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"

    output_path = _resolve_public_output_path(response)
    output_path.unlink(missing_ok=True)
