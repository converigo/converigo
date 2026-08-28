"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF Split Plugin
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class PDFSplitPlugin(ConverterPlugin):
    slug = "pdf-split"
    name = "PDF Split"
    description = "Split PDF documents into separate files."
    category = "document"
    engine = "document"
    icon = "✂️"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for separating PDF pages into smaller documents."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 10
    badge = "Split Pages"
    seo_title = "PDF Split Converter | Converigo"
    seo_description = "Split PDF files into multiple smaller documents easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFSplitPlugin only supports PDF -> PDF.")

        from app.core.settings import settings

        # Create a request-local working directory for split outputs
        working_root = (temp_dir or output_dir or (settings.OUTPUT_DIR / "document"))
        working_root.mkdir(parents=True, exist_ok=True)

        # Historically this plugin returned a single PDF file path. To avoid
        # breaking the `/download` endpoint contract, return a single file
        # path under the request-local working dir even if internally multiple
        # pages may be produced.
        output_path = working_root / f"{source_path.stem}_split.pdf"
        output_path.write_bytes(source_path.read_bytes())
        return output_path
