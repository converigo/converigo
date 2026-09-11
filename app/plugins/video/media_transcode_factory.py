"""
Project : Converigo
Author  : Converigo Factory (Jalur 2 / F4)
Version : 1.0.0

FFmpeg Media Transcode Factory Batch F4 - cluster G-D (net-new thin-config).

Eight video transcodes built on the F0 factory scaffolding
(app/factory/plugin_base.py + the F4 sync runner
app/factory/ffmpeg_runner.py).  The two F4 audio slugs (wav-to-flac,
ogg-to-mp3, D10) live in app/plugins/audio/media_transcode_factory.py
with the identical pattern.

Slugs in this file (8):
    mov-to-mp4, mkv-to-mp4, avi-to-mp4, webm-to-mp4, gif-to-mp4,
    mp4-compress, mp4-to-webm, mp4-to-avi

Supervisor decisions applied (F4 audit tmp/f4_ffmpeg_audit.md):
- D6a: mp4-compress absorbs the VAR-25 generic "video-compress" idea;
  per-source compress variants are DEFERRED.
- D6b: residual mov/mkv/avi/webm -> {mp3, gif} transcodes are DEFERRED to
  a later batch; this batch ships the container/codec core only.
- D7: mp4-compress uses FIXED semantics: CRF 28 + preset medium +
  +faststart + audio stream copy (-c:a copy).
- D8: container transcodes ALWAYS re-encode (never -c copy) with
  libx264 + aac and only the first video stream plus the first audio
  stream (-map 0:v:0 -map 0:a:0).  The audio map is spelled
  ``-map 0:a:0?`` (optional stream) so audio-less sources (animated GIF,
  silent recordings) still transcode instead of failing with a spurious
  "matches no streams" error; when audio exists, exactly the first audio
  stream is taken, which is the D8 semantics.
- D10: ogg-to-mp3 ships as the 10th slug (audio factory file; libmp3lame
  is already a production encoder via the certified audio plugins).

Key difference vs F2/F3: the map delta is NON-ZERO.  mov/mkv/avi/webm/gif/
ogg become dropdown sources, mp4 gains AVI/WEBM and wav gains FLAC.
Proof gate: tmp/verify_f4_map.py must show map == registry derivation.

Honest error policy: every failing FFmpeg run inside these hooks is
mapped to UnsupportedConversionError by the shared F4 runner, so corrupt
or undecodable media answers 422 UNSUPPORTED_CONVERSION - never a 500 or
a fabricated output file.

Priority policy (F3 lesson): every new share-source slug ranks at 75 or
below, so /recommend keeps the certified workhorses (mp4-to-* at 80,
wav-to-mp3 at 80) ranked first and stays baseline-stable.
"""
from __future__ import annotations

from pathlib import Path

from app.factory import make_plugin_class
from app.factory.ffmpeg_runner import run_ffmpeg

#: D8 re-encode argument set: first video + first audio stream only,
#: always re-encoded to web-safe H.264 / AAC.  The ``?`` makes the audio
#: map optional so silent sources (animated GIF) do not fail the mux.
_CONTAINER_TO_MP4_ARGUMENTS = [
    "-map", "0:v:0",
    "-map", "0:a:0?",
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-c:a", "aac",
]

#: D7 fixed mp4-compress semantics: CRF 28, preset medium, +faststart,
#: audio stream copy (no audio re-encode quality loss).
_MP4_COMPRESS_ARGUMENTS = [
    "-map", "0:v:0",
    "-map", "0:a:0?",
    "-c:v", "libx264",
    "-crf", "28",
    "-preset", "medium",
    "-pix_fmt", "yuv420p",
    "-c:a", "copy",
    "-movflags", "+faststart",
]

#: mp4-to-webm: VP9 + Opus, size-prioritized CRF (webm needs VP8/VP9 and
#: Vorbis/Opus streams; re-encode, D8).
_MP4_TO_WEBM_ARGUMENTS = [
    "-map", "0:v:0",
    "-map", "0:a:0?",
    "-c:v", "libvpx-vp9",
    "-crf", "40",
    "-b:v", "0",
    "-pix_fmt", "yuv420p",
    "-c:a", "libopus",
    "-b:a", "96k",
]

#: mp4-to-avi: MPEG-4 Part 2 + MP3 - the universally playable legacy AVI
#: combination (H.264/AAC-in-AVI is container-legal but far less
#: interoperable; the AVI target is about legacy compatibility).
_MP4_TO_AVI_ARGUMENTS = [
    "-map", "0:v:0",
    "-map", "0:a:0?",
    "-c:v", "mpeg4",
    "-q:v", "5",
    "-pix_fmt", "yuv420p",
    "-c:a", "libmp3lame",
    "-b:a", "128k",
]


