from fastapi.testclient import TestClient

from app.main import app


def test_homepage_renders_faq_section_and_jsonld():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert "Frequently asked questions" in html
    assert "What is Converigo?" in html
    assert 'type="application/ld+json"' in html
    assert "FAQPage" in html
    assert "Organization" in html
