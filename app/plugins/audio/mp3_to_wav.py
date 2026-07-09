"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

MP3 -> WAV Plugin
"""

from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class MP3ToWAVPlugin(ConverterPlugin):

    slug = "mp3-to-wav"

    source_formats = [
        "mp3",
    ]

    target_formats = [
        "wav",
    ]

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