"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

MP4 -> MP3 Plugin

Converigo Smart Metadata Version
"""

import logging
import shutil
import subprocess
from pathlib import Path

from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin

logger = logging.getLogger(__name__)


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

    def _ensure_audio_stream(self, source_path: Path) -> None:
        ffprobe = shutil.which("ffprobe")
        ffmpeg = shutil.which("ffmpeg")

        if ffprobe:
            command = [
                ffprobe,
                "-v",
                "error",
                "-select_streams",
                "a",
                "-show_entries",
                "stream=index",
                "-of",
                "default=nw=1:nk=1",
                str(source_path),
            ]
        elif ffmpeg:
            command = [
                ffmpeg,
                "-v",
                "error",
                "-i",
                str(source_path),
                "-map",
                "0:a:0",
                "-f",
                "null",
                "-",
            ]
        else:
            return

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return
        except (OSError, PermissionError) as exc:
            if ffprobe and ffmpeg:
                logger.debug("ffprobe probe failed, falling back to ffmpeg: %s", exc)
                command = [
                    ffmpeg,
                    "-v",
                    "error",
                    "-i",
                    str(source_path),
                    "-map",
                    "0:a:0",
                    "-f",
                    "null",
                    "-",
                ]
                try:
                    completed = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                except (OSError, PermissionError):
                    return
            else:
                return

        if completed.returncode != 0:
            stderr = (completed.stderr or "").lower()
            if "stream map" in stderr or "matches no streams" in stderr or "invalid argument" in stderr:
                raise RuntimeError(
                    "The selected MP4 file does not contain an audio stream. Please upload a video file that includes audio before converting to MP3."
                )
            return

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

        self._ensure_audio_stream(source_path)

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