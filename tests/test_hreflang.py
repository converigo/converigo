import re

from fastapi.testclient import TestClient

from app.main import app


def _find_hreflang_links(html: str) -> dict[str, str]:
    pattern = r'<link\s+rel="alternate"\s+hreflang="(?P<lang>[^"]+)"\s+href="(?P<href>[^"]+)"\s*/?>'
    return {match.group('lang'): match.group('href') for match in re.finditer(pattern, html)}


def test_homepage_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/')

    assert response.status_code == 200
    links = _find_hreflang_links(response.text)

    assert links['en'] == 'https://converigo.com/?lang=en'
    assert links['id'] == 'https://converigo.com/?lang=id'
    assert links['x-default'] == 'https://converigo.com/'


def test_tool_page_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/tools/jpg-to-pdf')

    assert response.status_code == 200
    links = _find_hreflang_links(response.text)

    assert links['en'] == 'https://converigo.com/tools/jpg-to-pdf?lang=en'
    assert links['id'] == 'https://converigo.com/tools/jpg-to-pdf?lang=id'
    assert links['x-default'] == 'https://converigo.com/tools/jpg-to-pdf'


def test_blog_index_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/blog')

    assert response.status_code == 200
    links = _find_hreflang_links(response.text)

    assert links['en'] == 'https://converigo.com/blog?lang=en'
    assert links['id'] == 'https://converigo.com/blog?lang=id'
    assert links['x-default'] == 'https://converigo.com/blog'


def test_blog_article_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/blog/how-to-convert-mp4-to-mp3')

    assert response.status_code == 200
    links = _find_hreflang_links(response.text)

    assert links['en'] == 'https://converigo.com/blog/how-to-convert-mp4-to-mp3?lang=en'
    assert links['id'] == 'https://converigo.com/blog/how-to-convert-mp4-to-mp3?lang=id'
    assert links['x-default'] == 'https://converigo.com/blog/how-to-convert-mp4-to-mp3'
