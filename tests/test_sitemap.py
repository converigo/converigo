from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient

from app.main import app


def test_sitemap_contains_homepage_converter_and_trust_pages():
    client = TestClient(app)
    response = client.get("/sitemap.xml")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    root = ET.fromstring(response.text)
    namespaces = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    locations = [loc.text for loc in root.findall(".//sm:url/sm:loc", namespaces)]

    assert any(loc.endswith("/") for loc in locations)
    assert any("/tools/" in loc for loc in locations)
    assert any(loc.endswith("/about") for loc in locations)
    assert any(loc.endswith("/privacy-policy") for loc in locations)
    assert any(loc.endswith("/terms") for loc in locations)
    assert any(loc.endswith("/contact") for loc in locations)
    assert any(loc.endswith("/cookies") for loc in locations)
    assert any(loc.endswith("/mp4-to-mp3") for loc in locations)
    assert any(loc.endswith("/jpg-to-pdf") for loc in locations)
    assert any(loc.endswith("/png-to-jpg") for loc in locations)
    assert any(loc.endswith("/pdf-to-jpg") for loc in locations)
    assert any(loc.endswith("/blog") for loc in locations)
    assert any(loc.endswith("/blog/how-to-convert-mp4-to-mp3") for loc in locations)
    assert any(loc.endswith("/blog/jpg-to-pdf-guide") for loc in locations)
    assert any(loc.endswith("/blog/png-to-jpg-guide") for loc in locations)
    assert not any(loc.endswith("/tools/mp4-to-mp3") for loc in locations)
    assert not any(loc.endswith("/tools/jpg-to-pdf") for loc in locations)
    assert not any(loc.endswith("/tools/png-to-jpg") for loc in locations)
    assert not any(loc.endswith("/tools/pdf-to-jpg") for loc in locations)
