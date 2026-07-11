from fastapi.testclient import TestClient

from app.main import app


def test_pdf_to_jpg_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/pdf-to-jpg")

    assert response.status_code == 200
    assert "PDF to JPG Converter Online Free - Converigo" in response.text
    assert "What is PDF to JPG conversion?" in response.text
    assert "FAQPage" in response.text
    assert "application/ld+json" in response.text
    assert "Upload PDF" in response.text
