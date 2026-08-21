from fastapi.testclient import TestClient

from app.main import app


def test_jpg_to_pdf_legacy_page_is_retired():
    client = TestClient(app)
    response = client.get("/jpg-to-pdf")

    assert response.status_code == 410


def test_jpg_to_pdf_canonical_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/tools/jpg-to-pdf")

    assert response.status_code == 200
    assert "Converter tool" in response.text
    assert "Frequently asked questions" in response.text
    assert "Other converters you may need" in response.text
    assert "Upload file" in response.text
    assert "FAQ" in response.text
    assert "application/ld+json" in response.text
