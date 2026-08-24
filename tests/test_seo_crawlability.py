from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_missing_page_returns_404_status_and_custom_content():
    response = client.get("/this-page-should-not-exist")

    assert response.status_code == 404
    html = response.text
    assert "Page Not Found" in html
    assert "Popular converters" in html
    assert "Learning Center" in html
    assert 'name="robots" content="noindex,follow"' in html


def test_legacy_root_converter_page_is_retired():
    response = client.get("/mp4-to-mp3")

    assert response.status_code == 410


def test_blog_page_keeps_breadcrumb_json_ld_unchanged():
    response = client.get("/blog/how-to-convert-mp4-to-mp3")

    assert response.status_code == 200
    html = response.text
    assert 'aria-label="Breadcrumb"' in html

    structured_data = response.context.get("structured_data") if hasattr(response, "context") else None
    assert structured_data is not None
    assert structured_data["@graph"][-1]["itemListElement"][0]["name"] == "Home"
    assert structured_data["@graph"][-1]["itemListElement"][1]["name"] == "Blog"
    assert structured_data["@graph"][-1]["itemListElement"][2]["name"] == "Cara Convert MP4 ke MP3 Online Gratis Tanpa Aplikasi"
