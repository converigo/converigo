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
    assert any(loc.endswith("/privacy") for loc in locations)
    assert any(loc.endswith("/terms") for loc in locations)
    assert any(loc.endswith("/contact") for loc in locations)
    assert any(loc.endswith("/cookies") for loc in locations)
