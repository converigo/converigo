from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app


def test_ppt_to_pdf_conversion_creates_pdf(tmp_path: Path):
    client = TestClient(app)

    pptx_path = Path("tests/sample.pptx")
    assert pptx_path.exists(), "Sample PPTX is missing"

    resp = client.post(
        "/convert",
        data={"target_format": "pdf"},
        files={"file": (pptx_path.name, pptx_path.read_bytes(), "application/vnd.openxmlformats-officedocument.presentationml.presentation")},
    )

    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload.get("status") == "success"
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    assert filename.endswith(".pdf")

    local_path = settings.OUTPUT_DIR / conversion_id / filename
    download_resp = client.get(download_path)
    assert download_resp.status_code == 200, download_resp.text
    assert download_resp.content, "Downloaded content is empty"

    assert local_path.exists(), f"Expected output PDF not found: {local_path}"
    assert local_path.stat().st_size > 0, "Output PDF is empty"
    assert local_path.suffix.lower() == ".pdf"
    assert len(list((settings.OUTPUT_DIR / conversion_id).glob("*"))) == 1
