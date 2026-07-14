from fastapi.testclient import TestClient

from app.main import app


def test_manifest_is_served_from_static_files():
    client = TestClient(app)
    response = client.get("/static/site.webmanifest")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/manifest+json")


def test_logo_asset_is_served_as_valid_png():
    client = TestClient(app)
    response = client.get("/static/images/converigo-logo.png")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("image/png")
    assert response.content.startswith(b"\x89PNG")


def test_header_uses_canonical_logo_path_and_nonzero_render_size():
    from pathlib import Path
    from PIL import Image

    template = Path("app/templates/components/header.html").read_text(encoding="utf-8")
    assert '/static/images/converigo-logo.png' in template

    with Image.open("app/static/images/converigo-logo.png") as img:
        width, height = img.size

    assert width > 0 and height > 0
    assert width >= 48 and height >= 48
