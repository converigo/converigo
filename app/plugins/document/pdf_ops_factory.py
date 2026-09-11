"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F3)
Version : 1.0.0

PDF Ops Factory Batch F3 - cluster G-C (PDF Operations, net-new).

Six thin converters built on the F0 certified factory scaffolding
(app/factory/plugin_base.py): discovery -> supports() check -> working
root -> single servable file -> non-empty output -> honest RuntimeError
-> API 422 UNSUPPORTED_CONVERSION.

Supervisor decisions applied (F3 audit tmp/f3_pdf_ops_audit.md):
- D5a: pdf-protect is DEFERRED to a future options-channel batch.
  Without an options channel there is no honest way to source a user
  password, and a fixed password would be false security.
- D5b: pdf-to-html / pdf-to-md ship as MVP fixed-semantics TEXT
  EXTRACTION (pypdf page.extract_text()); they are NOT layout-preserving
  conversions and the descriptions / generated contracts say so honestly.
- D1 (F2 carry-over): pdf-watermark keeps FIXED semantics (a
  semi-transparent "CONVERIGO" stamp at the bottom-right of every page).
- D4 (F2 carry-over): operation slug convention <format>-<operation>.
  pdf-rotate, pdf-unlock, pdf-watermark and pdf-metadata share the
  (pdf, pdf) pair exactly like the certified pdf-compress / pdf-split
  precedent: the registry pair index keeps one deterministic legacy
  entry while every operation resolves through its unique slug
  (registry.get_plugin("pdf", "pdf", slug=...)).  Self-pairs are
  excluded from the STATIC_TARGET_MAP dropdown; pdf-to-html / pdf-to-md
  are regular cross-format converters.

Engine reuse (zero new dependencies): pypdf 6.16.2 (already required)
for rotate / unlock / metadata / extraction; the watermark stamp page
is rendered with reportlab (already required for txt-to-pdf and
jpg-to-pdf) into an in-memory buffer, so no new requirements and no
bundled assets.

