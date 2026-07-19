from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.plugins.registry import registry


def _assert_output_exists(response):
    assert response.status_code == 201
    data = response.json()
    assert data.get("status") == "success"
    assert "download_path" in data
    download = data["download_path"].lstrip("/")
    out_path = Path(download)
    assert out_path.exists()


def test_jpg_to_png_runtime_conversion():
    plugin = registry.get_plugin("jpg", "png")
    assert plugin is not None

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.jpg"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/jpeg")},
            data={"target_format": "png"},
        )

    _assert_output_exists(response)


def test_png_to_jpg_runtime_conversion():
    plugin = registry.get_plugin("png", "jpg")
    assert plugin is not None

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.png"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/png")},
            data={"target_format": "jpg"},
        )

    _assert_output_exists(response)


def test_xlsx_to_pdf_runtime_conversion():
    plugin = registry.get_plugin("xlsx", "pdf")
    assert plugin is not None

    client = TestClient(app)
    # Prefer the validated fixture; fall back to legacy locations if missing
    sample_path = Path(__file__).parent.parent / "fixtures" / "sample_valid.xlsx"
    if not sample_path.exists():
        sample_path = Path(__file__).parent.parent / "test_files" / "sample.xlsx"
    if not sample_path.exists():
        sample_path = Path(__file__).parent / "sample.xlsx"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"target_format": "pdf"},
        )

    _assert_output_exists(response)


def test_pptx_to_pdf_runtime_conversion():
    plugin = registry.get_plugin("pptx", "pdf")
    assert plugin is not None

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.pptx"
    if not sample_path.exists():
        sample_path = Path(__file__).parent / "sample.pptx"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
            data={"target_format": "pdf"},
        )

    _assert_output_exists(response)


def test_odt_to_pdf_runtime_conversion():
    plugin = registry.get_plugin("odt", "pdf")
    assert plugin is not None

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.odt"
    if not sample_path.exists():
        sample_path = Path(__file__).parent / "sample.odt"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "application/vnd.oasis.opendocument.text")},
            data={"target_format": "pdf"},
        )

    _assert_output_exists(response)


def test_mp4_to_mp3_runtime_placeholder():
    """Placeholder for MP4 -> MP3 runtime test. Skips if sample MP4 not present."""
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.mp4"
    if not sample_path.exists():
        pytest.skip("sample.mp4 not available; skipping MP4->MP3 runtime test")

    plugin = registry.get_plugin("mp4", "mp3")
    assert plugin is not None

    client = TestClient(app)
    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "video/mp4")},
            data={"target_format": "mp3"},
        )

    _assert_output_exists(response)
