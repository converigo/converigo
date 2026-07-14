"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.0

GZ -> Extract Plugin
"""

from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class GZExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "gz-extract"
    name = "GZ Extract"
    description = "Extract files from GZIP archives safely."
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

    source_formats = ["gz", "gzip"]
    target_formats = ["gz", "gzip"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from GZIP archives quickly."
    priority = 65
    quality = 95
    compatibility = 90
    estimated_saving = 0
    badge = "GZIP Expert"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "GZIP File Extractor | Converigo"
    seo_description = "Extract files from GZIP archives online. Fast, free, and secure."

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
                "GZExtractPlugin only supports GZIP extraction."
            )

        engine = ArchiveEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
