from __future__ import annotations

import pytest
from pathlib import Path

from tests.certified.audio._helpers import (
    convert_with_ffmpeg,
    create_audio_sample,
    skip_if_ffmpeg_unavailable,
)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_mp3_to_wav(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source_path = await create_audio_sample(tmp_path, "sample.mp3", output_format="mp3")
    output_path = tmp_path / "sample.wav"

    await convert_with_ffmpeg(source_path, output_path, ["-vn", "-acodec", "pcm_s16le"])

    assert output_path.exists(), "Output wav was not created"
    assert output_path.suffix.lower() == ".wav"
