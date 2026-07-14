"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> OGG Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToOGGPlugin(ConverterPlugin):
    slug = "mp4-to-ogg"
    name = "MP4 to OGG"
    description = "Extract audio from MP4 videos and convert it into OGG format."
    category = "video"
    engine = "ffmpeg"
    icon = "🎵"
    popular = True
    featured = False
    source_formats = ["mp4"]
    target_formats = ["ogg"]
    goal = "extract_audio"
    use_case = "Best for open-source audio projects and web playback."
    priority = 84
    quality = 88
    compatibility = 90
    estimated_saving = 15
    badge = "Open Format"
    seo_title = "MP4 to OGG Converter | Converigo"
    seo_description = "Convert MP4 videos to OGG audio quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToOGGPlugin only supports MP4 -> OGG.")

        output_path = Path("outputs") / "audio" / f"{source_path.stem}.ogg"
        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vn", "-acodec", "libvorbis"],
        )
