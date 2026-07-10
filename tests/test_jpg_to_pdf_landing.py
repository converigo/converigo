from fastapi.testclient import TestClient

from app.main import app


def test_jpg_to_pdf_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/jpg-to-pdf")

    assert response.status_code == 200
    assert "JPG to PDF Converter Online Free - Convertin" in response.text
    assert "What is JPG to PDF conversion?" in response.text
    assert "FAQPage" in response.text
    assert "application/ld+json" in response.text
