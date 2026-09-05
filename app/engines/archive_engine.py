"""
Archive Engine for Converigo

Handles extraction of archive formats: ZIP, RAR, 7Z, TAR, GZ

Batch 6 (VAR-34, Gate 2): the RAR path was migrated from a subprocess
``unrar`` call to in-process extraction via ``libarchive-c`` (RAR4 and
RAR5 readers).  The RAR path enforces the same extraction limits as the
zip/tar paths, validates every member destination against path
traversal, and raises honest typed errors (RarEncryptedError,
RarMultiVolumeError, RarUnsupportedContentError) which the rar-extract
plugin translates into HTTP 422 UNSUPPORTED_CONVERSION with a clear
message instead of a generic 500.
"""

from __future__ import annotations

import gzip
import shutil
import struct
import tarfile
import zipfile
from pathlib import Path

from app.core.settings import settings
from app.engines.base_engine import BaseEngine


class RarEncryptedError(RuntimeError):
    """The RAR archive (or some of its members) is password-protected."""


class RarMultiVolumeError(RuntimeError):
    """The RAR file is a part of a multi-volume (split) archive set."""


class RarUnsupportedContentError(RuntimeError):
    """The file is not a RAR archive or contains unreadable content."""


_RAR4_SIGNATURE = b"Rar!\x1a\x07\x00"
_RAR5_SIGNATURE = b"Rar!\x1a\x07\x01\x00"


def _read_vint(data: bytes, pos: int) -> tuple[int, int]:
    """Read one RAR5 variable-length integer, returning (value, next_pos)."""
    value = 0
    shift = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, pos
        shift += 7
    raise ValueError("truncated vint")


def _rar_is_multivolume(data: bytes) -> bool | None:
    """Best-effort parse of the RAR main archive header volume flag.

    Returns True/False when the main archive header could be parsed,
    None when the signature/headers are unreadable.  Detecting split
    archives up-front matters because the RAR5 reader otherwise yields
    silent empty output for continuation volumes.
    """
    if data[:7] == _RAR4_SIGNATURE:
        # RAR4 main header: crc(2) type(1) flags(2) size(2); MHD_VOLUME = bit 0x0001.
        if len(data) < 12:
            return None
        (flags,) = struct.unpack_from("<H", data, 10)
        return bool(flags & 0x0001)
    if data[:8] == _RAR5_SIGNATURE:
        # RAR5 main header: crc32(4) header_size(vint) type(vint) flags(vint)
        #   [extra_size(vint)] [data_size(vint)] archive_flags(vint)
        # with VOLUME = bit 0x0001 in archive_flags.
        try:
            pos = 12
            _header_size, pos = _read_vint(data, pos)
            header_type, pos = _read_vint(data, pos)
            header_flags, pos = _read_vint(data, pos)
            if header_type != 1:  # first block is not the main archive header
                return None
            if header_flags & 0x0001:  # extra area present
                _extra_size, pos = _read_vint(data, pos)
            if header_flags & 0x0002:  # data area present
                _data_size, pos = _read_vint(data, pos)
            archive_flags, pos = _read_vint(data, pos)
            return bool(archive_flags & 0x0001)
        except (ValueError, IndexError, struct.error):
            return None
    return None


