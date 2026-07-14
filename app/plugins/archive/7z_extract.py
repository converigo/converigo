"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.0

7Z -> Extract Plugin
"""

from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class SevenZExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "7z-extract"
    name = "7Z Extract"
    description = "Extract files from 7Z archives safely."
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

    source_formats = ["7z"]
    target_formats = ["7z"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from 7Z archives quickly."
    priority = 80
    quality = 95
    compatibility = 90
    estimated_saving = 0
    badge = "7Z Expert"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "7Z File Extractor | Converigo"
    seo_description = "Extract files from 7Z archives online. Fast, free, and secure."

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
                "SevenZExtractPlugin only supports 7Z extraction."
            )

        engine = ArchiveEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
