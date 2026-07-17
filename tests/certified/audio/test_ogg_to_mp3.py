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
async def test_ogg_to_mp3(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source_path = await create_audio_sample(tmp_path, "sample.ogg", output_format="ogg")
    output_path = tmp_path / "sample.mp3"

    await convert_with_ffmpeg(source_path, output_path, ["-vn", "-acodec", "libmp3lame"])

    assert output_path.exists(), "Output mp3 was not created"
    assert output_path.suffix.lower() == ".mp3"
