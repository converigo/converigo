from fastapi.testclient import TestClient

from app.core.settings import settings
from app.core.template_context import build_template_context
from app.main import app


def test_build_template_context_exposes_ga_values(monkeypatch):
    monkeypatch.setattr(settings, "APP_NAME", "Converigo Test")
    monkeypatch.setattr(settings, "APP_VERSION", "9.9.9")
    monkeypatch.setattr(settings, "GA_MEASUREMENT_ID", "G-TEST123")

    context = build_template_context()

    assert context["app_name"] == "Converigo Test"
    assert context["app_version"] == "9.9.9"
    assert context["ga_measurement_id"] == "G-TEST123"


def test_home_page_renders_ga_snippet_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "GA_MEASUREMENT_ID", "G-TEST123")

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert "googletagmanager.com/gtag/js?id=G-TEST123" in response.text
