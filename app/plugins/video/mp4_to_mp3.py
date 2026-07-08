import shutil
import subprocess
from pathlib import Path

from app.plugins.base import ConverterPlugin


class MP4ToMP3Plugin(ConverterPlugin):
    slug = "mp4-to-mp3"
    source_formats = ["mp4"]
    target_formats = ["mp3"]

    async def convert(self, source_path: Path, target_format: str) -> Path:

        ffmpeg_path = shutil.which("ffmpeg")

        print("=" * 60)
        print("FFMPEG PATH :", ffmpeg_path)
        print("=" * 60)

        if ffmpeg_path is None:
            raise RuntimeError(
                "Python tidak menemukan binary ffmpeg pada PATH."
            )

        output_dir = Path("outputs") / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)

        output_path = output_dir / f"{source_path.stem}.mp3"

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(source_path),
            "-vn",
            "-acodec",
            "libmp3lame",
            str(output_path),
        ]

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
        )

        print("RETURN CODE :", completed.returncode)
        print("STDOUT")
        print(completed.stdout)
        print("STDERR")
        print(completed.stderr)

        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)

        return output_path