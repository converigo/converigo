import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.core.settings import settings

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self) -> None:
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = settings.OUTPUT_DIR
        self.retention_seconds = settings.FILE_RETENTION_SECONDS

    def clean_old_files(self) -> None:
        threshold = datetime.utcnow() - timedelta(seconds=self.retention_seconds)

        for directory in (self.upload_dir, self.output_dir):
            if not directory.exists():
                continue

            for path in directory.rglob("*"):
                if not path.is_file():
                    continue

                try:
                    modified_at = datetime.utcfromtimestamp(path.stat().st_mtime)
                    if modified_at < threshold:
                        path.unlink()
                        logger.info("Removed stale temporary file: %s", path)
                except Exception:
                    logger.exception("Failed to remove stale file: %s", path)
