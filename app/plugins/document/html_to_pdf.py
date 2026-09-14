"""
Project : Converigo
Version : 1.0.0

HTML -> PDF converter.

Renders HTML with MuPDF's Story layout engine inside a *child process*
(app/factory/html_render_worker.py) and validates what comes back.  This
plugin owns none of that: it routes, offloads, and translates failures.

Why the three things below are non-negotiable:

1. ``asyncio.to_thread`` - the runner blocks on a subprocess that may take
   seconds.  Calling it directly from this ``async def`` would stall every
   other request on the event loop, so it is offloaded here and nowhere
   else.  The worker is never re-used between conversions; each call spawns
   its own child, so a crash or timeout cannot poison the next document.
2. Every ``HtmlRenderError`` becomes the honest 422
   ``UnsupportedConversionError`` carrying ``client_message`` only.  The
   server-side ``detail`` (exit codes, byte counts, child diagnostics) is
   logged and never reaches the client.
3. A refused PDF is deleted by the runner before it raises, so no partial
   output can be served.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.factory.html_pdf_runner import (
    HtmlRenderError,
    render_html_document,
)
from app.plugins.base import ConverterPlugin

logger = logging.getLogger(__name__)


def _unsupported(source: str, target: str, message: str) -> Exception:
    """Lazily build the honest-422 error (html-to-csv lazy-import precedent)."""
    from app.services.conversion_service import UnsupportedConversionError

    return UnsupportedConversionError(source, target, message)


class HTMLToPDFPlugin(ConverterPlugin):
    slug = "html-to-pdf"
    name = "HTML to PDF"
    description = "Convert HTML documents into paginated PDF documents."
    category = "document"
    engine = "document"
    icon = "\U0001F9FE"

    source_formats = ["html"]
    target_formats = ["pdf"]

    goal = "conversion"
    use_case = (
        "Best for turning a saved web page or an HTML report export into a "
        "paginated PDF that prints the same everywhere."
    )

    priority = 70
    quality = 85
    compatibility = 80
    estimated_saving = 6
    badge = "HTML Renderer"
    color = "blue"

    seo_title = "HTML to PDF Converter | Converigo"
    seo_description = (
        "Convert HTML to PDF online for free. Real pagination and text that "
        "stays selectable, with the rendering limits stated up front."
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
            raise RuntimeError("HTMLToPDFPlugin only supports HTML -> PDF.")

        from app.core.settings import settings

        working_dir = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_dir.mkdir(parents=True, exist_ok=True)

        output_path = working_dir / f"{source_path.stem}.pdf"

        try:
            # Blocking by design on the thread side; the loop stays free.
            outcome, report = await asyncio.to_thread(
                render_html_document, source_path, output_path
            )
        except HtmlRenderError as exc:
            # detail is server-side only (byte counts, exit status, child
            # stderr presence); the client gets the static client_message.
            logger.warning(
                "html-to-pdf refused error=%s detail=%s",
                type(exc).__name__,
                exc.detail,
            )
            raise _unsupported("html", "pdf", exc.client_message) from exc

        logger.info(
            "html-to-pdf served pid=%s pages=%s bytes=%s ink=%s",
            outcome.pid,
            report.pages,
            outcome.output_bytes,
            report.ink_pixels,
        )

        if output_path.resolve() == source_path.resolve():
            raise RuntimeError("Plugin produced source path as output, aborting.")

        return output_path
