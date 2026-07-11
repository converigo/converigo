from fastapi.testclient import TestClient

from app.main import app


def test_robots_txt_returns_sitemap_reference():
    client = TestClient(app)
    response = client.get("/robots.txt")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "User-agent: *" in response.text
    assert "Allow: /" in response.text
    assert "Sitemap: https://converigo.com/sitemap.xml" in response.text
