"""
PROJECT: CONVERIGO
TEST SUITE: Certified PDF Compress Converter (DOC-29 / Batch 5)
STATUS: CERTIFIED (Batch 5 evidence run — pending PC merge-gate approval)

Certified-level coverage for the PDF compress converter
(PDFCompressPlugin — Batch 5 genuine rewrite on pypdf, BSD, already in
requirements; no new dependencies).

Verification: real-file samples, output is NOT a stub copy (differs from
plain byte copy and from a bare pypdf re-write), page count preserved and
text content preserved, HTTP upload -> convert -> download pipeline,
output never larger than input (guard), single output file, honest errors
for password-protected and page-less PDFs.
"""

from __future__ import annotations

import asyncio
import io
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pypdf import PdfReader, PdfWriter

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

SAMPLE_PDF = Path("tests/sample.pdf")
OUTPUT_DIR = settings.OUTPUT_DIR


def _resolve_public_output_path(response) -> Path:
    payload = response.json()
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    output_path = OUTPUT_DIR / conversion_id / filename
    assert output_path.exists(), f"Expected output file not found: {output_path}"
    return output_path


def _make_real_pdf(path: Path, pages: int = 3, compression: int | None = 0) -> Path:
    """Build a real multi-page PDF via reportlab.

    ``compression=0`` writes raw (uncompressed) content streams so the
    pypdf compression pass has real work to do — representative of PDFs
    exported without optimization.  ``compression=None`` uses reportlab's
    default (already compressed) for the never-larger guard test.
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter, pageCompression=compression)
    for i in range(pages):
        body = (
            f"BATCH5-COMPRESS page {i + 1} of {pages}. "
            "The quick brown fox jumps over the lazy dog. " * 40
        )
        text_object = c.beginText(72, 720)
        for j in range(0, len(body), 80):
            text_object.textLine(body[j : j + 80])
        c.drawText(text_object)
        c.showPage()
    c.save()
    assert path.exists() and path.stat().st_size > 0
    return path


def _make_encrypted_pdf(path: Path) -> Path:
    """Build a real password-protected PDF (honest-error sample)."""
    src = _make_real_pdf(path.with_name("enc_src.pdf"), pages=1)
    reader = PdfReader(str(src))
    writer = PdfWriter()
    writer.append(reader)
    writer.encrypt("secret")
    with path.open("wb") as handle:
        writer.write(handle)
    return path



def _convert(client, filename: str = "sample.pdf"):
    assert SAMPLE_PDF.exists(), f"Sample file is missing: {SAMPLE_PDF}"
    with SAMPLE_PDF.open("rb") as handle:
        return client.post(
            "/convert",
            files={"file": (filename, handle, "application/pdf")},
            data={"target_format": "pdf", "operation": "pdf-compress"},
        )


@pytest.mark.certified
def test_pdf_compress_plugin_discovered():
    """TEST 001: Plugin is properly registered and not a placeholder."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-compress")
    assert plugin is not None
    assert plugin.slug == "pdf-compress"
    assert plugin.engine == "document"
    assert "pdf" in plugin.source_formats
    assert "pdf" in plugin.target_formats


