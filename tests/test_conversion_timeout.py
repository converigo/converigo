import asyncio
from pathlib import Path

import pytest

from app.core.settings import settings
from app.services.conversion_service import ConversionError, ConversionService


@pytest.fixture(autouse=True)
def reset_timeout_settings(monkeypatch):
    monkeypatch.setattr(settings, "CONVERSION_TIMEOUT_SECONDS", 5, raising=False)
    monkeypatch.setattr(settings, "VIDEO_CONVERSION_TIMEOUT_SECONDS", 5, raising=False)
    monkeypatch.setattr(settings, "AUDIO_CONVERSION_TIMEOUT_SECONDS", 5, raising=False)
    monkeypatch.setattr(settings, "IMAGE_CONVERSION_TIMEOUT_SECONDS", 5, raising=False)
    monkeypatch.setattr(settings, "DOCUMENT_CONVERSION_TIMEOUT_SECONDS", 5, raising=False)
    yield


def test_normal_conversion_succeeds(monkeypatch, tmp_path):
    source_path = tmp_path / "sample.txt"
    source_path.write_text("hello", encoding="utf-8")

    service = ConversionService()

    class FakePlugin:
        async def convert(self, source_path, target_format):
            output_path = tmp_path / f"converted.{target_format}"
            output_path.write_text("ok", encoding="utf-8")
            return output_path

    monkeypatch.setattr("app.services.conversion_service.registry.get_plugin", lambda source_format, target_format: FakePlugin())

    output_path = asyncio.run(service.convert_file(source_path, "pdf"))

    assert output_path == tmp_path / "converted.pdf"


def test_timeout_conversion_is_stopped_safely(monkeypatch, tmp_path):
    source_path = tmp_path / "sample.txt"
    source_path.write_text("hello", encoding="utf-8")

    service = ConversionService()

    class SlowPlugin:
        async def convert(self, source_path, target_format):
            await asyncio.sleep(10)
            return tmp_path / f"converted.{target_format}"

    monkeypatch.setattr("app.services.conversion_service.registry.get_plugin", lambda source_format, target_format: SlowPlugin())

    with pytest.raises(ConversionError, match="timed out"):
        asyncio.run(service.convert_file(source_path, "pdf"))
