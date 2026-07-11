from io import BytesIO
from pathlib import Path

from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from app.main import app
from app.plugins.registry import registry


def test_pdf_to_jpg_plugin_is_discovered_and_converts():
    plugin = registry.get_plugin("pdf", "jpg")

    assert plugin.slug == "pdf-to-jpg"

    client = TestClient(app)

    buffer = BytesIO()
    pdf_canvas = canvas.Canvas(buffer)
    pdf_canvas.drawString(100, 750, "Converigo PDF to JPG test")
    pdf_canvas.save()
    buffer.seek(0)

    response = client.post(
        "/convert",
        files={"file": ("sample.pdf", buffer, "application/pdf")},
        data={"target_format": "jpg"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "jpg"

    output_path = Path("outputs/document") / response.json()["filename"]
    assert output_path.exists()