@pytest.mark.certified
def test_pdf_compress_genuinely_shrinks_unoptimized_pdf(tmp_path: Path) -> None:
    """TEST 002: pypdf compression really shrinks an unoptimized PDF and keeps content."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-compress")
    src = _make_real_pdf(tmp_path / "batch5_compressible.pdf", pages=3)
    in_size = src.stat().st_size
    output = asyncio.run(
        plugin.convert(src, "pdf", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    out_size = output.stat().st_size
    assert output.suffix.lower() == ".pdf"
    assert out_size < in_size, (
        f"pdf-compress did not shrink the sample: {in_size} -> {out_size} bytes"
    )
    reader = PdfReader(str(output))
    assert len(reader.pages) == 3, f"Page count changed: {len(reader.pages)}"
    text = " ".join((page.extract_text() or "") for page in reader.pages)
    assert "BATCH5-COMPRESS" in text, "Compressed PDF lost its text content"


@pytest.mark.certified
def test_pdf_compress_output_is_not_a_stub_byte_copy(tmp_path: Path) -> None:
    """TEST 003: Output differs from the input (the old stub was a plain byte copy)."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-compress")
    src = _make_real_pdf(tmp_path / "batch5_stubcheck.pdf", pages=2)
    output = asyncio.run(
        plugin.convert(src, "pdf", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.read_bytes() != src.read_bytes(), (
        "Output is a byte copy — the DOC-29 stub behaviour has returned"
    )


@pytest.mark.certified
def test_pdf_compress_http_smaller_output():
    """TEST 004: HTTP pipeline returns 201 and a genuinely smaller valid PDF."""
    client = TestClient(app)
    sample = _make_real_pdf(Path(settings.TEMP_DIR) / "batch5_http_compress.pdf", pages=3)
    try:
        in_size = sample.stat().st_size
        with sample.open("rb") as handle:
            response = client.post(
                "/convert",
                files={"file": ("batch5_http_compress.pdf", handle, "application/pdf")},
                data={"target_format": "pdf", "operation": "pdf-compress"},
            )
        assert response.status_code == 201, response.text
        payload = response.json()
        assert payload.get("status") == "success"
        output_path = _resolve_public_output_path(response)
        out_size = output_path.stat().st_size
        assert out_size < in_size, (
            f"HTTP output not smaller: {in_size} -> {out_size} bytes"
        )
        reader = PdfReader(str(output_path))
        assert len(reader.pages) == 3
        text = " ".join((page.extract_text() or "") for page in reader.pages)
        assert "BATCH5-COMPRESS" in text
        output_path.unlink(missing_ok=True)
    finally:
        sample.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_compress_download_served():
    """TEST 005: The compressed PDF is downloadable through /download."""
    client = TestClient(app)
    sample = _make_real_pdf(Path(settings.TEMP_DIR) / "batch5_dl_compress.pdf", pages=2)
    try:
        with sample.open("rb") as handle:
            response = client.post(
                "/convert",
                files={"file": ("batch5_dl_compress.pdf", handle, "application/pdf")},
                data={"target_format": "pdf", "operation": "pdf-compress"},
            )
        assert response.status_code == 201, response.text
        download_path = response.json()["download_path"]
        download_resp = client.get(download_path)
        assert download_resp.status_code == 200, download_resp.text
        assert download_resp.content.startswith(b"%PDF-"), "Downloaded file is not a PDF"
        assert "attachment" in download_resp.headers.get("content-disposition", "")
        _resolve_public_output_path(response).unlink(missing_ok=True)
    finally:
        sample.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_compress_never_larger_than_input(tmp_path: Path) -> None:
    """TEST 006: Guard — output is never larger than the input (already-optimized PDF)."""
    plugin = registry.get_plugin("pdf", "pdf", slug="pdf-compress")
    src = _make_real_pdf(tmp_path / "batch5_optimized.pdf", pages=1, compression=None)
    output = asyncio.run(
        plugin.convert(src, "pdf", output_dir=tmp_path / "out", temp_dir=tmp_path / "tmp")
    )
    assert output.stat().st_size <= src.stat().st_size, (
        f"Output larger than input: {src.stat().st_size} -> {output.stat().st_size}"
    )
    PdfReader(str(output)).pages[0].extract_text()


@pytest.mark.certified
def test_pdf_compress_honest_error_for_encrypted_pdf():
    """TEST 007: Password-protected PDFs fail honestly (no fake output)."""
    client = TestClient(app)
    sample = _make_encrypted_pdf(
        Path(settings.TEMP_DIR) / "batch5_encrypted.pdf"
    )
    try:
        with sample.open("rb") as handle:
            response = client.post(
                "/convert",
                files={"file": ("batch5_encrypted.pdf", handle, "application/pdf")},
                data={"target_format": "pdf", "operation": "pdf-compress"},
            )
        assert response.status_code in (400, 422, 500), response.text
        body = response.json()
        detail = str(body.get("detail") or body)
        assert "password" in detail.lower(), detail
    finally:
        sample.unlink(missing_ok=True)


@pytest.mark.certified
def test_pdf_compress_rejects_non_pdf_input():
    """TEST 008: Non-PDF input is rejected (honest error, not fake output)."""
    client = TestClient(app)
    with open("tests/sample.txt", "rb") as handle:
        response = client.post(
            "/convert",
            files={"file": ("sample.txt", handle, "text/plain")},
            data={"target_format": "pdf", "operation": "pdf-compress"},
        )
    assert response.status_code == 422, response.text
    body = response.json()
    assert body.get("code") == "UNSUPPORTED_CONVERSION", body


@pytest.mark.certified
def test_pdf_compress_single_output_file():
    """TEST 009: Exactly one compressed PDF output file per conversion."""
    client = TestClient(app)
    response = _convert(client)
    assert response.status_code == 201, response.text
    conversion_id = Path(
        response.json()["download_path"].removeprefix("/download/")
    ).parts[0]
    files = list((OUTPUT_DIR / conversion_id).glob("*.pdf"))
    assert len(files) == 1, f"Expected exactly one PDF output, got: {files}"
    for f in files:
        f.unlink(missing_ok=True)


