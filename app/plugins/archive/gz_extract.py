"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.1

GZ -> Extract Plugin

Batch 6 (VAR-33) fix: the archive engine extracts into a temporary
directory, but the /convert download route expects a single downloadable
FILE.  Mirroring the Batch 5 zip-extract pattern, this plugin now returns
a single servable file, deterministic per input type:
- standalone ``.gz`` (e.g. ``notes.txt.gz``): the engine already wrote
  exactly one decompressed file -> return that file directly;
- ``.tar.gz`` / ``.tgz``: the engine extracted the full tar tree ->
  repackage it into one downloadable TAR archive (stdlib ``tarfile``,
  clean POSIX member names) — the decompressed-archive form.
"""

import tarfile
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
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "GZExtractPlugin only supports GZIP extraction."
            )

        # Working directory mirrors the Batch 5 zip-extract pattern: the
        # engine extracts into ``<working_root>/archive/<stem>/`` and returns
        # that directory.  Behavior is deterministic per input type — see
        # the module docstring.
        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "archive")
        working_root.mkdir(parents=True, exist_ok=True)

        engine = ArchiveEngine()
        extract_dir = await engine.convert(
            source_path=source_path,
            target_format=target_format,
            temp_dir=working_root,
        )

        produced = sorted(p for p in extract_dir.rglob("*") if p.is_file())
        if not produced:
            raise RuntimeError("GZIP extraction produced no files.")

        is_tar_gz = source_path.name.lower().endswith((".tar.gz", ".tgz"))
        if len(produced) == 1 and not is_tar_gz:
            # Standalone .gz: return the single decompressed file as-is.
            return produced[0]

        output_path = working_root / f"{self._archive_base_name(source_path)}.tar"
        with tarfile.open(output_path, "w") as tar_ref:
            for member in produced:
                # Clean POSIX member names (``shutil.make_archive`` produced
                # ``./``-prefixed entries on Windows during the Gate 1 probe).
                tar_ref.add(
                    member,
                    arcname=member.relative_to(extract_dir).as_posix(),
                )

        if output_path.stat().st_size == 0:
            raise RuntimeError("GZIP extraction produced an empty archive.")

        return output_path

    @staticmethod
    def _archive_base_name(source_path: Path) -> str:
        name = source_path.name
        lower = name.lower()
        if lower.endswith(".tar.gz"):
            return name[: -len(".tar.gz")]
        if lower.endswith(".tgz"):
            return name[: -len(".tgz")]
        return source_path.stem
