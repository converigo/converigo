from __future__ import annotations

# This certified test creates a tiny AVI container at runtime and converts it
# to MP4 using FFmpeg. It skips when FFmpeg is unavailable.
import pytest
from pathlib import Path

from tests.certified.video._helpers import (
    convert_with_ffmpeg,
    create_sample_video,
    skip_if_ffmpeg_unavailable,
)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_avi_to_mp4(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source_path = await create_sample_video(tmp_path, "sample.avi")
    output_path = tmp_path / "sample.mp4"

    await convert_with_ffmpeg(source_path, output_path, [])

    assert output_path.exists(), "Output mp4 was not created"
    assert output_path.suffix.lower() == ".mp4"
