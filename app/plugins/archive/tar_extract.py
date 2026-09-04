"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.1

TAR -> Extract Plugin

Batch 6 (VAR-33) fix: the archive engine extracts into a temporary
directory, but the /convert download route expects a single downloadable
FILE.  This plugin now repackages the extracted directory into a single
TAR archive (stdlib ``tarfile`` with clean POSIX member names —
``shutil.make_archive`` emitted ``./``-prefixed entries on Windows during
the Gate 1 probe) and returns that file so the normal upload -> convert
-> download pipeline works.  Mirrors the Batch 5 zip-extract pattern.
"""

import tarfile
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
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "TARExtractPlugin only supports TAR extraction."
            )

        # Working directory mirrors the Batch 5 zip-extract pattern: the
        # engine extracts into ``<working_root>/archive/<stem>/`` and returns
        # that directory; we repackage it into a single TAR file so the
        # download route (which serves files, not directories) can deliver
        # the result.
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "archive")
        working_root.mkdir(parents=True, exist_ok=True)

        engine = ArchiveEngine()
        extract_dir = await engine.convert(
            source_path=source_path,
            target_format=target_format,
            temp_dir=working_root,
        )

        members = sorted(p for p in extract_dir.rglob("*") if p.is_file())
        if not members:
            raise RuntimeError("TAR extraction produced no files.")

        output_path = working_root / f"{source_path.stem}.tar"
        with tarfile.open(output_path, "w") as tar_ref:
            for member in members:
                # Clean POSIX member names (``shutil.make_archive`` produced
                # ``./``-prefixed entries on Windows during the Gate 1 probe).
                tar_ref.add(
                    member,
                    arcname=member.relative_to(extract_dir).as_posix(),
                )

        if output_path.stat().st_size == 0:
            raise RuntimeError("TAR extraction produced an empty archive.")

        return output_path
