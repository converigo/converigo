from __future__ import annotations

import asyncio
import shutil
import subprocess
from pathlib import Path

import pytest


def require_ffmpeg() -> str:
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is not installed")
    return ffmpeg


async def create_sample_video(
    tmp_path: Path,
    filename: str,
    *,
    duration: float = 1.0,
    size: str = "160x120",
    fps: int = 8,
    include_audio: bool = False,
) -> Path:
    ffmpeg = require_ffmpeg()
    output_path = tmp_path / filename
    command = [
        ffmpeg,
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"testsrc2=size={size}:rate={fps}",
    ]

    if include_audio:
        command.extend([
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=1000:duration=1",
        ])

    command.extend([
        "-t",
        str(duration),
        "-pix_fmt",
        "yuv420p",
        str(output_path),
    ])

    completed = await run_ffmpeg(command)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "Failed to create sample video")

    return output_path


async def run_ffmpeg(command: list[str], timeout_seconds: int = 60) -> subprocess.CompletedProcess[str]:
    return await asyncio.to_thread(
        subprocess.run,
        command,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )


async def convert_with_ffmpeg(input_path: Path, output_path: Path, arguments: list[str]) -> Path:
    ffmpeg = require_ffmpeg()
    command = [ffmpeg, "-y", "-i", str(input_path), *arguments, str(output_path)]
    completed = await run_ffmpeg(command)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "FFmpeg conversion failed")
    return output_path


def skip_if_ffmpeg_unavailable() -> None:
    try:
        require_ffmpeg()
    except RuntimeError as exc:
        pytest.skip(str(exc))
