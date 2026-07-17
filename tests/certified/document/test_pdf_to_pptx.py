from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def test_pdf_to_pptx_conversion_creates_pptx(tmp_path: Path):
    client = TestClient(app)

    pdf_path = Path("test_files/sample.pdf")
    assert pdf_path.exists(), "Sample PDF is missing"

    resp = client.post(
        "/convert",
        data={"target_format": "pptx"},
        files={"file": (pdf_path.name, pdf_path.read_bytes(), "application/pdf")},
    )

    assert resp.status_code == 201, resp.text
    payload = resp.json()
    assert payload.get("status") == "success"
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.endswith(".pptx")

    # download_path uses /outputs/... absolute-like path; convert to local filesystem path
    local_path = Path(str(download_path).lstrip("/"))

    assert local_path.exists(), f"Expected output PPTX not found: {local_path}"
    assert local_path.stat().st_size > 0, "Output PPTX is empty"
    assert local_path.suffix.lower() == ".pptx"

