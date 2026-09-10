"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.1

7Z -> Extract Plugin

P2.4-F2 (Option 1) fix: the archive engine extracts into a temporary
directory but the /convert download route expects a single downloadable
FILE.  This plugin forwards the request-local temp_dir to the engine and
repackages the extracted directory into a single downloadable ZIP file
(stdlib ``shutil.make_archive``, no new dependencies) so the download
route can deliver the result.  ArchiveEngine is unchanged.

NOTE: 7Z extraction still relies on the ``7z`` binary
(``archive_engine.py``), which is provisioned in Docker
(``p7zip-full``) but absent on the host dev box, and no valid ``.7z``
sample exists in the repo (all ``*.7z`` are 14-byte stubs).  The
adapter-level fix (A1+A2) is applied here, but functional 7Z
verification is blocked until a valid sample and a guaranteed ``7z``
binary are available.  ``7z-extract`` is also listed in
``NON_PRODUCTION_READY_SLUGS``.
"""

import shutil
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
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "SevenZExtractPlugin only supports 7Z extraction."
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

        archive_base = working_root / source_path.stem
        output_path = Path(
            shutil.make_archive(str(archive_base), "zip", root_dir=str(extract_dir))
        )

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("7Z extraction produced an empty archive.")

        return output_path
