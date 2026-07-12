from fastapi.testclient import TestClient
from app.main import app


def test_image_hub_renders():
    client = TestClient(app)
    resp = client.get("/image-conversion")
    assert resp.status_code == 200
    text = resp.text
    assert "Image Conversion" in text
    assert "Choose a workflow" in text
    assert "Featured workflow (placeholder)" in text
    assert "FAQ content placeholder" in text
    # structured data JSON-LD should be present
    assert 'application/ld+json' in text or 'BreadcrumbList' in text
