from io import BytesIO
from pathlib import Path

from docx import Document
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry


def test_word_to_pdf_plugin_is_discovered_and_converts():
    plugin = registry.get_plugin("docx", "pdf")

    assert plugin.slug == "word-to-pdf"

    client = TestClient(app)

    document = Document()
    document.add_paragraph("Converigo DOCX to PDF test")
    document.add_paragraph("This document should be converted successfully.")

    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)

    response = client.post(
        "/convert",
        files={
            "file": (
                "sample.docx",
                buffer,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        data={"target_format": "pdf"},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "pdf"

    download_path = response.json()["download_path"]
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2
    conversion_id, filename = relative_parts
    output_path = settings.OUTPUT_DIR / conversion_id / filename
    assert output_path.exists()
