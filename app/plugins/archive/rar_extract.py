"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.1

RAR -> Extract Plugin

P2.4-F2 (Option 1) fix: the archive engine extracts into a temporary
directory but the /convert download route expects a single downloadable
FILE.  This plugin forwards the request-local temp_dir to the engine and
repackages the extracted directory into a single downloadable ZIP file
(stdlib ``shutil.make_archive``, no new dependencies) so the download
route can deliver the result.  ArchiveEngine is unchanged.

NOTE: RAR extraction still relies on the ``unrar`` binary
(``archive_engine.py``), which is provisioned in Docker
(``p7zip-full`` + ``unrar-free``) but absent on the host dev box.  The
adapter-level fix (A1+A2) is applied here, but functional RAR
verification is blocked until a valid RAR sample and a guaranteed
``unrar`` binary are available.
"""

import shutil
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
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "RARExtractPlugin only supports RAR extraction."
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
            raise RuntimeError("RAR extraction produced an empty archive.")

        return output_path
