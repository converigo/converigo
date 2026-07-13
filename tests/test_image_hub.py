import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_image_hub_renders():
    client = TestClient(app)
    resp = client.get("/image-conversion")
    assert resp.status_code == 200
    text = resp.text
    assert "Image Conversion Hub" in text
    assert "Featured converters" in text
    assert "Popular converters" in text
    assert "Related converters" in text
    assert "All image converters" in text
    assert "/tools/png-to-jpg" in text
    assert 'application/ld+json' in text or 'FAQPage' in text
    assert '<link rel="canonical" href="https://converigo.com/image-conversion">' in text


@pytest.mark.parametrize(
    ("path", "expected_title"),
    [
        ("/image-conversion", "Image Conversion Hub"),
        ("/pdf-conversion", "PDF Conversion Hub"),
        ("/audio-conversion", "Audio Conversion Hub"),
        ("/video-conversion", "Video Conversion Hub"),
        ("/document-conversion", "Document Conversion Hub"),
    ],
)
def test_category_hubs_render_from_converter_data(path, expected_title):
    client = TestClient(app)
    resp = client.get(path)
    assert resp.status_code == 200
    text = resp.text
    assert expected_title in text
    assert "Featured converters" in text
    assert "Popular converters" in text
    assert "Related converters" in text
    assert "All converters" in text
