"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> WAV Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToWAVPlugin(ConverterPlugin):
    slug = "mp4-to-wav"
    name = "MP4 to WAV"
    description = "Extract audio from MP4 videos and convert it into WAV format."
    category = "video"
    engine = "ffmpeg"
    icon = "🎵"
    popular = True
    featured = False
    source_formats = ["mp4"]
    target_formats = ["wav"]
    goal = "extract_audio"
    use_case = "Best for high-quality audio editing and archival workflows."
    priority = 95
    quality = 95
    compatibility = 95
    estimated_saving = 5
    badge = "High Quality"
    seo_title = "MP4 to WAV Converter | Converigo"
    seo_description = "Convert MP4 videos to WAV audio quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToWAVPlugin only supports MP4 -> WAV.")

        output_path = Path("outputs") / "audio" / f"{source_path.stem}.wav"
        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-vn", "-acodec", "pcm_s16le"],
        )
