import re

from fastapi.testclient import TestClient

from app.main import app


def _find_hreflang_links(html: str) -> dict[str, str]:
    pattern = r'<link\s+rel="alternate"\s+hreflang="(?P<lang>[^"]+)"\s+href="(?P<href>[^"]+)"\s*/?>'
    return {match.group('lang'): match.group('href') for match in re.finditer(pattern, html)}


def test_landing_page_canonical_and_hreflang_for_converters():
    client = TestClient(app)

    for path in ["/mp4-to-mp3", "/jpg-to-pdf", "/png-to-jpg", "/pdf-to-jpg"]:
        response = client.get(path)
        assert response.status_code == 200

        assert '<link rel="canonical" href="https://converigo.com' in response.text
        assert f'<link rel="canonical" href="https://converigo.com{path}"' in response.text

        links = _find_hreflang_links(response.text)
        assert links["en"] == f"https://converigo.com{path}?lang=en"
        assert links["id"] == f"https://converigo.com{path}?lang=id"
        assert links["x-default"] == f"https://converigo.com{path}"
