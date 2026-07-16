"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 1.0.0

FFmpeg Engine
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.settings import settings


class FFmpegEngine:

    @staticmethod
    async def convert(
        source_path: Path,
        output_path: Path,
        arguments: list[str],
        timeout_seconds: int | None = None,
    ) -> Path:

        ffmpeg = shutil.which("ffmpeg")

        if ffmpeg is None:
            raise RuntimeError("FFmpeg tidak ditemukan pada PATH.")

        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        command = [
            ffmpeg,
            "-y",
            "-i",
            str(source_path),
            *arguments,
            str(output_path),
        ]

        print("=" * 60)
        print("FFMPEG COMMAND")
        print(command)
        print("=" * 60)

        timeout_value = timeout_seconds or settings.CONVERSION_TIMEOUT_SECONDS

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                timeout=timeout_value,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("FFmpeg tidak ditemukan pada PATH.") from exc
        except subprocess.TimeoutExpired as exc:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Conversion timed out after {timeout_value} seconds."
            ) from exc

        if completed.returncode != 0:
            detail = (completed.stderr or completed.stdout or "").strip()
            if not detail:
                detail = f"FFmpeg conversion failed with exit code {completed.returncode}."
            raise RuntimeError(detail)

        return output_path