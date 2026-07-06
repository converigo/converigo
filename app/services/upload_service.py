import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import UploadFile

from app.utils.file_validator import FileValidationError, validate_upload_file

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class UploadError(Exception):
    pass


class UploadService:
    async def process_upload(self, file: UploadFile) -> Path:
        validate_upload_file(file)

        target_file = UPLOAD_DIR / Path(file.filename).name

        try:
            with NamedTemporaryFile(delete=False, dir=UPLOAD_DIR, prefix="upload_", suffix=Path(file.filename).suffix) as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = Path(tmp.name)

            shutil.move(str(tmp_path), str(target_file))
            return target_file
        except FileValidationError as exc:
            raise UploadError(str(exc))
        except Exception as exc:
            raise UploadError("Unable to save uploaded file.") from exc
