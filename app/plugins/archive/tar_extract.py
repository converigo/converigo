"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.0

TAR -> Extract Plugin
"""

from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class TARExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "tar-extract"
    name = "TAR Extract"
    description = "Extract files from TAR archives safely."
    category = "archive"
    engine = "archive"
    icon = "📦"

    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = False
    featured = False

    # ==========================================
    # Formats
    # ==========================================

    source_formats = ["tar"]
    target_formats = ["tar"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from TAR archives quickly."
    priority = 70
    quality = 95
    compatibility = 90
    estimated_saving = 0
    badge = "TAR Expert"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "TAR File Extractor | Converigo"
    seo_description = "Extract files from TAR archives online. Fast, free, and secure."

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
                "TARExtractPlugin only supports TAR extraction."
            )

        engine = ArchiveEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
