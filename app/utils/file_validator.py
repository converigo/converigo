"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.2.0
"""

from pathlib import Path

from fastapi import UploadFile

# ==========================================================
# Configuration
# ==========================================================

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB

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

    if len(filename) > 255:
        raise FileValidationError("Filename is too long.")


def validate_extension(filename: str) -> str:

    extension = get_extension(filename)

    if extension not in ALLOWED_EXTENSIONS:

        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))

        raise FileValidationError(
            f"Unsupported file type.\nAllowed types: {allowed}"
        )

    return extension


def validate_size(file: UploadFile) -> None:

    contents = file.file.read(MAX_FILE_SIZE + 1)

    file.file.seek(0)

    if len(contents) > MAX_FILE_SIZE:

        raise FileValidationError(
            f"Maximum upload size is {MAX_FILE_SIZE // 1024 // 1024} MB."
        )


# ==========================================================
# Main Validator
# ==========================================================

def validate_upload_file(file: UploadFile) -> None:

    validate_filename(file.filename)

    validate_extension(file.filename)

    validate_size(file)