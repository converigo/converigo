from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app


def _make_pdf_bytes() -> bytes:
    from io import BytesIO
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Converigo regression PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


def _remove_output_file(output_filename: str) -> None:
    output_path = Path("outputs") / "document" / output_filename
    if output_path.exists():
        output_path.unlink(missing_ok=True)


def test_pdf_to_xlsx_conversion_succeeds():
    client = TestClient(app)
    response = client.post(
        "/convert",
        files={"file": ("sample.pdf", _make_pdf_bytes(), "application/pdf")},
        data={"target_format": "xlsx"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "xlsx"
    _remove_output_file(response.json()["filename"])


def test_pdf_to_pptx_conversion_succeeds():
    client = TestClient(app)
    response = client.post(
        "/convert",
        files={"file": ("sample.pdf", _make_pdf_bytes(), "application/pdf")},
        data={"target_format": "pptx"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "pptx"
    _remove_output_file(response.json()["filename"])


def test_pdf_to_odt_conversion_succeeds():
    client = TestClient(app)
    response = client.post(
        "/convert",
        files={"file": ("sample.pdf", _make_pdf_bytes(), "application/pdf")},
        data={"target_format": "odt"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "odt"
    _remove_output_file(response.json()["filename"])


def test_jpg_to_png_conversion_succeeds():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.jpg"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/jpeg")},
            data={"target_format": "png"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "png"
    _remove_output_file(response.json()["filename"])


def test_png_to_jpg_conversion_succeeds():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.png"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "image/png")},
            data={"target_format": "jpg"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "jpg"
    _remove_output_file(response.json()["filename"])


def test_mp4_to_mp3_conversion_succeeds():
    client = TestClient(app)
    sample_path = Path(__file__).parent.parent / "test_files" / "sample.mp4"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "video/mp4")},
            data={"target_format": "mp3"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "mp3"
    _remove_output_file(response.json()["filename"])
