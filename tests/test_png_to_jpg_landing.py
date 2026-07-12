from fastapi.testclient import TestClient

from app.main import app


def test_png_to_jpg_landing_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/png-to-jpg")

    assert response.status_code == 200
    assert "PNG to JPG Converter Online Free" in response.text
    assert "Convert PNG images to JPG online free" in response.text
    assert "href=\"#converter\"" in response.text
    assert "href=\"#how-to-use\"" in response.text
    assert "href=\"#supported-formats\"" in response.text
    assert "href=\"#faq\"" in response.text
    assert "href=\"#related-tools\"" in response.text
    assert "Input format" in response.text
    assert "Output format" in response.text
    assert "FAQPage" in response.text
    assert "SoftwareApplication" in response.text
    assert "BreadcrumbList" in response.text
    assert "application/ld+json" in response.text
