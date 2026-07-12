from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_webp_to_png_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)

    response = client.get("/webp-to-png")

    assert response.status_code == 200
    assert "WEBP to PNG Converter Online Free - Converigo" in response.text
    assert "What is WEBP to PNG conversion?" in response.text
    assert "Why convert WEBP to PNG?" in response.text
    assert "Does PNG preserve image quality?" in response.text
    assert "application/ld+json" in response.text


def test_webp_to_png_conversion_endpoint_still_accepts_uploads():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.webp"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/webp")},
            data={"target_format": "png"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
