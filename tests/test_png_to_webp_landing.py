from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_png_to_webp_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)

    response = client.get("/png-to-webp")

    assert response.status_code == 200
    assert "PNG to WEBP Converter Online Free - Converigo" in response.text
    assert "What is PNG to WEBP conversion?" in response.text
    assert "Why convert PNG to WEBP?" in response.text
    assert "Is PNG to WEBP converter free?" in response.text
    assert "application/ld+json" in response.text


def test_png_to_webp_conversion_endpoint_still_accepts_uploads():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.png"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/png")},
            data={"target_format": "webp"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
