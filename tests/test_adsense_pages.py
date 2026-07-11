from fastapi.testclient import TestClient

from app.main import app


def test_adsense_required_pages_are_available():
    client = TestClient(app)

    for path in ["/about", "/contact", "/privacy-policy", "/terms"]:
        response = client.get(path)
        assert response.status_code == 200, f"Expected {path} to be available"
        assert "text/html" in response.headers.get("content-type", "")
