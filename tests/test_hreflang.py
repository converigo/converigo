import re

from fastapi.testclient import TestClient

from app.main import app


def _find_canonical(html: str) -> str | None:
    match = re.search(r'<link\s+rel="canonical"\s+href="([^"]+)"', html)
    return match.group(1) if match else None


def _find_hreflang_links(html: str) -> dict[str, str]:
    pattern = r'<link\s+rel="alternate"\s+hreflang="(?P<lang>[^"]+)"\s+href="(?P<href>[^"]+)"\s*/?>'
    return {match.group('lang'): match.group('href') for match in re.finditer(pattern, html)}


def _assert_public_seo_contract(response, expected_url: str) -> dict[str, str]:
    assert response.status_code == 200
    html = response.text
    assert '?lang=' not in html

    canonical = _find_canonical(html)
    assert canonical == expected_url

    links = _find_hreflang_links(html)
    assert links
    assert 'x-default' in links
    assert links['x-default'] == expected_url

    for locale, href in links.items():
        if locale == 'x-default':
            continue
        assert href == expected_url, f"Locale {locale} should point to {expected_url}, got {href}"

    return links


def test_homepage_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/')
    _assert_public_seo_contract(response, 'https://converigo.com/')


def test_tool_page_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/tools/jpg-to-pdf')
    _assert_public_seo_contract(response, 'https://converigo.com/tools/jpg-to-pdf')


def test_learning_index_hreflang_uses_learning_url():
    client = TestClient(app)
    response = client.get('/learning')
    _assert_public_seo_contract(response, 'https://converigo.com/learning')


def test_learning_article_hreflang_uses_learning_url():
    client = TestClient(app)
    response = client.get('/learning/what-is-png')
    _assert_public_seo_contract(response, 'https://converigo.com/learning/what-is-png')


def test_blog_index_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/blog')
    _assert_public_seo_contract(response, 'https://converigo.com/blog')


def test_blog_article_includes_hreflang_links():
    client = TestClient(app)
    response = client.get('/blog/how-to-convert-mp4-to-mp3')
    _assert_public_seo_contract(response, 'https://converigo.com/blog/how-to-convert-mp4-to-mp3')
