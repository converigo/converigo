from fastapi.testclient import TestClient

from app.main import app


def test_word_to_pdf_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/word-to-pdf")

    assert response.status_code == 200
    assert "Word to PDF Converter Online Free - Converigo" in response.text
    assert "What is Word to PDF conversion?" in response.text
    assert "FAQPage" in response.text
    assert "application/ld+json" in response.text
    assert "Upload DOCX" in response.text
