from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest

from app.engines.ffmpeg_engine import FFmpegEngine


def require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed")
    return ffmpeg


async def run_ffmpeg(command: list[str], timeout_seconds: int = 60) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


async def create_audio_sample(
    tmp_path: Path,
    filename: str,
    *,
    output_format: str,
    duration: float = 1.0,
) -> Path:
    ffmpeg = require_ffmpeg()
    output_path = tmp_path / filename
    command = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        "sine=frequency=1000:duration=1",
        "-t",
        str(duration),
    ]

    if output_format == "mp3":
        command.extend(["-c:a", "libmp3lame"])
    elif output_format == "wav":
        command.extend(["-c:a", "pcm_s16le"])
    elif output_format == "flac":
        command.extend(["-c:a", "flac"])
    elif output_format == "aac":
        command.extend(["-c:a", "aac", "-b:a", "128k"])
    elif output_format == "ogg":
        command.extend(["-c:a", "libvorbis"])
    elif output_format == "m4a":
        command.extend(["-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart"])
    else:
        raise ValueError(f"Unsupported output format: {output_format}")

    command.append(str(output_path))

    completed = await run_ffmpeg(command)
    if completed.returncode != 0:
        raise RuntimeError(
            completed.stderr.strip() or completed.stdout.strip() or f"Failed to create {output_format} sample"
        )

    return output_path


async def convert_with_ffmpeg(input_path: Path, output_path: Path, arguments: list[str]) -> Path:
    return await FFmpegEngine.convert(
        source_path=input_path,
        output_path=output_path,
        arguments=arguments,
    )


def skip_if_ffmpeg_unavailable() -> None:
    try:
        require_ffmpeg()
    except RuntimeError as exc:
        pytest.skip(str(exc))