Honest error mapping: unreadable, password-protected (non-empty user
password) and text-less inputs raise the typed
``UnsupportedConversionError`` (lazy import, rar-extract precedent) so
the API boundary keeps answering with the honest 422
UNSUPPORTED_CONVERSION error class instead of a 500 or a fabricated
output.
"""
from __future__ import annotations

import io
from pathlib import Path

from html import escape

from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas

from app.factory import make_plugin_class

#: Fixed watermark text (D1): same fixed-semantics decision as jpg-watermark.
_WATERMARK_TEXT = "CONVERIGO"

#: Fixed metadata set (D1): pdf-metadata stamps Converigo provenance fields
#: onto the document and preserves every other existing info entry as-is.
_PRODUCER = "Converigo (https://converigo.com)"
_CREATOR = "Converigo (https://converigo.com)"

_UNLOCK_FAILURE_MESSAGE = (
    "PDF is password protected with a user password; Converigo can only "
    "unlock owner-restricted files that open without a password."
)

_MVP_NOTE = (
    "Converigo MVP: plain text extraction per page; this is NOT a "
    "layout-preserving conversion."
)


def _honest_unsupported(target_format: str, message: str):
    """Build the typed honest error for the API boundary.

    Mirrors the rar-extract precedent (app/plugins/archive/rar_extract.py):
    plugins raise ``UnsupportedConversionError`` (lazily imported to avoid
    a circular import) so the router answers 422 UNSUPPORTED_CONVERSION
    with a clear message instead of a generic 500 or fabricated output.
    """
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError("pdf", target_format, message=message)


def _open_pdf(source_path: Path, target_format: str) -> PdfReader:
    """Open a PDF, applying the empty-password unlock policy.

    Owner-restricted files (empty user password) are decrypted in place;
    files protected with a real user password raise the honest
    UnsupportedConversionError so the API keeps answering with
    422 UNSUPPORTED_CONVERSION.
    """
    try:
        reader = PdfReader(str(source_path))
    except Exception as exc:
        raise _honest_unsupported(
            target_format, f"PDF input could not be decoded: {exc}"
        ) from exc
    if reader.is_encrypted:
        try:
            if not reader.decrypt(""):
                raise RuntimeError("empty password rejected")
        except Exception as exc:
            raise _honest_unsupported(target_format, _UNLOCK_FAILURE_MESSAGE) from exc
    return reader


def _write_pdf(writer: PdfWriter, output_path: Path) -> Path:
    """Persist the rebuilt document; the output is never encrypted."""
    with output_path.open("wb") as handle:
        writer.write(handle)
    writer.close()
    return output_path


def _rebuild_writer(reader: PdfReader) -> PdfWriter:
    writer = PdfWriter()
    writer.append(reader, import_outline=True)
    return writer


def _extract_page_texts(reader: PdfReader) -> list[str]:
    """Per-page text extraction shared by the MVP HTML / MD converters."""
    return [(page.extract_text() or "").strip() for page in reader.pages]


def _convert_pdf_rotate(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    if not reader.pages:
        raise _honest_unsupported(target_format, "PDF has no pages to rotate.")
    writer = _rebuild_writer(reader)
    for page in writer.pages:
        page.rotate(90)  # D1 fixed semantics: 90 degrees clockwise.
    return _write_pdf(writer, working_root / f"{source_path.stem}_rotated.pdf")


def _convert_pdf_unlock(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    if not reader.pages:
        raise _honest_unsupported(target_format, "PDF has no pages to unlock.")
    writer = _rebuild_writer(reader)
    # PdfWriter never carries the reader's encryption dictionary over, so
    # this rewrite is the unlock: the output opens without any password.
    return _write_pdf(writer, working_root / f"{source_path.stem}_unlocked.pdf")


def _build_watermark_stamp(page_width: float, page_height: float):
    """Render the fixed CONVERIGO stamp (D1) as a one-page overlay PDF.

    Same fixed-semantics decision as jpg-watermark (F2): a semi-transparent
    grey "CONVERIGO" line at the bottom-right of the page, rendered with
    reportlab (already required) into an in-memory buffer - no new assets.
    """
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=(page_width, page_height))
    font_size = max(12.0, min(36.0, page_width / 12.0))
    canvas.setFont("Helvetica-Bold", font_size)
    canvas.setFillColorRGB(0.55, 0.55, 0.55)
    canvas.setFillAlpha(0.45)
    text_width = canvas.stringWidth(_WATERMARK_TEXT, "Helvetica-Bold", font_size)
    margin = 24.0
    canvas.drawString(page_width - text_width - margin, margin, _WATERMARK_TEXT)
    canvas.save()
    buffer.seek(0)
    return PdfReader(buffer).pages[0]


def _convert_pdf_watermark(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    if not reader.pages:
        raise _honest_unsupported(target_format, "PDF has no pages to watermark.")
    writer = _rebuild_writer(reader)
    for page in writer.pages:
        box = page.mediabox
        stamp = _build_watermark_stamp(float(box.width), float(box.height))
        page.merge_page(stamp)
    return _write_pdf(writer, working_root / f"{source_path.stem}_watermarked.pdf")


def _convert_pdf_metadata(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    if not reader.pages:
        raise _honest_unsupported(
            target_format, "PDF has no pages to stamp metadata onto."
        )
    writer = _rebuild_writer(reader)
    writer.add_metadata(
        {
            "/Producer": _PRODUCER,
            "/Creator": _CREATOR,
        }
    )
    return _write_pdf(writer, working_root / f"{source_path.stem}_metadata.pdf")


def _convert_pdf_to_html(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    texts = _extract_page_texts(reader)
    if not any(texts):
        raise _honest_unsupported(
            target_format,
            "PDF contains no extractable text (scanned/image-only PDFs are "
            "not supported by the text-extraction MVP converter).",
        )
    sections = []
    for index, text in enumerate(texts):
        paragraphs = "".join(
            f"    <p>{escape(line)}</p>\n"
            for line in text.splitlines()
            if line.strip()
        )
        sections.append(
            f'  <section class="page" id="page-{index + 1}">\n'
            f"    <h2>Page {index + 1}</h2>\n"
            f"{paragraphs}"
            "  </section>"
        )
    document = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        f"<title>{escape(source_path.stem)}</title>\n"
        f"<!-- {_MVP_NOTE} -->\n"
        "</head>\n"
        "<body>\n"
        f"{chr(10).join(sections)}\n"
        "</body>\n"
        "</html>\n"
    )
    output = working_root / f"{source_path.stem}.html"
    output.write_text(document, encoding="utf-8")
    return output


def _convert_pdf_to_md(
    plugin, source_path: Path, target_format: str, working_root: Path
) -> Path:
    reader = _open_pdf(source_path, target_format)
    texts = _extract_page_texts(reader)
    if not any(texts):
        raise _honest_unsupported(
            target_format,
            "PDF contains no extractable text (scanned/image-only PDFs are "
            "not supported by the text-extraction MVP converter).",
        )
    sections = []
    for index, text in enumerate(texts):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        if not lines:
            continue
        sections.append(f"## Page {index + 1}\n\n" + "\n\n".join(lines))
    document = "\n\n".join(sections) + "\n"
    output = working_root / f"{source_path.stem}.md"
    output.write_text(document, encoding="utf-8")
    return output


# ---------------------------------------------------------------------------
# Plugin classes (F0 factory; one thin declarative block per slug, metadata
# style identical to the F2 image-ops batch).
# ---------------------------------------------------------------------------

PdfRotatePlugin = make_plugin_class(
    slug="pdf-rotate",
    source_formats=["pdf"],
    target_formats=["pdf"],
    engine_hook=_convert_pdf_rotate,
    name="PDF Rotate",
    description="Rotate every page of a PDF document 90 degrees clockwise.",
    category="document",
    engine="document",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="90° Clockwise",
    icon="🔄",
    use_case="Best for fixing sideways scans without an editor.",
    seo_title="PDF Rotate Tool | Converigo",
    seo_description="Rotate PDF pages 90 degrees clockwise quickly and easily.",
)

PdfUnlockPlugin = make_plugin_class(
    slug="pdf-unlock",
    source_formats=["pdf"],
    target_formats=["pdf"],
    engine_hook=_convert_pdf_unlock,
    name="PDF Unlock",
    description="Remove owner restrictions from PDF files that open without a password.",
    category="document",
    engine="document",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Restriction-Free",
    icon="🔓",
    use_case="Best for opening owner-restricted PDFs for editing and printing.",
    seo_title="PDF Unlock Tool | Converigo",
    seo_description="Remove PDF owner restrictions quickly and easily.",
)

PdfWatermarkPlugin = make_plugin_class(
    slug="pdf-watermark",
    source_formats=["pdf"],
    target_formats=["pdf"],
    engine_hook=_convert_pdf_watermark,
    name="PDF Watermark",
    description="Stamp a semi-transparent CONVERIGO watermark on every PDF page.",
    category="document",
    engine="document",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Watermarked",
    icon="💧",
    use_case="Best for branding shared PDFs with a bottom-right stamp.",
    seo_title="PDF Watermark Tool | Converigo",
    seo_description="Add a watermark to PDF documents quickly and easily.",
)

PdfMetadataPlugin = make_plugin_class(
    slug="pdf-metadata",
    source_formats=["pdf"],
    target_formats=["pdf"],
    engine_hook=_convert_pdf_metadata,
    name="PDF Metadata",
    description="Stamp Converigo producer and creator metadata onto PDF documents.",
    category="document",
    engine="document",
    priority=70,
    quality=90,
    compatibility=95,
    estimated_saving=5,
    badge="Provenance",
    icon="🏷️",
    use_case="Best for tagging PDF provenance before archiving or sharing.",
    seo_title="PDF Metadata Tool | Converigo",
    seo_description="Stamp PDF producer and creator metadata quickly and easily.",
)

PdfToHTMLPlugin = make_plugin_class(
    slug="pdf-to-html",
    source_formats=["pdf"],
    target_formats=["html"],
    engine_hook=_convert_pdf_to_html,
    name="PDF to HTML",
    description=(
        "Extract the text content of PDF pages into a simple HTML file "
        "(text extraction MVP, not a layout-preserving conversion)."
    ),
    category="document",
    engine="document",
    # MVP rank: kept BELOW the mature pdf conversions (pdf-to-word/excel/
    # jpg at priority 80) so /recommend/pdf keeps recommending the mature
    # workhorses first and stays byte-identical to the baseline behaviour.
    priority=70,
    quality=70,
    compatibility=95,
    estimated_saving=10,
    badge="Text MVP",
    icon="🌐",
    use_case="Best for reusing PDF text content in web pages.",
    seo_title="PDF to HTML Converter | Converigo",
    seo_description="Extract PDF text into HTML format quickly and easily.",
)

PdfToMDPlugin = make_plugin_class(
    slug="pdf-to-md",
    source_formats=["pdf"],
    target_formats=["md"],
    engine_hook=_convert_pdf_to_md,
    name="PDF to Markdown",
    description=(
        "Extract the text content of PDF pages into a Markdown file "
        "(text extraction MVP, not a layout-preserving conversion)."
    ),
    category="document",
    engine="document",
    # MVP rank: see PdfToHTMLPlugin note (below the mature pdf conversions).
    priority=70,
    quality=70,
    compatibility=95,
    estimated_saving=10,
    badge="Text MVP",
    icon="📝",
    use_case="Best for reusing PDF text content in Markdown docs and wikis.",
    seo_title="PDF to Markdown Converter | Converigo",
    seo_description="Extract PDF text into Markdown format quickly and easily.",
)