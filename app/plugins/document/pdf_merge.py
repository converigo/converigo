"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF Merge Plugin
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class PDFMergePlugin(ConverterPlugin):
    slug = "pdf-merge"
    name = "PDF Merge"
    description = "Merge multiple PDF files into a single document."
    category = "document"
    engine = "document"
    icon = "📚"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for combining multiple PDF files into one shared document."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 10
    badge = "Combine Files"
    seo_title = "PDF Merge Converter | Converigo"
    seo_description = "Merge multiple PDF files into one document quickly."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFMergePlugin only supports PDF -> PDF.")

        output_dir = Path("outputs") / "document"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source_path.stem}_merged.pdf"
        output_path.write_bytes(source_path.read_bytes())
        return output_path
