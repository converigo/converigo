from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_mp4_to_mp3_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)

    response = client.get("/mp4-to-mp3")

    assert response.status_code == 200
    assert "MP4 to MP3 Converter Online Free - Converigo" in response.text
    assert "What is MP4 to MP3 conversion?" in response.text
    assert "How do I convert MP4 to MP3?" in response.text
    assert "Is Converigo free?" in response.text
    assert "application/ld+json" in response.text


def test_mp4_to_mp3_conversion_endpoint_still_accepts_uploads():
    client = TestClient(app)
    sample_path = Path(__file__).parent / "sample.mp4"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "video/mp4")},
            data={"target_format": "mp3"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
