import asyncio
from io import BytesIO
from pathlib import Path

import fitz
import pytest
from docx import Document
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

# OLE2 / Compound File Binary header used by genuine legacy .doc files.
_OLE2_HEADER = bytes.fromhex("d0cf11e0a1b11ae1")
_PLACEHOLDER_TEXT = "content unavailable in minimal converter"
_DOCX_MIME = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)


def _make_docx_bytes(paragraphs: list[str]) -> bytes:
    document = Document()
    for text in paragraphs:
        document.add_paragraph(text)
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer.read()


def _upload(client: TestClient, filename: str, content: bytes, media_type: str):
    return client.post(
        "/convert",
        files={"file": (filename, content, media_type)},
        data={"target_format": "pdf"},
    )


def _download_pdf_text(client: TestClient, response) -> str:
    download_path = response.json()["download_path"]
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2
    output_path = settings.OUTPUT_DIR / relative_parts[0] / relative_parts[1]
    assert output_path.exists()
    with fitz.open(str(output_path)) as doc:
        return "\n".join(page.get_text() for page in doc)


def _pdf_text(path: Path) -> str:
    with fitz.open(str(path)) as doc:
        return "\n".join(page.get_text() for page in doc)


def _run_convert(plugin, source_path: Path, output_dir: Path) -> Path:
    return asyncio.run(
        plugin.convert(
            source_path=source_path,
            target_format="pdf",
            output_dir=output_dir,
        )
    )


def test_word_to_pdf_plugin_is_discovered_and_converts():
    """Regression: real .docx via HTTP upload still succeeds with real content."""
    plugin = registry.get_plugin("docx", "pdf")

    assert plugin.slug == "word-to-pdf"

    client = TestClient(app)
    response = _upload(
        client,
        "sample.docx",
        _make_docx_bytes(
            [
                "Converigo DOCX to PDF test",
                "This document should be converted successfully.",
            ]
        ),
        _DOCX_MIME,
    )

    assert response.status_code == 201
    assert response.json()["status"] == "success"
    assert response.json()["target_format"] == "pdf"

    pdf_text = _download_pdf_text(client, response)
    assert "Converigo DOCX to PDF test" in pdf_text
    assert _PLACEHOLDER_TEXT not in pdf_text


def test_docx_renamed_as_doc_gets_real_content(tmp_path):
    """A .doc with PK magic (docx renamed) → real content, not placeholder.

    Uses plugin-level convert because the upload validator expects OLE2
    magic for .doc extensions and rejects PK magic at the upload gate.
    """
    plugin = registry.get_plugin("doc", "pdf")
    assert plugin.slug == "word-to-pdf"
    assert plugin.supports(".doc", "pdf")

    renamed = tmp_path / "renamed.doc"
    renamed.write_bytes(
        _make_docx_bytes(["Real content inside a renamed DOC"])
    )

    output_path = _run_convert(plugin, renamed, tmp_path / "out")
    pdf_text = _pdf_text(output_path)
    assert "Real content inside a renamed DOC" in pdf_text
    assert _PLACEHOLDER_TEXT not in pdf_text


def test_legacy_doc_ole2_fails_explicitly(tmp_path):
    """A genuine legacy .doc (OLE2 magic) must fail with a clear message."""
    plugin = registry.get_plugin("doc", "pdf")
    legacy_doc = tmp_path / "legacy.doc"
    legacy_doc.write_bytes(_OLE2_HEADER + b"\x00" * 512)

    with pytest.raises(RuntimeError, match="not supported"):
        _run_convert(plugin, legacy_doc, tmp_path / "out")

    client = TestClient(app)
    response = _upload(
        client, "legacy.doc", legacy_doc.read_bytes(), "application/msword"
    )
    assert response.status_code == 500
    detail = response.json()["detail"]
    assert "not supported" in detail
    assert "docx" in detail.lower()


def test_corrupt_docx_fails_explicitly(tmp_path):
    """A .docx that is not a valid document must fail, not emit a placeholder.

    Uses plugin-level convert because the upload validator catches
    non-PK-magic files at the upload gate.
    """
    plugin = registry.get_plugin("docx", "pdf")
    corrupt = tmp_path / "broken.docx"
    corrupt.write_bytes(b"this is not a real docx file" * 10)

    with pytest.raises(RuntimeError, match="not a valid DOCX"):
        _run_convert(plugin, corrupt, tmp_path / "out")


def test_non_word_zip_renamed_docx_fails_explicitly(tmp_path):
    """A PK-magic archive that is not a Word document must not fake pass.

    This passes the upload signature gate (PK magic) but has no
    word/document.xml, so the plugin must raise instead of emitting a
    placeholder PDF.
    """
    import zipfile

    plugin = registry.get_plugin("docx", "pdf")
    fake = tmp_path / "fake.docx"

    with zipfile.ZipFile(fake, "w") as zf:
        zf.writestr("readme.txt", "this is a zip, not a word document")
    with fake.open("rb") as fh:
        assert fh.read(4) == b"PK\x03\x04"

    with pytest.raises(RuntimeError, match="could not be parsed"):
        _run_convert(plugin, fake, tmp_path / "out")

