"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.2.0
"""

import hashlib
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile

from app.core.settings import settings
from app.utils.file_validator import (
    FileValidationError,
    validate_upload_file,
)

logger = logging.getLogger(__name__)

UPLOAD_DIR = settings.UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 1024 * 1024  # 1 MB


class UploadError(Exception):
    pass


class UploadService:

    async def process_upload(
        self,
        file: UploadFile,
    ) -> Path:

        target_path = None

        try:

            validate_upload_file(file)

            extension = Path(file.filename).suffix.lower()

            filename = f"{uuid.uuid4().hex}{extension}"

            target_path = UPLOAD_DIR / filename

            sha256 = hashlib.sha256()
            file_size = 0

            uploaded_at = datetime.utcnow()

            with open(target_path, "wb") as destination:

                while True:

                    chunk = await file.read(CHUNK_SIZE)

                    if not chunk:
                        break

                    destination.write(chunk)

                    file_size += len(chunk)

                    if file_size > settings.MAX_UPLOAD_SIZE:
                        raise FileValidationError(
                            f"Maximum upload size is {settings.MAX_UPLOAD_SIZE_MB} MB."
                        )

                    sha256.update(chunk)

            await file.close()

            # Metadata sementara
            metadata = {
                "original_name": file.filename,
                "stored_name": filename,
                "extension": extension,
                "path": str(target_path),
                "size": file_size,
                "sha256": sha256.hexdigest(),
                "uploaded_at": uploaded_at.isoformat(),
            }

            # Sprint berikutnya metadata akan dikirim
            # ke Logger / Database / Queue.
            _ = metadata

            return target_path

        except FileValidationError as exc:

            if target_path and target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    logger.exception("Failed to remove partial upload %s", target_path)

            raise UploadError(
                str(exc)
            ) from exc

        except Exception as exc:
            if target_path and target_path.exists():
                try:
                    target_path.unlink()
                except Exception:
                    logger.exception("Failed to remove partial upload %s", target_path)

            raise UploadError(
                "Unable to save uploaded file."
            ) from exc