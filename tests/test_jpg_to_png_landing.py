from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_jpg_to_png_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)

    response = client.get("/jpg-to-png")

    assert response.status_code == 200
    assert "JPG to PNG Converter Online Free - Convertin" in response.text
    assert "What is JPG to PNG conversion?" in response.text
    assert "How do I convert JPG to PNG?" in response.text
    assert "Is JPG to PNG converter free?" in response.text
    assert "application/ld+json" in response.text


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
