import subprocess
from pathlib import Path

from app.plugins.base import ConverterPlugin


class MP4ToMP3Plugin(ConverterPlugin):
    slug = "mp4-to-mp3"
    source_formats = ["mp4"]
    target_formats = ["mp3"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("MP4ToMP3Plugin only supports mp4 to mp3 conversion.")

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
