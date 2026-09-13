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


# Strings that must never reach an HTTP response body: internal library names,
# exception class names and on-disk upload paths.
_INTERNAL_MARKERS = (
    "Traceback",
    "openpyxl",
    "python-docx",
    "docx.api",
    "DocxDocument",
    "PackageNotFoundError",
    "BadZipFile",
    "InvalidFileException",
    "uploads\\",
    "uploads/",
    ".venv",
    "site-packages",
)


def _assert_no_internal_leak(message: str) -> None:
    leaked = [marker for marker in _INTERNAL_MARKERS if marker.lower() in message.lower()]
    assert not leaked, f"Response body leaks internal details: {leaked} in {message!r}"


def test_legacy_doc_pair_is_no_longer_registered():
    """PR-1: (doc -> pdf) could never work, so it must not be routable at all."""
    with pytest.raises(ValueError):
        registry.get_plugin("doc", "pdf")

    plugin = registry.get_plugin("docx", "pdf")
    assert plugin.slug == "word-to-pdf"
    assert "doc" not in plugin.source_formats
    assert "docx" in plugin.source_formats


def test_legacy_doc_upload_is_refused_with_resave_guidance():
    """A genuine .doc upload gets an honest 4xx + re-save guidance, never a 500.

    Before PR-1 this returned HTTP 500.
    """
    client = TestClient(app)
    response = _upload(
        client,
        "legacy.doc",
        _OLE2_HEADER + b"\x00" * 512,
        "application/msword",
    )

    assert response.status_code == 415, response.text
    body = response.json()
    assert body["code"] == "UNSUPPORTED_FILE_TYPE", body
    message = body["message"]
    assert "Legacy .doc" in message, message
    assert ".docx" in message, message
    _assert_no_internal_leak(message)


def test_ole2_masquerading_as_docx_returns_honest_422(tmp_path):
    """OLE2 bytes behind a .docx name must give 422 UNSUPPORTED_CONVERSION.

    The upload gate cannot stop this one: the container signature check is
    skipped when the MIME matches, so the honest refusal has to happen in the
    converter. Before PR-1 this returned HTTP 500.
    """
    client = TestClient(app)
    response = client.post(
        "/convert",
        files={"file": ("fake.docx", _OLE2_HEADER + b"\x00" * 512, _DOCX_MIME)},
        data={"target_format": "pdf"},
    )

    assert response.status_code == 422, response.text
    body = response.json()
    assert body["code"] == "UNSUPPORTED_CONVERSION", body
    assert "ole2" in body["message"].lower(), body
    assert "docx" in body["message"].lower(), body
    _assert_no_internal_leak(body["message"])


def test_plugin_raises_legacy_format_unsupported_error(tmp_path):
    """The plugin layer raises the dedicated, honestly-typed legacy error."""
    from app.services.conversion_service import UnsupportedConversionError

    plugin = registry.get_plugin("docx", "pdf")
    legacy_docx = tmp_path / "masquerade.docx"
    legacy_docx.write_bytes(_OLE2_HEADER + b"\x00" * 512)

    with pytest.raises(UnsupportedConversionError) as excinfo:
        _run_convert(plugin, legacy_docx, tmp_path / "out")

    assert type(excinfo.value).__name__ == "LegacyFormatUnsupportedError"
    assert "docx" in str(excinfo.value).lower()
    _assert_no_internal_leak(str(excinfo.value))


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

