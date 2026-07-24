from fastapi.testclient import TestClient

from app.main import app


def test_ready_endpoint_reports_dependency_checks():
    client = TestClient(app)
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["plugin_registry"] is True
    assert response.headers["x-request-id"] == payload["request_id"]


def test_metrics_endpoint_exposes_request_and_stage_metrics():
    client = TestClient(app)

    client.get("/health")
    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert "converigo_requests_total" in metrics_response.text
    assert "converigo_success_rate" in metrics_response.text
    assert "converigo_request_duration_seconds" in metrics_response.text


def test_unsupported_conversion_error_includes_correlation_ids():
    client = TestClient(app)
    response = client.post(
        "/convert",
        files={"file": ("sample.txt", b"hello world", "text/plain")},
        data={"target_format": "png"},
    )

    assert response.status_code == 422
    payload = response.json()
    assert payload["code"] == "UNSUPPORTED_CONVERSION"
    assert payload["request_id"] == response.headers["x-request-id"]
    assert payload["conversion_id"] == response.headers["x-conversion-id"]


def test_slow_request_detection_uses_configurable_threshold(monkeypatch, caplog):
    monkeypatch.setattr("app.core.settings.settings.SLOW_REQUEST_THRESHOLD_MS", 0)
    client = TestClient(app)

    with caplog.at_level("WARNING"):
        response = client.get("/health")

    assert response.status_code == 200
    assert any(record.message == "Slow request detected" for record in caplog.records)