def _load_rar_ffi_helpers() -> tuple:
    """Bind libarchive C symbols that libarchive-c does not wrap.

    Returns ``(format_name_fn, entry_is_encrypted_fn)``; either entry is
    None when the native library does not export it (very old builds).
    Both exist in Debian bookworm's libarchive 3.6.2 (the production
    image) and in the locally verified 3.8.x build.
    """
    import ctypes

    from libarchive import ffi

    format_name_fn = None
    is_encrypted_fn = None
    try:
        format_name_fn = ctypes.CFUNCTYPE(ctypes.c_char_p, ctypes.c_void_p)(
            ("archive_format_name", ffi.libarchive)
        )
    except (AttributeError, OSError):
        pass
    try:
        is_encrypted_fn = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p)(
            ("archive_entry_is_encrypted", ffi.libarchive)
        )
    except (AttributeError, OSError):
        pass
    return format_name_fn, is_encrypted_fn



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

    @staticmethod
    def _copy_rar_entry(entry, destination: Path) -> int:
        """Stream one RAR member to disk, enforcing a hard single-file cap."""
        written = 0
        hard_cap = ArchiveEngine.MAX_SINGLE_FILE_SIZE_BYTES
        with open(destination, "wb") as dst:
            for block in entry.get_blocks():
                if written + len(block) > hard_cap:
                    raise RuntimeError(
                        "Archive extraction blocked: MAX_SINGLE_FILE_SIZE_BYTES exceeded"
                    )
                dst.write(block)
                written += len(block)
        return written

    def _extract_rar_members(self, source_path: Path, extract_path: Path) -> None:
        """Extract RAR (RAR4 + RAR5) in-process via libarchive-c (VAR-34).

        Enforces the same limits as the zip/tar paths (MAX_FILES,
        MAX_TOTAL_SIZE_BYTES, MAX_SINGLE_FILE_SIZE_BYTES), validates every
        member destination against path traversal, and raises honest typed
        errors for password-protected / multi-volume / non-RAR input
        instead of failing silently or producing partial output.
        """
        # Import lazily so the rest of the archive engine (zip/tar/gz)
        # keeps working on hosts where libarchive-c is not installed.
        try:
            import libarchive
        except ImportError as exc:
            raise RuntimeError(
                "libarchive-c is not installed; RAR extraction is unavailable."
            ) from exc

        format_name_fn, is_encrypted_fn = _load_rar_ffi_helpers()

        # Multi-volume sets must be rejected up-front: the RAR5 reader
        # yields silent empty output for continuation volumes, and a first
        # volume alone can never be fully extracted. Only the header is
        # needed - do not buffer the whole archive for this check.
        with open(source_path, "rb") as handle:
            raw = handle.read(64)
        if _rar_is_multivolume(raw) is True:
            raise RarMultiVolumeError(
                "RAR extraction blocked: multi-volume (split) RAR archives are "
                "not supported. Please provide a single-volume RAR archive."
            )

        # Gate on the RAR signature so garbage/placeholder files and
        # other archive formats mislabeled as .rar surface as honest
        # errors instead of entering the generic read path.
        if not (raw[:7] == _RAR4_SIGNATURE or raw[:8] == _RAR5_SIGNATURE):
            raise RarUnsupportedContentError(
                "The uploaded file is not a valid RAR archive."
            )

        files = 0
        written = 0
        try:
            with libarchive.file_reader(str(source_path)) as archive:
                for entry in archive:
                    # The RAR reader must be the one handling this file:
                    # libarchive transparently falls back to other formats
                    # (e.g. ZIP), which would mislabel the conversion.
                    if format_name_fn is not None:
                        fmt = format_name_fn(entry._archive_p) or b""
                        if not fmt.startswith((b"RAR", b"rar")):
                            raise RarUnsupportedContentError(
                                "The uploaded file is not a RAR archive."
                            )

                    # Member/header encryption flag (RAR4 + RAR5). Detected
                    # before any data read — RAR4 data errors for encrypted
                    # members are otherwise indistinguishable from garbage.
                    if is_encrypted_fn is not None and is_encrypted_fn(entry._entry_p):
                        raise RarEncryptedError(
                            "RAR extraction blocked: the archive is "
                            "password-protected. Password-protected RAR "
                            "archives are not supported."
                        )

                    name = str(entry.pathname or "")
                    _validate_member_destination(extract_path, name)

                    parts = [
                        p
                        for p in name.replace("\\", "/").split("/")
                        if p not in ("", ".")
                    ]
                    destination = extract_path / Path(*parts)

                    if entry.isdir:
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    if not entry.isfile:
                        # Symlinks and special entries are skipped (never
                        # materialised) — mirrors the tar/zip path behavior
                        # of ignoring non-regular-file members.
                        continue

                    files += 1
                    if files > self.MAX_FILES:
                        raise RuntimeError("Archive extraction blocked: MAX_FILES exceeded")

                    size = entry.size or 0
                    if size > self.MAX_SINGLE_FILE_SIZE_BYTES:
                        raise RuntimeError(
                            "Archive extraction blocked: MAX_SINGLE_FILE_SIZE_BYTES exceeded"
                        )
                    if written + size > self.MAX_TOTAL_SIZE_BYTES:
                        raise RuntimeError(
                            "Archive extraction blocked: MAX_TOTAL_SIZE_BYTES exceeded"
                        )

                    destination.parent.mkdir(parents=True, exist_ok=True)
                    written += self._copy_rar_entry(entry, destination)
        except (RarEncryptedError, RarMultiVolumeError, RarUnsupportedContentError):
            raise
        except libarchive.ArchiveError as exc:
            message = str(exc)
            lowered = message.lower()
            # Header-encrypted RAR4 archives fail during header read with an
            # explicit passphrase error; classify those as password errors.
            if "passphrase" in lowered or "password" in lowered or "encrypted" in lowered:
                raise RarEncryptedError(
                    "RAR extraction blocked: the archive is password-protected. "
                    "Password-protected RAR archives are not supported."
                ) from exc
            raise RarUnsupportedContentError(
                f"RAR extraction failed: {message}"
            ) from exc

        if files == 0:
            raise RarUnsupportedContentError("RAR extraction produced no files.")

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Extract archive to output directory (hardened against traversal + zip bombs)."""

        suffix = source_path.suffix.lower()
        stem = source_path.stem

        # Handle double extensions like .tar.gz
        if source_path.name.endswith(".tar.gz") or source_path.name.endswith(".tgz"):
            extract_dir_name = source_path.name.replace(".tar.gz", "").replace(".tgz", "")
        else:
            extract_dir_name = stem

        # Prefer a request-local temp_dir for working files when provided.
        # Fallback to output_dir then global settings.OUTPUT_DIR.
        resolved_output_dir = (temp_dir or output_dir or settings.OUTPUT_DIR) / "archive"
        resolved_output_dir.mkdir(parents=True, exist_ok=True)

        extract_path = resolved_output_dir / extract_dir_name
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
                # VAR-34 (Batch 6 Gate 2): in-process libarchive-c RAR
                # extraction (RAR4 + RAR5) with the same limits and
                # traversal validation as the zip/tar paths.
                self._extract_rar_members(source_path, extract_path)


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

        except (
            RarEncryptedError,
            RarMultiVolumeError,
            RarUnsupportedContentError,
        ):
            # Honest typed RAR errors: preserve the extraction-root cleanup
            # semantics but keep the typed exception for the plugin layer.
            if extract_path.exists():
                shutil.rmtree(extract_path, ignore_errors=True)
            raise

        except Exception as e:
            if extract_path.exists():
                shutil.rmtree(extract_path)
            raise RuntimeError(f"Archive extraction failed: {str(e)}")

