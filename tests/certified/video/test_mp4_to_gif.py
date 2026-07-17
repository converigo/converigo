from __future__ import annotations

# This certified test generates a temporary MP4 sample and converts it to GIF
# using FFmpeg when the runtime is available. It skips when FFmpeg is missing.
import pytest
from pathlib import Path

from tests.certified.video._helpers import (
    convert_with_ffmpeg,
    create_sample_video,
    skip_if_ffmpeg_unavailable,
)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_mp4_to_gif(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source_path = await create_sample_video(tmp_path, "sample.mp4")
    output_path = tmp_path / "sample.gif"

    await convert_with_ffmpeg(
        source_path,
        output_path,
        ["-vf", "fps=8,scale=320:-1:flags=lanczos", "-loop", "0"],
    )

    assert output_path.exists(), "Output gif was not created"
    assert output_path.suffix.lower() == ".gif"
