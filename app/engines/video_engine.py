import subprocess
from pathlib import Path

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

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        if (
            source_path.suffix.lower() != ".mp4"
            or target_format.lower() != "mp3"
        ):
            raise RuntimeError(
                "VideoEngine currently supports only MP4 → MP3."
            )

        output_dir = Path("outputs") / "audio"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / f"{source_path.stem}.mp3"

        command = [
            "ffmpeg",
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            str(output_path),
        ]

        try:

            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

        except FileNotFoundError as exc:

            raise RuntimeError(
                "FFmpeg was not found."
            ) from exc

        if result.returncode != 0:

            raise RuntimeError(
                result.stderr.strip()
                or result.stdout.strip()
            )

        return output_path