"""
Archive Engine for Converigo

Handles extraction of archive formats: ZIP, RAR, 7Z, TAR, GZ
"""

from __future__ import annotations

import gzip
import shutil
import tarfile
import zipfile
from pathlib import Path

from app.engines.base_engine import BaseEngine


def _is_within_directory(directory: Path, target: Path) -> bool:
    try:
        directory_resolved = directory.resolve()
        target_resolved = target.resolve()
        return directory_resolved == target_resolved or directory_resolved in target_resolved.parents
    except Exception:
        return False


def _validate_member_destination(extract_path: Path, member_name: str) -> None:
    # Block absolute paths
    if member_name.startswith("/") or member_name.startswith("\\"):
        raise RuntimeError("Archive extraction blocked: absolute path entry")

    # Normalize separators and strip leading traversal
    normalized = member_name.replace("\\", "/").lstrip("/")

    # Reject traversal components
    parts = [p for p in normalized.split("/") if p not in ("", ".")]
    if any(p == ".." for p in parts):
        raise RuntimeError("Archive extraction blocked: path traversal entry")

    destination = extract_path / Path(*parts)
    if not _is_within_directory(extract_path, destination):
        raise RuntimeError("Archive extraction blocked: unsafe member destination")


class ArchiveEngine(BaseEngine):
    """Engine for extracting archive files."""

    ENGINE_NAME = "archive"

    # Extraction limits (zip-bomb / abuse prevention)
    MAX_FILES = 200
    MAX_TOTAL_SIZE_BYTES = 50 * 1024 * 1024  # 50 MiB
    MAX_SINGLE_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MiB

    SUPPORTED_FORMATS = [
        "zip",
        "rar",
        "7z",
        "tar",
        "gz",
        "gzip",
        "tar.gz",
        "tgz",
    ]

    def _validate_zip_member(self, extract_path: Path, member_name: str) -> None:
        _validate_member_destination(extract_path, member_name)

    def _extract_zip_member(
        self,
        zip_ref: zipfile.ZipFile,
        extract_path: Path,
        member: zipfile.ZipInfo,
    ) -> None:
        # Normalize like validation expects.
        filename = str(member.filename).replace("\\", "/").lstrip("/")

        # Skip directories
        if member.is_dir() or filename.endswith("/"):
            (extract_path / Path(filename)).mkdir(parents=True, exist_ok=True)
            return

        destination = extract_path / Path(filename)
        destination.parent.mkdir(parents=True, exist_ok=True)

        with zip_ref.open(member, "r") as src, open(destination, "wb") as dst:
            shutil.copyfileobj(src, dst)

    def _extract_tarfile(self, tar_ref: tarfile.TarFile, extract_path: Path) -> None:
        members = tar_ref.getmembers()

        if len(members) > self.MAX_FILES:
            raise RuntimeError("Archive extraction blocked: MAX_FILES exceeded")

        total_size = 0
        for m in members:
            size = getattr(m, "size", 0) or 0
            total_size += max(0, size)
            if size > self.MAX_SINGLE_FILE_SIZE_BYTES:
                raise RuntimeError("Archive extraction blocked: MAX_SINGLE_FILE_SIZE_BYTES exceeded")

        if total_size > self.MAX_TOTAL_SIZE_BYTES:
            raise RuntimeError("Archive extraction blocked: MAX_TOTAL_SIZE_BYTES exceeded")

        # Validate paths first
        for m in members:
            _validate_member_destination(extract_path, getattr(m, "name", ""))

        # Extraction now safe due to validation.
        tar_ref.extractall(path=extract_path)

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        """Extract archive to output directory (hardened against traversal + zip bombs)."""

        suffix = source_path.suffix.lower()
        stem = source_path.stem

        # Handle double extensions like .tar.gz
        if source_path.name.endswith(".tar.gz") or source_path.name.endswith(".tgz"):
            extract_dir_name = source_path.name.replace(".tar.gz", "").replace(".tgz", "")
        else:
            extract_dir_name = stem

        output_dir = Path("outputs") / "archive"
        output_dir.mkdir(parents=True, exist_ok=True)

        extract_path = output_dir / extract_dir_name
        extract_path.mkdir(parents=True, exist_ok=True)

        try:
            if suffix == ".zip":
                with zipfile.ZipFile(source_path, "r") as zip_ref:
                    members = zip_ref.infolist()

                    # Limits
                    if len(members) > self.MAX_FILES:
                        raise RuntimeError("Archive extraction blocked: MAX_FILES exceeded")

                    total_size = sum(max(0, m.file_size) for m in members)
                    if total_size > self.MAX_TOTAL_SIZE_BYTES:
                        raise RuntimeError("Archive extraction blocked: MAX_TOTAL_SIZE_BYTES exceeded")

                    for m in members:
                        if m.file_size > self.MAX_SINGLE_FILE_SIZE_BYTES:
                            raise RuntimeError("Archive extraction blocked: MAX_SINGLE_FILE_SIZE_BYTES exceeded")
                        self._validate_zip_member(extract_path, m.filename)

                    for m in members:
                        self._extract_zip_member(zip_ref, extract_path, m)

            elif suffix == ".rar":
                # RAR extraction requires unrar executable.
                # We do not refactor architecture; existing behavior preserved.
                import subprocess

                try:
                    subprocess.run(
                        ["unrar", "x", str(source_path), str(extract_path)],
                        check=True,
                        capture_output=True,
                    )
                except FileNotFoundError:
                    raise RuntimeError("unrar is not installed. Please install WinRAR or unrar utility.")

            elif suffix == ".7z":
                # 7Z extraction requires 7z executable.
                import subprocess

                try:
                    subprocess.run(
                        ["7z", "x", str(source_path), f"-o{extract_path}"],
                        check=True,
                        capture_output=True,
                    )
                except FileNotFoundError:
                    raise RuntimeError("7z is not installed. Please install 7-Zip or p7zip utility.")

            elif suffix in {".tar", ".tgz", ".gz"}:
                if source_path.name.endswith(".tar.gz") or source_path.name.endswith(".tgz"):
                    with tarfile.open(source_path, "r:gz") as tar_ref:
                        self._extract_tarfile(tar_ref, extract_path)
                elif suffix == ".tar":
                    with tarfile.open(source_path, "r") as tar_ref:
                        self._extract_tarfile(tar_ref, extract_path)
                elif suffix == ".gz":
                    # Standalone .gz -> single file decompress
                    output_file = extract_path / stem
                    with gzip.open(source_path, "rb") as f_in:
                        with open(output_file, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)

            else:
                raise RuntimeError(f"Unsupported archive format: {suffix}")

            return extract_path

        except Exception as e:
            if extract_path.exists():
                shutil.rmtree(extract_path)
            raise RuntimeError(f"Archive extraction failed: {str(e)}")