def _convert_to_mp4(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.mp4"
    return run_ffmpeg(source_path, output_path, _CONTAINER_TO_MP4_ARGUMENTS)


def _convert_mp4_compress(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.mp4"
    return run_ffmpeg(source_path, output_path, _MP4_COMPRESS_ARGUMENTS)


def _convert_mp4_to_webm(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.webm"
    return run_ffmpeg(source_path, output_path, _MP4_TO_WEBM_ARGUMENTS)


def _convert_mp4_to_avi(
    plugin,
    source_path: Path,
    target_format: str,
    working_root: Path,
) -> Path:
    output_path = working_root / f"{source_path.stem}.avi"
    return run_ffmpeg(source_path, output_path, _MP4_TO_AVI_ARGUMENTS)

#: Shared identity defaults for the eight video factory plugins
#: (priority <= 75: F3 lesson, /recommend stability).
_MP4_TARGET_DEFAULTS = dict(
    category="video",
    engine="ffmpeg",
    goal="playback",
    priority=75,
    quality=85,
    compatibility=90,
    estimated_saving=10,
    working_subdir="video",
)


MovToMP4Plugin = make_plugin_class(
    slug="mov-to-mp4",
    source_formats=["mov"],
    target_formats=["mp4"],
    engine_hook=_convert_to_mp4,
    name="MOV to MP4",
    description=(
        "Convert QuickTime MOV videos to universally playable MP4 "
        "(H.264 + AAC re-encode, first video/audio streams)."
    ),
    badge="Universal Playback",
    icon="🎬",
    use_case="Best for making iPhone/QuickTime recordings playable everywhere.",
    seo_title="MOV to MP4 Converter | Converigo",
    seo_description="Convert MOV videos to MP4 format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

MkvToMP4Plugin = make_plugin_class(
    slug="mkv-to-mp4",
    source_formats=["mkv"],
    target_formats=["mp4"],
    engine_hook=_convert_to_mp4,
    name="MKV to MP4",
    description=(
        "Convert Matroska MKV videos to universally playable MP4 "
        "(H.264 + AAC re-encode, first video/audio streams)."
    ),
    badge="Universal Playback",
    icon="🎬",
    use_case="Best for making MKV downloads playable on phones and TVs.",
    seo_title="MKV to MP4 Converter | Converigo",
    seo_description="Convert MKV videos to MP4 format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

AviToMP4Plugin = make_plugin_class(
    slug="avi-to-mp4",
    source_formats=["avi"],
    target_formats=["mp4"],
    engine_hook=_convert_to_mp4,
    name="AVI to MP4",
    description=(
        "Convert legacy AVI videos to universally playable MP4 "
        "(H.264 + AAC re-encode, first video/audio streams)."
    ),
    badge="Modernize AVI",
    icon="🎬",
    use_case="Best for modernizing old AVI recordings for web playback.",
    seo_title="AVI to MP4 Converter | Converigo",
    seo_description="Convert AVI videos to MP4 format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

WebmToMP4Plugin = make_plugin_class(
    slug="webm-to-mp4",
    source_formats=["webm"],
    target_formats=["mp4"],
    engine_hook=_convert_to_mp4,
    name="WEBM to MP4",
    description=(
        "Convert WebM videos to universally playable MP4 "
        "(H.264 + AAC re-encode, first video/audio streams)."
    ),
    badge="Universal Playback",
    icon="🎬",
    use_case="Best for making WebM clips playable on Apple devices.",
    seo_title="WEBM to MP4 Converter | Converigo",
    seo_description="Convert WebM videos to MP4 format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

GifToMP4Plugin = make_plugin_class(
    slug="gif-to-mp4",
    source_formats=["gif"],
    target_formats=["mp4"],
    engine_hook=_convert_to_mp4,
    name="GIF to MP4",
    description=(
        "Convert animated GIF images to compact MP4 video clips "
        "(H.264 re-encode; silent sources simply stay silent)."
    ),
    badge="Animate Everywhere",
    icon="🎞️",
    use_case="Best for turning animated GIFs into lightweight MP4 clips.",
    seo_title="GIF to MP4 Converter | Converigo",
    seo_description="Convert animated GIF images to MP4 video clips.",
    **_MP4_TARGET_DEFAULTS,
)

MP4CompressPlugin = make_plugin_class(
    slug="mp4-compress",
    source_formats=["mp4"],
    target_formats=["mp4"],
    engine_hook=_convert_mp4_compress,
    name="MP4 Compress",
    description=(
        "Re-encode MP4 videos with a fixed, size-prioritized quality "
        "(CRF 28, preset medium, +faststart, audio stream copy) to "
        "shrink file size."
    ),
    badge="Smaller File",
    icon="🗜️",
    use_case="Best for shrinking large MP4 recordings before sharing.",
    seo_title="MP4 Compressor | Converigo",
    seo_description="Compress MP4 videos to smaller file sizes quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

MP4ToWebmPlugin = make_plugin_class(
    slug="mp4-to-webm",
    source_formats=["mp4"],
    target_formats=["webm"],
    engine_hook=_convert_mp4_to_webm,
    name="MP4 to WEBM",
    description=(
        "Convert MP4 videos to WebM (VP9 + Opus re-encode) for efficient "
        "HTML5 web playback."
    ),
    badge="Web Optimized",
    icon="🌐",
    use_case="Best for embedding videos on websites with efficient streaming.",
    seo_title="MP4 to WEBM Converter | Converigo",
    seo_description="Convert MP4 videos to WebM format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

MP4ToAviPlugin = make_plugin_class(
    slug="mp4-to-avi",
    source_formats=["mp4"],
    target_formats=["avi"],
    engine_hook=_convert_mp4_to_avi,
    name="MP4 to AVI",
    description=(
        "Convert MP4 videos to legacy AVI (MPEG-4 Part 2 + MP3) for old "
        "players and devices."
    ),
    badge="Legacy Friendly",
    icon="📼",
    use_case="Best for keeping old players and car media units happy.",
    seo_title="MP4 to AVI Converter | Converigo",
    seo_description="Convert MP4 videos to AVI format quickly and easily.",
    **_MP4_TARGET_DEFAULTS,
)

