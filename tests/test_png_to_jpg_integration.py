from pathlib import Path
from io import BytesIO

from PIL import Image
from fastapi.testclient import TestClient

from app.main import app


def test_png_to_jpg_integration(tmp_path):
    client = TestClient(app)

    # Create a small deterministic PNG
    src = tmp_path / "sample.png"
    img = Image.new("RGBA", (32, 32), (255, 0, 0, 255))
    img.save(src, format="PNG")

    with src.open("rb") as f:
        response = client.post(
            "/convert",
            files={"file": (src.name, f, "image/png")},
            data={"target_format": "jpg"},
        )

    assert response.status_code == 201, response.text

    data = response.json()
    assert data.get("status") == "success"
    assert data.get("target_format") == "jpg"

    download_path = data.get("download_path")
    assert download_path, data

    # Retrieve the converted file
    dl = client.get(download_path)
    assert dl.status_code == 200

    # Validate headers if present
    content_type = dl.headers.get("Content-Type") or dl.headers.get("content-type")
    if content_type:
        assert "jpeg" in content_type.lower()

    content = dl.content

    # Magic bytes for JPEG should start with FF D8 FF
    assert content[:3] == b"\xff\xd8\xff"

    # Pillow can open it as JPEG
    im = Image.open(BytesIO(content))
    assert im.format == "JPEG"
    assert im.size[0] > 0 and im.size[1] > 0
