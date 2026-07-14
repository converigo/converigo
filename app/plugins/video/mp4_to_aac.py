"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> AAC Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToAACPlugin(ConverterPlugin):
    slug = "mp4-to-aac"
    name = "MP4 to AAC"
    description = "Extract audio from MP4 videos and convert it into AAC format."
    category = "video"
    engine = "ffmpeg"
    icon = "🎵"
    popular = True
    featured = False
    source_formats = ["mp4"]
    target_formats = ["aac"]
    goal = "extract_audio"
    use_case = "Best for streaming, mobile playback, and compatibility-focused workflows."
    priority = 90
    quality = 90
    compatibility = 100
    estimated_saving = 20
    badge = "Compatible"
    seo_title = "MP4 to AAC Converter | Converigo"
    seo_description = "Convert MP4 videos to AAC audio quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToAACPlugin only supports MP4 -> AAC.")

        output_path = Path("outputs") / "audio" / f"{source_path.stem}.aac"
        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vn", "-acodec", "aac"],
        )
