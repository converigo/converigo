"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.2.0
"""

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
    "m4a": [b"ftyp"],
    "mp4": [b"ftyp"],
    "mov": [b"ftyp"],
    "avi": [b"RIFF"],
    "mkv": [b"\x1A\x45\xDF\xA3"],
    "webm": [b"\x1A\x45\xDF\xA3"],
    "pdf": [b"%PDF-"],
    "docx": [b"PK"],
    "doc": [b"\xD0\xCF\x11\xE0"],
    "txt": [],
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


def validate_signature(file: UploadFile, extension: str) -> None:

    signatures = FILE_SIGNATURES.get(extension, [])

    if not signatures:
        return

    current_position = file.file.tell()
    header = file.file.read(32)
    file.file.seek(current_position)

    if not header:
        raise FileValidationError("Uploaded file appears to be empty.")

    def matches_signature(signature: bytes) -> bool:
        if signature == b"ftyp":
            return signature in header
        return header.startswith(signature)

    if not any(matches_signature(signature) for signature in signatures):
        raise FileValidationError(
            "Uploaded file contents do not match the file type."
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

    validate_signature(file, extension)
