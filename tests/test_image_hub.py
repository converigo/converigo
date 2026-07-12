from fastapi.testclient import TestClient
from app.main import app


def test_image_hub_renders():
    client = TestClient(app)
    resp = client.get("/image-conversion")
    assert resp.status_code == 200
    text = resp.text
    assert "Image Conversion Hub" in text
    assert "Optimize for Web" in text
    assert "Edit-ready" in text
    assert "Create Icons" in text
    assert "Featured converters" in text
    assert "All image converters" in text
    assert "Frequently asked questions" in text
    assert "/tools/png-to-jpg" in text
    assert 'application/ld+json' in text or 'FAQPage' in text
    assert '<link rel="canonical" href="https://converigo.com/image-conversion">' in text
