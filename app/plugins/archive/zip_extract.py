"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.1

ZIP -> Extract Plugin

P2.4-F2 (Option 1) fix: the archive engine extracts into a temporary
directory but the /convert download route expects a single downloadable
FILE.  This plugin now forwards the request-local temp_dir to the engine
and packages the extracted directory into a single ZIP file (stdlib
``shutil.make_archive``, no new dependencies) so the normal
upload -> convert -> download pipeline works.  Mirrors the Batch 5
zip-extract pattern.  ArchiveEngine is unchanged.
"""

import shutil
from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class ZIPExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "zip-extract"
    name = "ZIP Extract"
    description = "Extract files from ZIP archives safely."
    category = "archive"
    engine = "archive"
    icon = "📦"

    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True
    featured = True

    # ==========================================
    # Formats
    # ==========================================

    source_formats = ["zip"]
    target_formats = ["zip"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from ZIP archives quickly."
    priority = 95
    quality = 95
    compatibility = 100
    estimated_saving = 0
    badge = "Most Popular"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "ZIP File Extractor | Converigo"
    seo_description = "Extract files from ZIP archives online. Fast, free, and secure."

    # ==========================================
    # Conversion
    # ==========================================

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "ZIPExtractPlugin only supports ZIP extraction."
            )

        # Working root is request-local: the service passes temp_dir
        # (settings.TEMP_DIR/<conversion_id>) and output_dir
        # (settings.OUTPUT_DIR/<conversion_id>).  The engine extracts into
        # ``<working_root>/archive/<stem>/`` and returns that directory;
        # we package it into a ZIP file so the download route (which serves
        # files, not directories) can deliver the result.
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "archive")
        working_root.mkdir(parents=True, exist_ok=True)

        engine = ArchiveEngine()
        extract_dir = await engine.convert(
            source_path=source_path,
            target_format=target_format,
            temp_dir=working_root,
        )

        zip_base = working_root / source_path.stem
        zip_path = Path(
            shutil.make_archive(str(zip_base), "zip", root_dir=str(extract_dir))
        )

        if not zip_path.exists() or zip_path.stat().st_size == 0:
            raise RuntimeError("ZIP extraction produced an empty archive.")

        return zip_path
