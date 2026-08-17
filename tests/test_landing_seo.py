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
        "/jpg-to-webp",
        "/webp-to-jpg",
        "/avif-to-jpg",
        "/heic-to-jpg",
        "/jpg-to-pdf",
        "/xlsx-to-pdf",
        "/svg-to-png",
        "/jpg-to-ico",
        "/jpg-to-tiff",
        "/webp-to-png",
        "/bmp-to-jpg",
        "/bmp-to-png",
        "/pdf-to-jpg",
        "/mp4-to-mp3",
        "/pdf-to-pptx",
        "/png-to-ico",
        "/mp3-to-wav",
        "/mp4-to-ogg",
        "/ppt-to-pdf",
        "/pdf-to-excel",
    ],
)
def test_landing_page_canonical_and_hreflang_for_converters(path):
    client = TestClient(app)
    response = client.get(path)
    assert response.status_code == 200

    assert '<link rel="canonical" href="https://converigo.com' in response.text
    assert f'<link rel="canonical" href="https://converigo.com{path}"' in response.text

    links = _find_hreflang_links(response.text)
    assert links["en"] == f"https://converigo.com{path}?lang=en"
    assert links["id"] == f"https://converigo.com{path}?lang=id"
    assert links["x-default"] == f"https://converigo.com{path}"


def test_homepage_hreflang_uses_root_url():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200

    links = _find_hreflang_links(response.text)
    assert links["en"] == "https://converigo.com/?lang=en"
    assert links["id"] == "https://converigo.com/?lang=id"
    assert links["x-default"] == "https://converigo.com/"
