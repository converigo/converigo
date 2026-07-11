from fastapi.testclient import TestClient

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
