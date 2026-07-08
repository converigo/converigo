import shutil
import subprocess
from pathlib import Path

from app.plugins.base import ConverterPlugin


class MP4ToMP3Plugin(ConverterPlugin):
    slug = "mp4-to-mp3"
    source_formats = ["mp4"]
    target_formats = ["mp3"]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError(
                "MP4ToMP3Plugin only supports mp4 to mp3 conversion."
            )

        output_dir = Path("outputs") / "audio"
        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path = output_dir / f"{source_path.stem}.mp3"

        print("=" * 60)
        print("MP4 TO MP3 DEBUG")
        print("=" * 60)
        print("SOURCE :", source_path)
        print("TARGET :", output_path)
        print("FFMPEG PATH :", shutil.which("ffmpeg"))
        print("=" * 60)

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

        print("COMMAND :")
        print(" ".join(command))
        print("=" * 60)

        try:

            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
            )

            print("RETURN CODE :", completed.returncode)

            if completed.stdout:
                print("STDOUT")
                print(completed.stdout)

            if completed.stderr:
                print("STDERR")
                print(completed.stderr)

        except FileNotFoundError as exc:

            print("=" * 60)
            print("FFMPEG TIDAK DITEMUKAN")
            print("PATH :", shutil.which("ffmpeg"))
            print("=" * 60)

            raise RuntimeError(
                "FFmpeg is not installed or not available on PATH."
            ) from exc

        if completed.returncode != 0:

            raise RuntimeError(
                f"FFmpeg failed:\n\n{completed.stderr.strip() or completed.stdout.strip()}"
            )

        if not output_path.exists():

            raise RuntimeError(
                f"Output file was not created: {output_path}"
            )

        print("=" * 60)
        print("SUCCESS")
        print("OUTPUT :", output_path)
        print("=" * 60)

        return output_path