from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_expected_payload():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "converigo"}


def test_health_endpoint_allows_loopback_host():
    client = TestClient(app)
    response = client.get("/health", headers={"host": "127.0.0.1"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "converigo"}


def test_health_endpoint_accepts_unconfigured_hosts():
    client = TestClient(app)
    response = client.get("/health", headers={"host": "my-app.up.railway.app"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "converigo"}


def test_health_endpoint_allows_railway_internal_host():
    client = TestClient(app)
    response = client.get("/health", headers={"host": "100.64.0.2"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "converigo"}


def test_health_endpoint_allows_railway_internal_host_with_port():
    client = TestClient(app)
    response = client.get("/health", headers={"host": "100.64.0.2:8080"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "converigo"}


def test_non_health_routes_still_require_allowed_host():
    client = TestClient(app)
    response = client.get("/", headers={"host": "blocked.example"})

    assert response.status_code == 400


def test_manifest_endpoint_serves_webmanifest():
    client = TestClient(app)
    response = client.get("/static/site.webmanifest")

    assert response.status_code == 200
    assert '"name": "Converigo"' in response.text
