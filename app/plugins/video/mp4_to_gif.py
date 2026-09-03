"""
MP4 -> GIF Plugin (VID-12)

Convert MP4 video clips to animated GIF using FFmpeg.
"""
from __future__ import annotations

from pathlib import Path

from app.core.settings import settings
from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToGIFPlugin(ConverterPlugin):
    slug = "mp4-to-gif"
    name = "MP4 to GIF"
    description = "Convert MP4 video clips to animated GIF images."
    category = "video"
    engine = "ffmpeg"
    icon = "🎞️"

    source_formats = ["mp4"]
    target_formats = ["gif"]

    goal = "playback"
    use_case = "Best for creating animated GIF previews from short video clips."
    priority = 75
    quality = 85
    compatibility = 90
    estimated_saving = 10
    badge = "Animated GIF"
    seo_title = "MP4 to GIF Converter | Converigo"
    seo_description = "Convert MP4 video files to animated GIF images quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToGIFPlugin only supports MP4 -> GIF.")

        working_root = (temp_dir or output_dir or (settings.OUTPUT_DIR / "video"))
        working_root.mkdir(parents=True, exist_ok=True)
        output_path = working_root / f"{source_path.stem}.gif"

        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vf", "fps=8,scale=320:-1:flags=lanczos", "-loop", "0"],
        )