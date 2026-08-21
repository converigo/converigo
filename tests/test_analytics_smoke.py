from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app


def test_homepage_renders_ga4_and_analytics_bootstrap(monkeypatch) -> None:
    monkeypatch.setattr(settings, "GA_MEASUREMENT_ID", "G-SMOKE123")
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    # Exactly one external gtag script tag
    assert response.text.count('googletagmanager.com/gtag/js?id=G-SMOKE123') == 1
    assert response.text.count('async src="https://www.googletagmanager.com/gtag/js?id=G-SMOKE123"') == 1
    # Exactly one gtag config call
    assert response.text.count("gtag('config'") == 1
    # dataLayer must be initialized and converigoAnalytics present
    assert 'window.dataLayer = window.dataLayer || []' in response.text
    assert 'window.converigoAnalytics' in response.text
