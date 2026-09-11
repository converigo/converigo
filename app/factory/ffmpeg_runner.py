"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F4)
Version : 1.0.0

Synchronous FFmpeg runner for factory-built media converters (F4).

Why a sync sibling of app/engines/ffmpeg_engine.py exists: the F0 factory
base (app/factory/plugin_base.py) invokes engine hooks synchronously
(``output_path = Path(self._convert(...))``), while FFmpegEngine.convert
is an ``async def``.  Factory hooks must therefore drive FFmpeg with a
plain blocking subprocess call - exactly the behavior
``FFmpegEngine.convert`` already exhibits internally (it blocks the event
loop on ``subprocess.run`` as well), so production timing semantics are
unchanged.  This module lives in app/factory/ (outside app/plugins/) so
plugin discovery rglob never mistakes it for a converter plugin.

Error policy (Supervisor F4 decision, audit tmp/f4_ffmpeg_audit.md):
a failing FFmpeg run on a factory media converter is treated as an
undecodable / unconvertible input and raises ``UnsupportedConversionError``
(lazy import, rar-extract precedent) so the API boundary answers the
honest 422 UNSUPPORTED_CONVERSION instead of a 500 or a fabricated
output.  Environment problems (FFmpeg missing from PATH) stay
RuntimeError -> 500, and timeouts raise RuntimeError so the conversion
service keeps its timeout semantics.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from app.core.settings import settings

#: Keep the honest error message readable: the tail of FFmpeg stderr holds
#: the actual failure ("Invalid data found ...", "moov atom not found").
_STDERR_DETAIL_LIMIT = 400


def run_ffmpeg(
    source_path: Path,
    output_path: Path,
    arguments: list[str],
    timeout_seconds: int | None = None,
) -> Path:
    """Run ``ffmpeg -y -i <source> <arguments> <output>`` synchronously.

    Mirrors the command shape and guards of ``FFmpegEngine.convert``:
    PATH check, parent mkdir, timeout, non-zero exit handling.  A non-zero
    exit raises the typed honest error (422 UNSUPPORTED_CONVERSION at the
    API boundary); missing binary and timeouts raise RuntimeError.
    """
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

    timeout_value = timeout_seconds or settings.CONVERSION_TIMEOUT_SECONDS

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=timeout_value,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("FFmpeg tidak ditemukan pada PATH.") from exc
    except subprocess.TimeoutExpired as exc:
        output_path.unlink(missing_ok=True)
        raise RuntimeError(
            f"Conversion timed out after {timeout_value} seconds."
        ) from exc

    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        if not detail:
            detail = f"FFmpeg conversion failed with exit code {completed.returncode}."
        if len(detail) > _STDERR_DETAIL_LIMIT:
            detail = detail[-_STDERR_DETAIL_LIMIT:]
        from app.services.conversion_service import UnsupportedConversionError

        raise UnsupportedConversionError(
            source_path.suffix.lstrip("."),
            output_path.suffix.lstrip("."),
            message=f"FFmpeg could not convert this input: {detail}",
        )

    return output_path
