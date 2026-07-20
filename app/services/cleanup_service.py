import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.core.settings import settings

logger = logging.getLogger(__name__)


class CleanupService:
    def __init__(self) -> None:
        self.upload_dir = settings.UPLOAD_DIR
        self.output_dir = settings.OUTPUT_DIR
        self.retention_seconds = getattr(settings, "OUTPUT_RETENTION_SECONDS", settings.FILE_RETENTION_SECONDS)

    def _is_recent(self, path: Path, threshold: datetime) -> bool:
        try:
            if not path.exists():
                return True
            modified_at = datetime.utcfromtimestamp(path.stat().st_mtime)
            return modified_at >= threshold
        except FileNotFoundError:
            return True
        except Exception:
            logger.exception("Failed to inspect file for cleanup: %s", path)
            return True

    def clean_old_files(self) -> None:
        threshold = datetime.utcnow() - timedelta(seconds=self.retention_seconds)
        # Clean both temporary uploads and generated outputs so expired files are
        # removed consistently at startup.
        directories_to_clean = [self.upload_dir, self.output_dir]

        for directory in directories_to_clean:
            if not directory.exists():
                continue

            try:
                for path in directory.rglob("*"):
                    if not path.is_file():
                        continue

                    if self._is_recent(path, threshold):
                        continue

                    try:
                        path.unlink(missing_ok=True)
                        logger.info("Removed expired file: %s", path)
                    except PermissionError:
                        logger.warning("Skipped file due to permission error: %s", path)
                    except Exception:
                        logger.exception("Failed to remove expired file: %s", path)
            except Exception:
                logger.exception("Cleanup scan failed for directory: %s", directory)
