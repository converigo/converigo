import asyncio
from io import BytesIO
from unittest.mock import patch

import pytest
from fastapi import UploadFile

import app.services.upload_service as upload_service_module
from app.core.settings import settings
from app.services.upload_service import UploadError, UploadService


@pytest.fixture(autouse=True)
def reset_upload_limits(monkeypatch):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 100, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024, raising=False)
    yield
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 100, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024, raising=False)


def test_small_upload_is_accepted(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 1024 * 1024, raising=False)
    monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)

    service = UploadService()
    file = UploadFile(filename="small.txt", file=BytesIO(b"small payload"))

    saved_path = asyncio.run(service.process_upload(file))

    assert saved_path.exists()
    assert saved_path.parent == tmp_path
    saved_path.unlink(missing_ok=True)


def test_oversized_upload_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 1024 * 1024, raising=False)
    monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)

    service = UploadService()
    oversized_payload = b"x" * (1024 * 1024 + 1)
    file = UploadFile(filename="large.txt", file=BytesIO(oversized_payload))

    with pytest.raises(UploadError, match="Maximum upload size"):
        asyncio.run(service.process_upload(file))


def test_mp4_with_mobile_container_signature_is_accepted(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 100, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024, raising=False)
    monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)

    service = UploadService()
    payload = b"\x00\x00\x00\x14moov" + b"\x00" * 24
    file = UploadFile(
        filename="android-recording.mp4",
        file=BytesIO(payload),
        headers={"content-type": "video/mp4"},
    )

    # Mock ffprobe to skip validation in test environment
    with patch("app.utils.file_validator.shutil.which", return_value=None):
        saved_path = asyncio.run(service.process_upload(file))

        assert saved_path.exists()
        saved_path.unlink(missing_ok=True)


def test_mp4_with_conflicting_content_type_is_rejected(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 100, raising=False)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE", 100 * 1024 * 1024, raising=False)
    monkeypatch.setattr(upload_service_module, "UPLOAD_DIR", tmp_path, raising=False)

    service = UploadService()
    payload = b"\x00\x00\x00\x14ftyp" + b"\x00" * 24
    file = UploadFile(
        filename="fake.mp4",
        file=BytesIO(payload),
        headers={"content-type": "text/plain"},
    )

    with pytest.raises(UploadError, match="content type"):
        asyncio.run(service.process_upload(file))
