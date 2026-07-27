from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry


def test_jpg_to_pdf_plugin_is_discovered_and_converts():
    plugin = registry.get_plugin("jpg", "pdf")

    assert plugin.slug == "jpg-to-pdf"

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.jpg"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/jpeg")},
            data={"target_format": "pdf"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "pdf"

    output_filename = response.json()["filename"]
    download_path = response.json()["download_path"]
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2
    conversion_id, filename = relative_parts
    output_path = settings.OUTPUT_DIR / conversion_id / filename
    assert output_path.exists()
