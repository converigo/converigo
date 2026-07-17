from __future__ import annotations

# This certified test generates a tiny sample MP4 at runtime and then
# converts it to MP3 using FFmpeg. It skips cleanly when FFmpeg is not
# available on the host, which keeps the test suite portable.
import pytest
from pathlib import Path

from tests.certified.video._helpers import (
    convert_with_ffmpeg,
    create_sample_video,
    skip_if_ffmpeg_unavailable,
)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_mp4_to_mp3(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source_path = await create_sample_video(tmp_path, "sample.mp4", include_audio=True)
    output_path = tmp_path / "sample.mp3"

    await convert_with_ffmpeg(
        source_path,
        output_path,
        ["-vn", "-acodec", "libmp3lame"],
    )

    assert output_path.exists(), "Output mp3 was not created"
    assert output_path.suffix.lower() == ".mp3"
