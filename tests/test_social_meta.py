from fastapi.testclient import TestClient

from app.core import template_context
from app.main import app


def test_homepage_renders_extended_social_metadata():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'property="og:url"' in html
    assert 'property="og:site_name"' in html
    assert 'property="og:image:alt"' in html
    assert 'property="og:image:width"' in html
    assert 'property="og:image:height"' in html
    assert 'name="twitter:site"' in html
    assert 'name="twitter:creator"' in html


def test_homepage_uses_converigo_og_image():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'property="og:image" content="https://converigo.com/static/images/converigo-og-image.png"' in html
    assert 'name="twitter:image" content="https://converigo.com/static/images/converigo-og-image.png"' in html


def test_homepage_includes_google_site_verification_when_configured(monkeypatch):
    monkeypatch.setenv("GOOGLE_SITE_VERIFICATION", "test-verification-token")
    template_context.build_template_context.cache_clear() if hasattr(template_context.build_template_context, "cache_clear") else None

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert '<meta name="google-site-verification" content="test-verification-token">' in html


def test_homepage_includes_bing_site_verification_when_configured(monkeypatch):
    monkeypatch.setenv("BING_SITE_VERIFICATION", "test-bing-token")
    template_context.build_template_context.cache_clear() if hasattr(template_context.build_template_context, "cache_clear") else None

    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert '<meta name="msvalidate.01" content="test-bing-token">' in html
