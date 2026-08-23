import re

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _find_hreflang_links(html: str) -> dict[str, str]:
    pattern = r'<link\s+rel="alternate"\s+hreflang="(?P<lang>[^"]+)"\s+href="(?P<href>[^"]+)"\s*/?>'
    return {match.group('lang'): match.group('href') for match in re.finditer(pattern, html)}


@pytest.mark.parametrize(
    "path",
    [
        "/tools/jpg-to-pdf",
        "/tools/xlsx-to-pdf",
        "/tools/svg-to-png",
        "/tools/jpg-to-ico",
        "/tools/jpg-to-tiff",
        "/tools/webp-to-png",
        "/tools/bmp-to-jpg",
        "/tools/bmp-to-png",
        "/tools/pdf-to-jpg",
        "/tools/mp4-to-mp3",
        "/tools/pdf-to-pptx",
        "/tools/png-to-ico",
        "/tools/mp3-to-wav",
        "/tools/mp4-to-ogg",
        "/tools/ppt-to-pdf",
        "/tools/pdf-to-excel",
    ],
)
def test_landing_page_canonical_and_hreflang_for_converters(path):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 200

    assert '<link rel="canonical" href="https://converigo.com' in response.text
    assert f'<link rel="canonical" href="https://converigo.com{path}"' in response.text

    links = _find_hreflang_links(response.text)
    assert links["en"] == f"https://converigo.com{path}"
    assert links["id"] == f"https://converigo.com{path}"
    assert links["x-default"] == f"https://converigo.com{path}"


def test_homepage_hreflang_uses_root_url():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

    links = _find_hreflang_links(response.text)
    assert links["en"] == "https://converigo.com/"
    assert links["id"] == "https://converigo.com/"
    assert links["x-default"] == "https://converigo.com/"
