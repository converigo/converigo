"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> MP3 Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP4ToMP3Plugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "mp4-to-mp3"

    name = "MP4 to MP3"

    description = (
        "Extract audio from MP4 videos "
        "and convert it into MP3 format."
    )

    category = "video"

    engine = "ffmpeg"

    icon = "🎵"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True

    featured = True


    # ==========================================
    # Formats
    # ==========================================

    source_formats = [
        "mp4",
    ]

    target_formats = [
        "mp3",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extract_audio"

    use_case = (
        "Best for extracting audio from videos, "
        "music files, podcasts, and recordings."
    )


    priority = 100

    quality = 95

    compatibility = 100

    estimated_saving = 60


    badge = "Most Popular"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "MP4 to MP3 Converter | Converigo"
    )

    seo_description = (
        "Convert MP4 videos to MP3 audio "
        "quickly and easily."
    )


    # ==========================================
    # Conversion
    # ==========================================

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:


        if not self.supports(
            source_path.suffix,
            target_format,
        ):

            raise RuntimeError(
                "MP4ToMP3Plugin only supports MP4 -> MP3."
            )


        output_path = (
            Path("outputs")
            / "audio"
            / f"{source_path.stem}.mp3"
        )


        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=[
                "-vn",
                "-acodec",
                "libmp3lame",
            ],
        )