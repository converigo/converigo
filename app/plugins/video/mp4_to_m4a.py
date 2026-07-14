"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> M4A Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToM4APlugin(ConverterPlugin):
    slug = "mp4-to-m4a"
    name = "MP4 to M4A"
    description = "Extract audio from MP4 videos and convert it into M4A format."
    category = "video"
    engine = "ffmpeg"
    icon = "🎵"
    popular = True
    featured = False
    source_formats = ["mp4"]
    target_formats = ["m4a"]
    goal = "extract_audio"
    use_case = "Best for compact audio files and compatibility with modern devices."
    priority = 92
    quality = 92
    compatibility = 98
    estimated_saving = 18
    badge = "Compact"
    seo_title = "MP4 to M4A Converter | Converigo"
    seo_description = "Convert MP4 videos to M4A audio quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToM4APlugin only supports MP4 -> M4A.")

        output_path = Path("outputs") / "audio" / f"{source_path.stem}.m4a"
        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vn", "-acodec", "aac"],
        )
