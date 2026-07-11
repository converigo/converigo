from datetime import datetime, timedelta
import os

from app.core.settings import settings
from app.services.cleanup_service import CleanupService


def test_cleanup_removes_expired_output_files_and_preserves_recent_ones(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path, raising=False)
    monkeypatch.setattr(settings, "OUTPUT_RETENTION_MINUTES", 60, raising=False)
    monkeypatch.setattr(settings, "OUTPUT_RETENTION_SECONDS", 60 * 60, raising=False)

    old_file = tmp_path / "old-output.pdf"
    old_file.write_bytes(b"old")
    old_timestamp = (datetime.utcnow() - timedelta(minutes=90)).timestamp()
    os.utime(old_file, (old_timestamp, old_timestamp))

    recent_file = tmp_path / "recent-output.pdf"
    recent_file.write_bytes(b"recent")

    cleanup_service = CleanupService()
    cleanup_service.clean_old_files()

    assert not old_file.exists()
    assert recent_file.exists()


def test_cleanup_handles_missing_files_without_crashing(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path, raising=False)
    monkeypatch.setattr(settings, "OUTPUT_RETENTION_MINUTES", 60, raising=False)
    monkeypatch.setattr(settings, "OUTPUT_RETENTION_SECONDS", 60 * 60, raising=False)

    missing_file = tmp_path / "missing-output.pdf"
    missing_file.write_bytes(b"temp")
    missing_file.unlink()

    cleanup_service = CleanupService()
    cleanup_service.clean_old_files()

    assert not missing_file.exists()
