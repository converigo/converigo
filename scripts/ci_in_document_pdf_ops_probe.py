"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F3)
Version : 1.0.0

In-document probe for Factory Batch F3 (cluster G-C: PDF Operations).

Executed INSIDE the production image by docker-runtime-verify step [4/5]:

    python scripts/ci_in_document_pdf_ops_probe.py

All fixtures are generated in-image with reportlab + pypdf (both are
requirements of the production image), so the probe is self-sufficient
exactly like the F2 image-ops probe.  Each of the six F3 factory plugins
is resolved through the real registry, executed against a temp working
dir, and the output is re-opened and validated (page geometry, encryption
state, metadata, watermark stream, extracted text).  Exit code 0 = PASS.
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pypdf import PdfReader, PdfWriter  # noqa: E402
from reportlab.pdfgen.canvas import Canvas  # noqa: E402

from app.plugins.registry import registry  # noqa: E402

PROBE_TEXT_1 = "Converigo F3 probe page one"
PROBE_TEXT_2 = "Converigo F3 probe page two"
PRODUCER = "Converigo (https://converigo.com)"


def _make_text_pdf(path: Path) -> Path:
    canvas = Canvas(str(path), pagesize=(612, 792))
    for text in (PROBE_TEXT_1, PROBE_TEXT_2):
        canvas.setFont("Helvetica", 14)
        canvas.drawString(72, 720, text)
        canvas.showPage()
    canvas.save()
    return path


def _make_owner_encrypted_pdf(path: Path) -> Path:
    base = path.with_name(f"{path.stem}_base.pdf")
    _make_text_pdf(base)
    reader = PdfReader(str(base))
    writer = PdfWriter()
    writer.append(reader)
    writer.encrypt(user_password="", owner_password="converigo-owner")
    with path.open("wb") as handle:
        writer.write(handle)
    assert PdfReader(str(path)).decrypt("") is not None
    base.unlink(missing_ok=True)
    return path


def _run(slug: str, fixture: Path, target_format: str, check) -> None:
    assert registry.has_slug(slug), f"{slug} not registered"
    plugin = registry.by_slug[slug]
    output = asyncio.run(plugin.convert(fixture, target_format))
    assert output.is_file(), f"{slug}: no output file {output}"
    check(output)
    print(f"PROBE {slug}: {fixture.name} -> {output.name} OK")


def _rotate_check(path: Path) -> None:
    reader = PdfReader(str(path))
    assert len(reader.pages) == 2, len(reader.pages)
    for page in reader.pages:
        assert (page.get("/Rotate") or 0) == 90, page.get("/Rotate")


def _unlock_check(path: Path) -> None:
    reader = PdfReader(str(path))
    assert not reader.is_encrypted, "unlock output must open without a password"
    assert PROBE_TEXT_1 in (reader.pages[0].extract_text() or "")


def _metadata_check(path: Path) -> None:
    metadata = PdfReader(str(path)).metadata
    assert metadata.producer == PRODUCER, metadata.producer
    assert metadata.creator == PRODUCER, metadata.creator


def _watermark_check(path: Path) -> None:
    reader = PdfReader(str(path))
    found = False
    for page in reader.pages:
        contents = page.get_contents()
        if contents is not None and b"CONVERIGO" in contents.get_data():
            found = True
    assert found, "watermark stamp text missing from page content streams"


def _html_check(path: Path) -> None:
    body = path.read_text(encoding="utf-8")
    assert body.lstrip().lower().startswith("<!doctype html>")
    assert PROBE_TEXT_1 in body and PROBE_TEXT_2 in body
    assert "NOT a layout-preserving conversion" in body


def _md_check(path: Path) -> None:
    body = path.read_text(encoding="utf-8")
    assert "## Page 1" in body and "## Page 2" in body
    assert PROBE_TEXT_1 in body and PROBE_TEXT_2 in body


def main(_argv: list[str]) -> int:
    with tempfile.TemporaryDirectory(prefix="f3_probe_") as tmp:
        root = Path(tmp)
        text_pdf = _make_text_pdf(root / "probe.pdf")
        owner_locked = _make_owner_encrypted_pdf(root / "probe_locked.pdf")
        _run("pdf-rotate", text_pdf, "pdf", _rotate_check)
        _run("pdf-unlock", owner_locked, "pdf", _unlock_check)
        _run("pdf-watermark", text_pdf, "pdf", _watermark_check)
        _run("pdf-metadata", text_pdf, "pdf", _metadata_check)
        _run("pdf-to-html", text_pdf, "html", _html_check)
        _run("pdf-to-md", text_pdf, "md", _md_check)
    print("F3 IN-IMAGE PROBE PASS: 6 pdf ops converters OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
