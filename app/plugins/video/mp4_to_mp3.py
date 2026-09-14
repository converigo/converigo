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

from app.core.settings import settings
from app.engines.ffmpeg_engine import FFmpegEngine
from app.plugins.base import ConverterPlugin

logger = logging.getLogger(__name__)


# The one user-facing sentence this plugin emits for an audio-less source.
#
# It travels through the sanctioned UnsupportedConversionError channel (HTTP 422,
# code UNSUPPORTED_CONVERSION), whose handler copies str(exc) straight into the
# response body. That makes this literal the ONLY place in the plugin where
# wording reaches a client, so it must stay plain prose: no Python class name,
# no engine/module name and no filesystem path.
#
# D4 (F1) removed the old echo of a raised RuntimeError text into
# HTTPException.detail, which is why an input-side condition now needs the typed
# channel instead of a generic 500.
NO_AUDIO_STREAM_MESSAGE = (
    "The selected MP4 file does not contain an audio stream. "
    "Please upload a video file that includes audio before converting to MP3."
)


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

    def _no_audio_stream_error(self, source_path: Path) -> Exception:
        """Honest error for a source that carries no audio to extract.

        An MP4 without an audio track cannot yield an MP3 no matter how often the
        request is retried: the missing thing is a property of the uploaded input,
        not a server fault. That is exactly the condition the
        ``UnsupportedConversionError`` channel exists for - the same shape as
        ``PDFEmptyError`` ("PDF has no pages") in this service and the F4 runner
        policy in app/factory/ffmpeg_runner.py, which maps unconvertible input to
        this error (422) while leaving environment problems (FFmpeg absent,
        timeouts) as RuntimeError -> 500.

        Local import mirrors the rar-extract / office-placeholder precedent and
        keeps app.plugins.video.* free of a module-level dependency on the service
        layer during plugin discovery.

        source_format comes from the file itself and target_format from this
        plugin's single declared target; the supports() guard at the top of
        convert() already narrowed both to mp4 -> mp3. The message is the
        reviewed public literal.
        """
        from app.services.conversion_service import UnsupportedConversionError

        return UnsupportedConversionError(
            source_path.suffix.lstrip(".").lower() or "mp4",
            self.target_formats[0],
            message=NO_AUDIO_STREAM_MESSAGE,
        )

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
            try:
                completed = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
            except (OSError, PermissionError):
                if ffmpeg:
                    # Fall through to ffmpeg probe
                    pass
                else:
                    return
            else:
                # Check if ffprobe found any audio streams
                if completed.returncode == 0 and completed.stdout.strip():
                    return  # Audio stream found
                elif completed.returncode == 0 and not completed.stdout.strip():
                    # ffprobe succeeded but found no audio streams
                    raise self._no_audio_stream_error(source_path)
                # If return code is non-zero, fall through to ffmpeg probe
                
        if ffmpeg:
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
            except subprocess.TimeoutExpired:
                return
            except (OSError, PermissionError):
                return

            if completed.returncode != 0:
                stderr_lower = (completed.stderr or "").lower()
                if "stream map" in stderr_lower or "matches no streams" in stderr_lower or "does not contain any stream" in stderr_lower or "invalid argument" in stderr_lower:
                    raise self._no_audio_stream_error(source_path)
            return

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:


        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            # Deliberately NOT the 422 channel: the registry guard
            # (PluginRegistry.get_plugin -> slug_winner_pairs) already refuses
            # every pair this plugin cannot serve, so reaching here means our own
            # dispatch is inconsistent - a server-side fault, and its text names a
            # Python class, which must never reach a client. Keep RuntimeError.
            raise RuntimeError(
                "MP4ToMP3Plugin only supports MP4 -> MP3."
            )

        self._ensure_audio_stream(source_path)

        # use request-local temp_dir when available so engines write
        # working files into the conversion-specific temp area instead
        # of writing directly into the public output directory.
        working_root = (temp_dir or output_dir or settings.OUTPUT_DIR) / "audio"
        working_root.mkdir(parents=True, exist_ok=True)

        output_path = working_root / f"{source_path.stem}.mp3"

        return await FFmpegEngine.convert(
            source_path=source_path,
            output_path=output_path,
            arguments=[
                "-vn",
                "-acodec",
                "libmp3lame",
            ],
        )