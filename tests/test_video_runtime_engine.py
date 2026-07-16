import asyncio
from pathlib import Path

import pytest

from app.core.settings import settings
from app.engines.video_engine import VideoEngine


@pytest.mark.parametrize("target_format", ["mp3", "m4a", "wav", "aac"])
def test_video_engine_converts_mp4_to_primary_audio_targets(tmp_path, monkeypatch, target_format):
    monkeypatch.setattr(settings, "OUTPUT_DIR", tmp_path / "outputs")
    monkeypatch.setattr(settings, "VIDEO_CONVERSION_TIMEOUT_SECONDS", 60)

    source_path = Path(__file__).parent.parent / "test_files" / "sample.mp4"
    engine = VideoEngine()

    output_path = asyncio.run(engine.convert(source_path, target_format))

    assert output_path.exists()
    assert output_path.suffix == f".{target_format}"
    output_path.unlink(missing_ok=True)
