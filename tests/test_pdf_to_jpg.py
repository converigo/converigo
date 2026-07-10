from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.plugins.registry import registry


def test_pdf_to_jpg_plugin_is_discovered_and_converts():
    plugin = registry.get_plugin("pdf", "jpg")

    assert plugin.slug == "pdf-to-jpg"

    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.pdf"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "application/pdf")},
            data={"target_format": "jpg"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "jpg"

    output_path = Path("outputs/document") / response.json()["filename"]
    assert output_path.exists()
