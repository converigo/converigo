"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 4.0.0

RAR -> Extract Plugin

Batch 6 (VAR-34, Gate 2): the archive engine now extracts RAR (RAR4 and
RAR5) in-process via ``libarchive-c`` instead of shelling out to
``unrar``.  Mirroring the Batch 6 tar/gz-extract pattern, this plugin
returns a single servable FILE (the /convert download route serves
files, not directories):

- exactly one extracted file  -> return that file directly;
- multiple extracted files    -> repackage the extracted tree into one
  downloadable TAR archive (stdlib ``tarfile``, clean POSIX member
  names) — the decompressed-archive form (libarchive cannot *write*
  RAR, so a TAR container is the deterministic servable output).

Honest errors: password-protected, multi-volume, and non-RAR/unsupported
content raise typed engine errors which are translated here into
``UnsupportedConversionError`` so the API answers 422
UNSUPPORTED_CONVERSION with a clear message instead of a generic 500.
"""

import tarfile
from pathlib import Path

from app.engines.archive_engine import (
    ArchiveEngine,
    RarEncryptedError,
    RarMultiVolumeError,
    RarUnsupportedContentError,
)
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

        # Working directory mirrors the tar/gz-extract pattern: the engine
        # extracts into ``<working_root>/archive/<stem>/`` and returns that
        # directory; we package the result into a single servable file.
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "archive")
        working_root.mkdir(parents=True, exist_ok=True)

        try:
            engine_output = await ArchiveEngine().convert(
                source_path=source_path,
                target_format=target_format,
                temp_dir=working_root,
            )
        except (RarEncryptedError, RarMultiVolumeError, RarUnsupportedContentError) as exc:
            # Honest-error contract: surface a clear, specific message via
            # the standard 422 UNSUPPORTED_CONVERSION path instead of a
            # generic conversion failure (500).
            from app.services.conversion_service import UnsupportedConversionError

            raise UnsupportedConversionError("rar", "rar", message=str(exc)) from exc

        produced = sorted(p for p in engine_output.rglob("*") if p.is_file())
        if not produced:
            raise RuntimeError("RAR extraction produced no files.")

        if len(produced) == 1:
            # Single-member RAR: return the extracted file as-is.
            return produced[0]

        output_path = working_root / f"{source_path.stem}.tar"
        with tarfile.open(output_path, "w") as tar_ref:
            for member in produced:
                # Clean POSIX member names (shutil.make_archive produced
                # ``./``-prefixed entries on Windows during the Gate 1 probe).
                tar_ref.add(
                    member,
                    arcname=member.relative_to(engine_output).as_posix(),
                )

        if output_path.stat().st_size == 0:
            raise RuntimeError("RAR extraction produced an empty archive.")

        return output_path

