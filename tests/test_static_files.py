from fastapi.testclient import TestClient

from app.main import app


def test_manifest_is_served_from_static_files():
    client = TestClient(app)
    response = client.get("/static/site.webmanifest")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")
