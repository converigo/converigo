"""
AAC -> MP3 Plugin (AUD-09)

Convert AAC audio files to MP3 using FFmpeg (libmp3lame).
"""
from __future__ import annotations

from pathlib import Path

from app.core.settings import settings
from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin


class AACToMP3Plugin(ConverterPlugin):
    slug = "aac-to-mp3"
    name = "AAC to MP3"
    description = "Convert AAC audio files to MP3 format."
    category = "audio"
    engine = "ffmpeg"
    icon = "🎧"

    source_formats = ["aac"]
    target_formats = ["mp3"]

    goal = "compatibility"
    use_case = "Best for converting AAC files to widely compatible MP3."
    priority = 80
    quality = 90
    compatibility = 95
    estimated_saving = 10
    badge = "Compatible Audio"
    seo_title = "AAC to MP3 Converter | Converigo"
    seo_description = "Convert AAC audio files to MP3 format quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("AACToMP3Plugin only supports AAC -> MP3.")

        working_root = (temp_dir or output_dir or (settings.OUTPUT_DIR / "audio"))
        working_root.mkdir(parents=True, exist_ok=True)
        output_path = working_root / f"{source_path.stem}.mp3"

        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=["-acodec", "libmp3lame"],
        )