"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP3 -> WAV Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP3ToWAVPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "mp3-to-wav"

    name = "MP3 to WAV"

    description = (
        "Convert MP3 audio into WAV format "
        "for high quality editing."
    )

    category = "audio"

    engine = "ffmpeg"

    icon = "🎧"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = False

    featured = False


    # ==========================================
    # Formats
    # ==========================================

    source_formats = [
        "mp3",
    ]

    target_formats = [
        "wav",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "quality"

    use_case = (
        "Best for professional audio editing, "
        "recording, and production workflows."
    )


    priority = 80

    quality = 100

    compatibility = 95

    estimated_saving = 5


    badge = "High Quality"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "MP3 to WAV Converter | Converigo"
    )

    seo_description = (
        "Convert MP3 files to WAV "
        "for better editing quality."
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
                "MP3ToWAVPlugin only supports MP3 -> WAV."
            )


        output_path = (
            Path("outputs")
            / "audio"
            / f"{source_path.stem}.wav"
        )


        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=[
                "-acodec",
                "pcm_s16le",
            ],
        )