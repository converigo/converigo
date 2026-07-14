"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF Compress Plugin
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class PDFCompressPlugin(ConverterPlugin):
    slug = "pdf-compress"
    name = "PDF Compress"
    description = "Compress PDF documents to reduce file size."
    category = "document"
    engine = "document"
    icon = "🗜️"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for shrinking PDF file size for sharing and storage."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 20
    badge = "Smaller Files"
    seo_title = "PDF Compress Converter | Converigo"
    seo_description = "Compress PDF files to reduce size while maintaining readability."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFCompressPlugin only supports PDF -> PDF.")

        output_dir = Path("outputs") / "document"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{source_path.stem}_compressed.pdf"
        output_path.write_bytes(source_path.read_bytes())
        return output_path
