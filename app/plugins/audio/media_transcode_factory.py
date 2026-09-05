"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F4)
Version : 1.0.0

Audio side of Factory Batch F4 (cluster G-D) - two thin audio transcodes
built with the same F0 factory scaffolding as the eight video plugins in
app/plugins/video/media_transcode_factory.py:

    wav-to-flac, ogg-to-mp3 (Supervisor D10)

- wav-to-flac is a bit-exact PCM -> FLAC lossless rewrap (FLAC is
  lossless, so quality 95 is honest).
- ogg-to-mp3 follows the certified wav/m4a/aac/flac-to-mp3 precedent
  (libmp3lame); priority stays at 75 so the mature mp3-target plugins
  keep their ranking wherever they share a source.
- Honest error policy: FFmpeg failures map to UnsupportedConversionError
  via the shared F4 runner (app/factory/ffmpeg_runner.py), so corrupt or
  undecodable audio answers 422 UNSUPPORTED_CONVERSION.
"""
from __future__ import annotations

from pathlib import Path

from app.factory import make_plugin_class
from app.factory.ffmpeg_runner import run_ffmpeg


def _convert_wav_to_flac(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.flac"
    return run_ffmpeg(source_path, output_path, ["-acodec", "flac"])


def _convert_ogg_to_mp3(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.mp3"
    return run_ffmpeg(
        source_path,
        output_path,
        ["-acodec", "libmp3lame", "-b:a", "192k"],
    )


WAVToFLACPlugin = make_plugin_class(
    slug="wav-to-flac",
    source_formats=["wav"],
    target_formats=["flac"],
    engine_hook=_convert_wav_to_flac,
    name="WAV to FLAC",
    description=(
        "Convert WAV audio files to FLAC, a lossless compressed format "
        "that keeps every sample bit-exact."
    ),
    category="audio",
    engine="ffmpeg",
    goal="quality",
    priority=75,
    quality=95,
    compatibility=95,
    estimated_saving=5,
    badge="Lossless Audio",
    icon="🎵",
    use_case="Best for archiving WAV recordings at reduced size with zero loss.",
    seo_title="WAV to FLAC Converter | Converigo",
    seo_description="Convert WAV audio files to lossless FLAC format quickly and easily.",
    working_subdir="audio",
)

OGGToMP3Plugin = make_plugin_class(
    slug="ogg-to-mp3",
    source_formats=["ogg"],
    target_formats=["mp3"],
    engine_hook=_convert_ogg_to_mp3,
    name="OGG to MP3",
    description="Convert OGG audio files to widely compatible MP3 format.",
    category="audio",
    engine="ffmpeg",
    goal="quality",
    priority=75,
    quality=90,
    compatibility=95,
    estimated_saving=10,
    badge="Compressed Audio",
    icon="🎧",
    use_case="Best for making OGG audio playable on any MP3 device.",
    seo_title="OGG to MP3 Converter | Converigo",
    seo_description="Convert OGG audio files to MP3 format quickly and easily.",
    working_subdir="audio",
)
