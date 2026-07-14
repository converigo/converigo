"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> FLAC Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToFLACPlugin(ConverterPlugin):
    slug = "mp4-to-flac"
    name = "MP4 to FLAC"
    description = "Extract audio from MP4 videos and convert it into FLAC format."
    category = "video"
    engine = "ffmpeg"
    icon = "🎵"
    popular = True
    featured = False
    source_formats = ["mp4"]
    target_formats = ["flac"]
    goal = "extract_audio"
    use_case = "Best for lossless audio archiving and preservation."
    priority = 88
    quality = 100
    compatibility = 85
    estimated_saving = 10
    badge = "Lossless"
    seo_title = "MP4 to FLAC Converter | Converigo"
    seo_description = "Convert MP4 videos to FLAC audio quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToFLACPlugin only supports MP4 -> FLAC.")

        output_path = Path("outputs") / "audio" / f"{source_path.stem}.flac"
        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vn", "-acodec", "flac"],
        )
