import subprocess
from pathlib import Path

from app.core.settings import settings
from app.engines.base_engine import BaseEngine


class VideoEngine(BaseEngine):
    ENGINE_NAME = "video"

    SUPPORTED_FORMATS = [
        "mp4",
        "mov",
        "avi",
        "mkv",
        "webm",
    ]

    AUDIO_TARGETS = {
        "mp3": {"extension": "mp3", "codec": "libmp3lame"},
        "m4a": {"extension": "m4a", "codec": "aac"},
        "wav": {"extension": "wav", "codec": "pcm_s16le"},
        "aac": {"extension": "aac", "codec": "aac"},
    }

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        normalized_target = target_format.lower().strip()
        if (
            source_path.suffix.lower() != ".mp4"
            or normalized_target not in self.AUDIO_TARGETS
        ):
            supported_targets = ", ".join(sorted(self.AUDIO_TARGETS))
            raise RuntimeError(
                f"VideoEngine currently supports only MP4 -> {supported_targets}."
            )

        output_dir = settings.OUTPUT_DIR / "audio"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        config = self.AUDIO_TARGETS[normalized_target]
        output_path = output_dir / f"{source_path.stem}.{config['extension']}"

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-acodec",
            config["codec"],
            str(output_path),
        ]

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=settings.VIDEO_CONVERSION_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg was not found.") from exc
        except subprocess.TimeoutExpired as exc:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Conversion timed out after {settings.VIDEO_CONVERSION_TIMEOUT_SECONDS} seconds."
            ) from exc

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or result.stdout.strip() or "FFmpeg conversion failed."
            )

        return output_path