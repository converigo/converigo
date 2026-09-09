from fastapi.testclient import TestClient

from app.main import app


def test_png_to_jpg_legacy_page_is_retired():
    client = TestClient(app)
    response = client.get("/png-to-jpg")

    assert response.status_code == 410


def test_png_to_jpg_canonical_page_renders_with_seo_and_faq():
    client = TestClient(app)
    response = client.get("/tools/png-to-jpg")

    assert response.status_code == 200
    assert "Convert PNG to JPG Online Free | Converigo" in response.text
    assert "Convert PNG images to JPG format online for free. Reduce compatibility issues, preserve image quality, and get a fast secure online conversion." in response.text
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
