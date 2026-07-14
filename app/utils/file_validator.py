"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.2.0
"""

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from fastapi import UploadFile

from app.core.settings import settings

# ==========================================================
# Configuration
# ==========================================================

ALLOWED_EXTENSIONS = {

    # IMAGE
    "jpg",
    "jpeg",
    "png",
    "gif",
    "webp",
    "bmp",

    # AUDIO
    "mp3",
    "wav",
    "aac",
    "ogg",
    "flac",
    "m4a",

    # VIDEO
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",

    # DOCUMENT
    "pdf",
    "docx",
    "doc",
    "txt",
}

DISALLOWED_EXTENSIONS = {
    "exe",
    "bat",
    "sh",
    "py",
    "js",
    "cmd",
    "scr",
    "dll",
    "com",
    "vbs",
    "ps1",
    "msi",
}

FILE_SIGNATURES = {
    "jpg": [b"\xff\xd8\xff"],
    "jpeg": [b"\xff\xd8\xff"],
    "png": [b"\x89PNG\r\n\x1a\n"],
    "gif": [b"GIF87a", b"GIF89a"],
    "webp": [b"RIFF"],
    "bmp": [b"BM"],
    "mp3": [b"ID3", b"\xff\xfb"],
    "wav": [b"RIFF"],
    "aac": [b"\xFF\xF1", b"\xFF\xF9"],
    "ogg": [b"OggS"],
    "flac": [b"fLaC"],
    "m4a": [b"ftyp", b"moov"],
    "mp4": [b"ftyp", b"moov"],
    "mov": [b"ftyp", b"moov"],
    "avi": [b"RIFF"],
    "mkv": [b"\x1A\x45\xDF\xA3"],
    "webm": [b"\x1A\x45\xDF\xA3"],
    "pdf": [b"%PDF-"],
    "docx": [b"PK"],
    "doc": [b"\xD0\xCF\x11\xE0"],
    "txt": [],
}

CONTENT_TYPE_BY_EXTENSION = {
    "jpg": ["image/jpeg"],
    "jpeg": ["image/jpeg"],
    "png": ["image/png"],
    "gif": ["image/gif"],
    "webp": ["image/webp"],
    "bmp": ["image/bmp"],
    "mp3": ["audio/mpeg"],
    "wav": ["audio/wav", "audio/x-wav"],
    "aac": ["audio/aac"],
    "ogg": ["audio/ogg", "application/ogg"],
    "flac": ["audio/flac"],
    "m4a": ["audio/mp4", "audio/m4a"],
    "mp4": ["video/mp4"],
    "mov": ["video/quicktime"],
    "avi": ["video/x-msvideo"],
    "mkv": ["video/x-matroska"],
    "webm": ["video/webm"],
    "pdf": ["application/pdf"],
    "docx": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
    "doc": ["application/msword"],
    "txt": ["text/plain"],
}


# ==========================================================
# Exceptions
# ==========================================================

class FileValidationError(Exception):
    """Raised when uploaded file is invalid."""
    pass


# ==========================================================
# Helpers
# ==========================================================

def get_extension(filename: str) -> str:
    return Path(filename).suffix.lower().replace(".", "")


def validate_filename(filename: str) -> None:

    if not filename:
        raise FileValidationError("Filename is empty.")

    name = Path(filename).name

    if name != filename:
        raise FileValidationError("Invalid filename.")

    if ".." in filename:
        raise FileValidationError("Invalid filename.")

    if len(filename) > settings.MAX_FILENAME_LENGTH:
        raise FileValidationError("Filename is too long.")


def validate_extension(filename: str) -> str:

    extension = get_extension(filename)

    if extension in DISALLOWED_EXTENSIONS:
        raise FileValidationError("Unsupported file type.")

    if extension not in ALLOWED_EXTENSIONS:

        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))

        raise FileValidationError(
            f"Unsupported file type.\nAllowed types: {allowed}"
        )

    return extension


def _get_content_type(file: UploadFile) -> str | None:
    if hasattr(file, "content_type") and file.content_type:
        return file.content_type

    headers = getattr(file, "headers", None)
    if headers:
        return headers.get("content-type")

    return None


MEDIA_EXTENSIONS = {
    "mp3",
    "wav",
    "aac",
    "ogg",
    "flac",
    "m4a",
    "mp4",
    "mov",
    "avi",
    "mkv",
    "webm",
}


def _validate_media_with_ffprobe(file: UploadFile, extension: str) -> None:
    if extension not in MEDIA_EXTENSIONS:
        return

    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return

    current_position = file.file.tell()

    try:
        file.file.seek(0)

        with tempfile.NamedTemporaryFile(suffix=f".{extension}", delete=False) as temp_file:
            temp_path = Path(temp_file.name)

            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)

        try:
            result = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=format_name:stream=codec_type",
                    "-of",
                    "json",
                    str(temp_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                raise FileValidationError(
                    "Uploaded file contents do not match the file type."
                )

            try:
                payload = json.loads(result.stdout or "{}")
            except json.JSONDecodeError as exc:
                raise FileValidationError(
                    "Uploaded file contents do not match the file type."
                ) from exc

            format_name = (payload.get("format") or {}).get("format_name")
            streams = payload.get("streams") or []

            if not format_name or not streams:
                raise FileValidationError(
                    "Uploaded file contents do not match the file type."
                )

        finally:
            try:
                temp_path.unlink(missing_ok=True)
            except Exception:
                pass
    finally:
        file.file.seek(current_position)


def validate_signature(file: UploadFile, extension: str) -> None:

    if extension in MEDIA_EXTENSIONS:
        _validate_media_with_ffprobe(file, extension)
        return

    signatures = FILE_SIGNATURES.get(extension, [])

    if not signatures:
        return

    current_position = file.file.tell()
    header = file.file.read(64 * 1024)
    file.file.seek(current_position)

    if not header:
        raise FileValidationError("Uploaded file appears to be empty.")

    def matches_signature(signature: bytes) -> bool:
        if signature in {b"ftyp", b"moov"}:
            return (
                header.startswith(signature)
                or (len(header) >= 8 and header[4:8] == signature)
                or signature in header
            )
        return header.startswith(signature)

    if not any(matches_signature(signature) for signature in signatures):
        raise FileValidationError(
            "Uploaded file contents do not match the file type."
        )


def validate_content_type(file: UploadFile, extension: str) -> None:
    expected_types = CONTENT_TYPE_BY_EXTENSION.get(extension, [])
    if not expected_types:
        return

    content_type = _get_content_type(file)
    if not content_type:
        return

    normalized_type = content_type.split(";")[0].strip().lower()
    if normalized_type not in expected_types:
        raise FileValidationError(
            "Uploaded file content type does not match the file type."
        )


def validate_size(file: UploadFile) -> None:

    max_size_bytes = settings.MAX_UPLOAD_SIZE
    contents = file.file.read(max_size_bytes + 1)

    file.file.seek(0)

    if len(contents) > max_size_bytes:

        raise FileValidationError(
            f"Maximum upload size is {settings.MAX_UPLOAD_SIZE_MB} MB."
        )


# ==========================================================
# Main Validator
# ==========================================================

def validate_upload_file(file: UploadFile) -> None:

    validate_filename(file.filename)

    extension = validate_extension(file.filename)

    validate_size(file)

    validate_content_type(file, extension)
    validate_signature(file, extension)
