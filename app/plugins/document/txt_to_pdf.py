"""
TXT -> PDF Plugin

Minimal plugin to convert plain text files to PDF using the
existing DocumentEngine rendering helper. Follows the existing
plugin pattern so it will be discovered by the PluginRegistry.
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin
from app.engines.document_engine import DocumentEngine


class TXTToPDFPlugin(ConverterPlugin):
    slug = "txt-to-pdf"
    name = "TXT to PDF"
    description = "Convert plain text (.txt) files into PDF documents."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["txt"]
    target_formats = ["pdf"]

    priority = 70
    quality = 70
    compatibility = 90

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("TXTToPDFPlugin only supports TXT -> PDF.")

        from app.core.settings import settings

        working_dir = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_dir.mkdir(parents=True, exist_ok=True)

        output_path = working_dir / f"{source_path.stem}.pdf"

        with source_path.open("r", encoding="utf-8", errors="replace") as f:
            lines = [line.rstrip('\n') for line in f.readlines()]

        engine = DocumentEngine()
        pdf_path = engine._render_text_lines_to_pdf(lines, output_path)

        if pdf_path.resolve() == source_path.resolve():
            raise RuntimeError("Plugin produced source path as output, aborting.")

        return pdf_path
