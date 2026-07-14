"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.0

RAR -> Extract Plugin
"""

from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class RARExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "rar-extract"
    name = "RAR Extract"
    description = "Extract files from RAR archives safely."
    category = "archive"
    engine = "archive"
    icon = "📦"

    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True
    featured = False

    # ==========================================
    # Formats
    # ==========================================

    source_formats = ["rar"]
    target_formats = ["rar"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from RAR archives quickly."
    priority = 85
    quality = 95
    compatibility = 95
    estimated_saving = 0
    badge = "RAR Expert"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "RAR File Extractor | Converigo"
    seo_description = "Extract files from RAR archives online. Fast, free, and secure."

    # ==========================================
    # Conversion
    # ==========================================

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "RARExtractPlugin only supports RAR extraction."
            )

        engine = ArchiveEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
