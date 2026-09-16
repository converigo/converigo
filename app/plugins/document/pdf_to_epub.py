"""
Project : Converigo
Version : 1.0.0

PDF -> EPUB converter (text-only MVP).

The plugin owns three things and nothing else:

1. Registration of the honest ``(pdf, epub)`` pair so the D5 target authority
   can offer it (``advertisable`` stays True because the converter really
   delivers; no fabricated capability, no JSON-only entry).
2. Offloading the blocking extraction to a worker thread with
   ``asyncio.to_thread``.  MuPDF walks every page inside a C call, so running it
   in this coroutine would stall the event loop for the whole document - the
   same rule html-to-pdf follows.
3. Translating :class:`PdfToEpubError` into the two sanctioned API outcomes:
   an input-side refusal becomes the typed ``UnsupportedConversionError`` (422
   UNSUPPORTED_CONVERSION with the static message), and everything else becomes
   a ``RuntimeError`` that ConversionService folds into the generic safe failure.

The wording that reaches a client never contains a path, an exception text, a
library name or a page of the document; it comes from the runner's literal
table.  All ceilings and the container validation live in
app/factory/pdf_epub_runner.py.
"""

from __future__ import annotations

import asyncio
import logging
import re
from pathlib import Path

from app.factory.pdf_epub_runner import PdfToEpubError, convert_pdf_to_epub
from app.plugins.base import ConverterPlugin

logger = logging.getLogger(__name__)

#: Sanitises the stem used for the served filename.  Uploads are already stored
#: under a server-generated uuid (app/services/upload_service.py), so this is a
#: second line of defence for any other caller: only a short alphanumeric token
#: can ever reach the filesystem.
_SAFE_STEM_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")

OUTPUT_FILE_STEM = "converted"


def _safe_output_name(source_path: Path) -> str:
    stem = source_path.stem
    if not _SAFE_STEM_RE.fullmatch(stem):
        stem = OUTPUT_FILE_STEM
    return f"{stem}.epub"


class PDFToEPUBPlugin(ConverterPlugin):
    slug = "pdf-to-epub"
    name = "PDF to EPUB"
    description = (
        "Convert a text PDF into an EPUB ebook with page-grouped chapters "
        "(text extraction MVP, not a layout-preserving conversion)."
    )
    category = "document"
    engine = "document"
    icon = "📚"

    source_formats = ["pdf"]
    target_formats = ["epub"]

    goal = "conversion"
    use_case = (
        "Best for reading a text PDF on an e-reader: the extracted text is "
        "rebuilt as an EPUB with one chapter per group of pages."
    )
    # Deliberately below the mature PDF conversions (pdf-to-word / -excel /
    # -jpg at 80) and level with the other MVP extractors, so /recommend/pdf
    # keeps ranking the established workhorses first.
    priority = 70
    quality = 80
    compatibility = 85
    estimated_saving = 8
    badge = "Ebook MVP"
    color = "purple"

    seo_title = "PDF to EPUB Converter | Converigo"
    seo_description = (
        "Convert a text PDF into an EPUB ebook online. Real extracted text, "
        "page-grouped chapters and the processing limits stated up front."
    )

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        source_path = Path(source_path)

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToEPUBPlugin only supports PDF -> EPUB.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_root.mkdir(parents=True, exist_ok=True)
        output_path = working_root / _safe_output_name(source_path)

        try:
            # Blocking by design on the thread side; the loop stays free.
            report = await asyncio.to_thread(
                convert_pdf_to_epub, source_path, output_path
            )
        except PdfToEpubError as exc:
            logger.warning(
                "pdf-to-epub refused kind=%s detail=%s", exc.kind, exc.detail
            )
            if exc.is_input_refusal:
                from app.services.conversion_service import UnsupportedConversionError

                raise UnsupportedConversionError(
                    "pdf", target_format, message=exc.client_message
                ) from exc
            # Resource, timeout or internal-validation failure: a static
            # sentence in, the generic safe 500 out.  Nothing from the runner's
            # internals travels past this line.
            raise RuntimeError(exc.client_message) from exc

        logger.info(
            "pdf-to-epub served pages=%s chapters=%s chars=%s bytes=%s",
            report.pages,
            report.chapters,
            report.chars,
            report.package_bytes,
        )

        if output_path.resolve() == source_path.resolve():  # pragma: no cover
            raise RuntimeError("Plugin produced source path as output, aborting.")

        return output_path
