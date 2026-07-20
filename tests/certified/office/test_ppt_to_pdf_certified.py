from pathlib import Path

from fastapi.testclient import TestClient

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
    assert download_path.endswith(".pdf")

    local_path = Path(str(download_path).lstrip("/"))

    assert local_path.exists(), f"Expected output PDF not found: {local_path}"
    assert local_path.stat().st_size > 0, "Output PDF is empty"
    assert local_path.suffix.lower() == ".pdf"
