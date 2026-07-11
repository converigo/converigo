from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_expected_payload():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "convertin"}


def test_health_endpoint_allows_loopback_host():
    client = TestClient(app)
    response = client.get("/health", headers={"host": "127.0.0.1"})

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "convertin"}
