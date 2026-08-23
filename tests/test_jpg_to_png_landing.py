from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_jpg_to_png_legacy_page_is_retired():
    client = TestClient(app)

    response = client.get("/jpg-to-png")

    assert response.status_code == 410


def test_jpg_to_png_conversion_endpoint_still_accepts_uploads():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.jpg"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/jpeg")},
            data={"target_format": "png"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
