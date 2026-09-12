"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / Phase 21.2 Batch 1)
Version : 1.0.0

WAV -> AAC - factory-built audio transcode (Phase 21.2 Batch 1).

Built on the F0 factory scaffolding (app/factory/plugin_base.py) together
with the F4 sync FFmpeg runner (app/factory/ffmpeg_runner.py), matching the
pattern of app/plugins/audio/media_transcode_factory.py.  Supervisor
decision for Batch 1: FACTORY pattern (make_plugin_class + run_ffmpeg) is
mandatory - not a thin hand-written class.

- wav-to-aac compresses uncompressed PCM WAV into AAC with the FFmpeg
  "aac" encoder (already present for the certified aac/m4a plugins - no
  new dependency).
- Priority 75: this slug shares the "wav" source with the certified
  wav-to-mp3 workhorse (priority 80), so the F3 lesson keeps every new
  share-source slug at 75 or below and /recommend stays baseline-stable.
- Honest error policy: a failing FFmpeg run is mapped to
  UnsupportedConversionError by the shared F4 runner, so corrupt or
  undecodable audio answers 422 UNSUPPORTED_CONVERSION - never a 500 or a
  fabricated output file.
"""
from __future__ import annotations

from pathlib import Path

from app.factory import make_plugin_class
from app.factory.ffmpeg_runner import run_ffmpeg


def _convert_wav_to_aac(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.aac"
    return run_ffmpeg(
        source_path,
        output_path,
        ["-vn", "-acodec", "aac", "-b:a", "128k"],
    )


WAVToAACPlugin = make_plugin_class(
    slug="wav-to-aac",
    source_formats=["wav"],
    target_formats=["aac"],
    engine_hook=_convert_wav_to_aac,
    name="WAV to AAC",
    description=(
        "Convert WAV audio files to AAC, shrinking uncompressed PCM into "
        "a compact format built for streaming and mobile playback."
    ),
    category="audio",
    engine="ffmpeg",
    goal="quality",
    priority=75,
    quality=90,
    compatibility=95,
    estimated_saving=80,
    badge="Compressed Audio",
    icon="🎧",
    use_case="Best for shrinking large WAV recordings into stream-ready AAC audio.",
    seo_title="WAV to AAC Converter | Converigo",
    seo_description="Convert WAV audio files to AAC format quickly and easily.",
    working_subdir="audio",
)