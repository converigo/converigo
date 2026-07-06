from fastapi import UploadFile

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "pdf", "docx", "txt", "mp4"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class FileValidationError(Exception):
    pass


def _get_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def validate_upload_file(file: UploadFile) -> None:
    extension = _get_extension(file.filename)
    if not extension or extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            "Unsupported file type. Allowed types: jpg, jpeg, png, gif, pdf, docx, txt."
        )

    contents = file.file.read(MAX_FILE_SIZE + 1)
    file.file.seek(0)

    if len(contents) > MAX_FILE_SIZE:
        raise FileValidationError("File is too large. Maximum size is 10 MB.")

    if file.filename.strip() == "":
        raise FileValidationError("Uploaded file must have a valid filename.")
