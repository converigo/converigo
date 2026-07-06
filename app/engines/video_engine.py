import subprocess
from pathlib import Path

from app.engines.base_engine import BaseEngine
from app.services.conversion_manager import register_engine


class VideoEngine(BaseEngine):
    ENGINE_NAME = "video"
    SUPPORTED_FORMATS = ["mp4", "mov", "avi", "mkv", "webm"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if source_path.suffix.lower() != ".mp4" or target_format.lower() != "mp3":
            raise RuntimeError("VideoEngine supports only MP4 to MP3 conversion in this implementation.")

        output_dir = Path("outputs") / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
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
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg is not installed or not available on PATH.") from exc

        if completed.returncode != 0:
            raise RuntimeError(
                f"FFmpeg failed: {completed.stderr.strip() or completed.stdout.strip()}"
            )

        return output_path


register_engine(VideoEngine)
