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
    ) -> Path:

        ffmpeg = shutil.which("ffmpeg")

        if ffmpeg is None:

            raise RuntimeError(
                "FFmpeg tidak ditemukan pada PATH."
            )

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

        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=settings.CONVERSION_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            if output_path.exists():
                output_path.unlink(missing_ok=True)
            raise RuntimeError(
                f"Conversion timed out after {settings.CONVERSION_TIMEOUT_SECONDS} seconds."
            ) from exc

        if completed.returncode != 0:

            raise RuntimeError(
                completed.stderr
            )

        return output_path