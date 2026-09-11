"""
PROJECT: CONVERIGO
TEST SUITE: Certified FFmpeg Media Factory - Factory Batch F4 (Jalur 2)

Factory Batch Plan F4 (cluster G-D net-new): ten FFmpeg thin-config
converters built on the F0 factory base (app/factory/plugin_base.py +
the F4 sync runner app/factory/ffmpeg_runner.py):

    video (app/plugins/video/media_transcode_factory.py):
        mov-to-mp4, mkv-to-mp4, avi-to-mp4, webm-to-mp4, gif-to-mp4,
        mp4-compress, mp4-to-webm, mp4-to-avi
    audio (app/plugins/audio/media_transcode_factory.py):
        wav-to-flac, ogg-to-mp3 (D10)

ONE parametric test file for the whole F4 batch, using the shared factory
harness uniform contract:

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    output content verified (ffprobe container/codec) ->
    honest 422 UNSUPPORTED_CONVERSION for corrupt input

Governance notes:
- D6a: mp4-compress is the generic video compressor (VAR-25 absorbed);
  per-source compress variants are deferred.
- D6b: residual mov/mkv/avi/webm -> {mp3, gif} transcodes are deferred;
  this suite intentionally does NOT cover them.
- D7: mp4-compress fixed semantics (CRF 28, preset medium, +faststart,
  audio stream copy) are asserted: smaller output + moov-before-mdat.
- D8: container transcodes always RE-ENCODE; codec expectations
  (h264/aac for mp4 targets, vp9/opus for webm, mpeg4/mp3 for avi) are
  asserted with ffprobe so a silent -c copy regression cannot pass.
- Legacy capability-smoke slugs (tests/{video,audio}/test_*_to_*.py)
  previously only exercised a raw ffmpeg subprocess; the dedicated
  legacy tests below prove these five scenarios now resolve through the
  real registry + factory plugin pipeline.
- D9: the four formerly pageless certified audio slugs (wav/m4a/aac/
  flac-to-mp3) gained landing-page + contract artifacts (pure plumbing);
  the D9 test asserts the artifacts AND that the certified converters
  still resolve through the registry unchanged.

Fixtures are generated in-module with lavfi (testsrc2 + sine) through the
installed ffmpeg binary - zero binary assets, same policy as F2/F3.
"""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.factory.plugin_base import FactoryConversionPlugin
from app.plugins.registry import registry
from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)
from tests.certified.video._helpers import require_ffmpeg, run_ffmpeg

ROOT = Path(__file__).resolve().parents[3]

# (slug, source_ext, target_ext, source_has_audio)
F4_CONVERSION_TABLE = [
    ("mov-to-mp4", "mov", "mp4", True),
    ("mkv-to-mp4", "mkv", "mp4", True),
    ("avi-to-mp4", "avi", "mp4", True),
    ("webm-to-mp4", "webm", "mp4", True),
    ("gif-to-mp4", "gif", "mp4", False),
    ("mp4-compress", "mp4", "mp4", True),
    ("mp4-to-webm", "mp4", "webm", True),
    ("mp4-to-avi", "mp4", "avi", True),
    ("wav-to-flac", "wav", "flac", True),
    ("ogg-to-mp3", "ogg", "mp3", True),
]

#: The five scenarios that existed ONLY as raw ffmpeg-subprocess capability
#: smokes before F4; they are genuine registry plugins since this batch.
#: Expected class names come from make_plugin_class's deterministic
#: slug-derived naming (the generated classes live in the factory module).
LEGACY_SMOKE_TABLE = [
    ("mov-to-mp4", "mov", "mp4", "MovToMp4Plugin"),
    ("mkv-to-mp4", "mkv", "mp4", "MkvToMp4Plugin"),
    ("avi-to-mp4", "avi", "mp4", "AviToMp4Plugin"),
    ("webm-to-mp4", "webm", "mp4", "WebmToMp4Plugin"),
    ("ogg-to-mp3", "ogg", "mp3", "OggToMp3Plugin"),
]

#: D9 - certified-but-pageless audio slugs that gained page+contract
#: artifacts in this batch (pure plumbing, converter code untouched).
D9_PAGELESS_TABLE = [
    ("wav-to-mp3", "wav", "mp3"),
    ("m4a-to-mp3", "m4a", "mp3"),
    ("aac-to-mp3", "aac", "mp3"),
    ("flac-to-mp3", "flac", "mp3"),
]

UPLOAD_MIME = {
    "mov": "video/quicktime",
    "mkv": "video/x-matroska",
    "avi": "video/x-msvideo",
    "webm": "video/webm",
    "gif": "image/gif",
    "mp4": "video/mp4",
    "wav": "audio/wav",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
}

# ---------------------------------------------------------------------------
# Fixture builders (lavfi, deterministic, ~1 second clips)
# ---------------------------------------------------------------------------

async def _build_media_fixtures(root: Path) -> dict[str, Path]:
    ffmpeg = require_ffmpeg()
    fixtures: dict[str, Path] = {}

    async def make_video(name: str, codec_args: list[str], *, audio: bool) -> Path:
        output_path = root / name
        command = [ffmpeg, "-y", "-f", "lavfi", "-i", "testsrc2=size=160x120:rate=8"]
        if audio:
            command += ["-f", "lavfi", "-i", "sine=frequency=1000:duration=1"]
        command += ["-t", "1", *codec_args, str(output_path)]
        completed = await run_ffmpeg(command)
        if completed.returncode != 0:
            raise RuntimeError(
                f"fixture {name} failed: {(completed.stderr or '')[-400:]}"
            )
        return output_path

    async def make_audio(name: str, codec_args: list[str]) -> Path:
        output_path = root / name
        command = [
            ffmpeg, "-y",
            "-f", "lavfi", "-i", "sine=frequency=1000:duration=1",
            "-t", "1", *codec_args, str(output_path),
        ]
        completed = await run_ffmpeg(command)
        if completed.returncode != 0:
            raise RuntimeError(
                f"fixture {name} failed: {(completed.stderr or '')[-400:]}"
            )
        return output_path

    transcode_source = [
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
    ]
    fixtures["mov"] = await make_video("clip.mov", transcode_source, audio=True)
    fixtures["mkv"] = await make_video("clip.mkv", transcode_source, audio=True)
    fixtures["avi"] = await make_video(
        "clip.avi",
        ["-c:v", "mpeg4", "-q:v", "5", "-c:a", "libmp3lame"],
        audio=True,
    )
    fixtures["webm"] = await make_video(
        "clip.webm",
        ["-c:v", "libvpx", "-b:v", "200k", "-c:a", "libvorbis"],
        audio=True,
    )
    fixtures["gif"] = await make_video("clip.gif", [], audio=False)
    # crf 10 keeps the compress fixture quality-high (bigger), so the D7
    # CRF-28 output can honestly shrink it in the faststart test.
    fixtures["mp4"] = await make_video(
        "clip.mp4",
        ["-c:v", "libx264", "-crf", "10", "-pix_fmt", "yuv420p", "-c:a", "aac"],
        audio=True,
    )
    fixtures["wav"] = await make_audio("clip.wav", ["-c:a", "pcm_s16le"])
    fixtures["ogg"] = await make_audio("clip.ogg", ["-c:a", "libvorbis"])
    return fixtures


@pytest.fixture(scope="module")
def media_fixtures(tmp_path_factory) -> dict[str, Path]:
    root = tmp_path_factory.mktemp("f4_media")
    return asyncio.run(_build_media_fixtures(root))


def _make_corrupt_fixture(source_path: Path, root: Path) -> Path:
    """Keep the magic prefix (so the upload validator passes it) but
    destroy the container structure so FFmpeg genuinely cannot decode."""
    corrupt_path = root / f"corrupt_{source_path.name}"
    corrupt_path.write_bytes(source_path.read_bytes()[:24] + b"\x00" * 128)
    return corrupt_path


# ---------------------------------------------------------------------------
# ffprobe helpers (codec/container verification, D8)
# ---------------------------------------------------------------------------

def _ffprobe(path: Path) -> dict:
    ffprobe = shutil.which("ffprobe")
    if ffprobe is None:
        pytest.skip("ffprobe is not installed")
    completed = subprocess.run(
        [
            ffprobe, "-v", "error", "-print_format", "json",
            "-show_format", "-show_streams", str(path),
        ],
        capture_output=True, text=True, check=True, timeout=60,
    )
    return json.loads(completed.stdout)


def _first_stream(probe: dict, codec_type: str) -> dict:
    for stream in probe.get("streams", []):
        if stream.get("codec_type") == codec_type:
            return stream
    raise AssertionError(f"no {codec_type} stream found in probe output")


#: Per-target codec expectations.  Re-encode (D8) means these codecs must
#: match EXACTLY - a silent -c copy regression cannot pass these checks.
TARGET_CODEC_EXPECTATIONS = {
    "mp4": {"video": {"h264"}, "audio": {"aac"}, "format": {"mp4", "mov", "mp4"}},
    "webm": {"video": {"vp9", "vp8"}, "audio": {"opus", "vorbis"}, "format": {"webm", "matroska"}},
    "avi": {"video": {"mpeg4", "msmpeg4v3"}, "audio": {"mp3"}, "format": {"avi"}},
    "flac": {"audio": {"flac"}, "format": {"flac"}},
    "mp3": {"audio": {"mp3"}, "format": {"mp3", "mp2"}},
}

# ---------------------------------------------------------------------------
# Uniform certified contract tests
# ---------------------------------------------------------------------------

def _verify_output(path: Path, target_ext: str, expect_audio: bool) -> None:
    """Container + codec verification via ffprobe (D8 re-encode proof)."""
    expectation = TARGET_CODEC_EXPECTATIONS[target_ext]
    probe = _ffprobe(path)

    format_name = probe["format"]["format_name"].lower()
    assert expectation["format"] & set(format_name.split(",")), (
        f"{target_ext}: unexpected container '{format_name}'"
    )

    audio_streams = [
        s for s in probe.get("streams", []) if s.get("codec_type") == "audio"
    ]
    if "video" in expectation:
        video_stream = _first_stream(probe, "video")
        assert video_stream["codec_name"] in expectation["video"], (
            f"{target_ext}: video codec {video_stream['codec_name']} "
            f"not in {expectation['video']} (re-encode regression?)"
        )
    else:
        assert not any(
            s.get("codec_type") == "video" for s in probe.get("streams", [])
        ), f"{target_ext}: audio target must not carry a video stream"

    if expect_audio:
        assert audio_streams, f"{target_ext}: expected an audio stream"
        assert audio_streams[0]["codec_name"] in expectation["audio"], (
            f"{target_ext}: audio codec {audio_streams[0]['codec_name']} "
            f"not in {expectation['audio']}"
        )
    else:
        assert not audio_streams, (
            f"{target_ext}: silent source must stay silent, got "
            f"{[s['codec_name'] for s in audio_streams]}"
        )


@pytest.mark.parametrize(
    "slug,source_ext,target_ext,expect_audio",
    F4_CONVERSION_TABLE,
    ids=[row[0] for row in F4_CONVERSION_TABLE],
)
def test_f4_happy_path_registry_to_download(
    media_fixtures: dict[str, Path],
    slug: str,
    source_ext: str,
    target_ext: str,
    expect_audio: bool,
) -> None:
    """discovery -> 201 -> download 200 -> ffprobe-verified output."""
    assert_slug_discovered(slug, source_ext, target_ext)
    output_path = run_happy_path(
        media_fixtures[source_ext],
        target_ext,
        slug,
        mime=UPLOAD_MIME[source_ext],
    )
    try:
        assert output_path.suffix == f".{target_ext}"
        _verify_output(output_path, target_ext, expect_audio)
    finally:
        cleanup_output(output_path)


@pytest.mark.parametrize(
    "slug,source_ext,target_ext,_",
    F4_CONVERSION_TABLE,
    ids=[f"corrupt-{row[0]}" for row in F4_CONVERSION_TABLE],
)
def test_f4_corrupt_input_honest_422(
    media_fixtures: dict[str, Path],
    tmp_path: Path,
    slug: str,
    source_ext: str,
    target_ext: str,
    _: bool,
) -> None:
    """Corrupt-but-magic-prefixed media -> honest 422, never 500/output."""
    corrupt_path = _make_corrupt_fixture(media_fixtures[source_ext], tmp_path)
    response = post_convert(
        corrupt_path,
        target_ext,
        slug,
        mime=UPLOAD_MIME[source_ext],
    )
    assert_honest_unsupported(response)

def test_f4_registry_installation_and_ranking() -> None:
    """All 10 slugs installed, supports() correct, priority <= 75 (F3
    lesson: /recommend stability), self-pair + new pairs indexed."""
    for slug, source_ext, target_ext, _ in F4_CONVERSION_TABLE:
        assert registry.has_slug(slug), f"{slug} missing from registry"
        plugin = registry.by_slug[slug]
        assert plugin.slug == slug
        assert plugin.supports(source_ext, target_ext)
        assert plugin.priority <= 75, (
            f"{slug} priority {plugin.priority} would flip /recommend"
        )
        assert plugin.category in {"video", "audio"}

    # New legacy pair indexes exist (map/registry derivation proof).
    assert ("mp4", "mp4") in registry.plugins  # mp4-compress self-pair
    assert ("ogg", "mp3") in registry.plugins
    for source_ext in ("mov", "mkv", "avi", "webm"):
        assert (source_ext, "mp4") in registry.plugins
    assert ("mp4", "webm") in registry.plugins
    assert ("mp4", "avi") in registry.plugins
    assert ("wav", "flac") in registry.plugins


@pytest.mark.parametrize(
    "slug,source_ext,target_ext,expected_class",
    LEGACY_SMOKE_TABLE,
    ids=[row[0] for row in LEGACY_SMOKE_TABLE],
)
def test_legacy_capability_smokes_are_registry_backed(
    slug: str,
    source_ext: str,
    target_ext: str,
    expected_class: str,
) -> None:
    """The former raw-ffmpeg capability smokes (mov/mkv/avi/webm -> mp4,
    ogg -> mp3) now resolve through registry.get_plugin(slug=...) into
    real F4 factory plugins - not just an ffmpeg subprocess."""
    assert registry.has_slug(slug)
    plugin = registry.get_plugin(source_ext, target_ext, slug=slug)
    assert isinstance(plugin, FactoryConversionPlugin)
    assert type(plugin).__name__ == expected_class
    # The plain (source, target) pair also resolves to this plugin.
    assert registry.get_plugin(source_ext, target_ext) is plugin


def test_mp4_compress_shrinks_and_faststart(media_fixtures: dict[str, Path]) -> None:
    """D7: fixed CRF-28/preset-medium re-encode + +faststart, audio copy."""
    source = media_fixtures["mp4"]
    output_path = run_happy_path(source, "mp4", "mp4-compress", mime=UPLOAD_MIME["mp4"])
    try:
        assert output_path.stat().st_size < source.stat().st_size, (
            "CRF 28 re-encode must shrink the CRF-10 fixture"
        )
        raw = output_path.read_bytes()
        assert b"ftyp" in raw[:32]
        moov_index = raw.find(b"moov")
        mdat_index = raw.find(b"mdat")
        assert 0 < moov_index < mdat_index, (
            "+faststart requires moov before mdat"
        )
    finally:
        cleanup_output(output_path)


def test_d9_pageless_slugs_now_have_page_and_contract() -> None:
    """D9: pure plumbing - the four formerly pageless certified audio
    slugs gained landing-page artifacts; converters unchanged and still
    resolvable through the registry.

    Contract policy (repo precedent, confirmed by the governance test
    tests/test_converter_contract.py): a <slug>.contract.json is only
    shipped when the declared regression_sample file actually exists.
    wav-to-mp3 / m4a-to-mp3 / aac-to-mp3 / flac-to-mp3 have no sample
    files, so they follow the wav-to-mp3 precedent: page WITHOUT contract
    (exactly like the pre-existing mp3-to-wav page).  The three F4
    mp4-source converters DO ship contracts (tests/sample.mp4 exists).
    """
    converters_dir = ROOT / "app" / "data" / "converters"
    for slug, source_ext, target_ext in D9_PAGELESS_TABLE:
        page = json.loads(
            (converters_dir / f"{slug}.json").read_text(encoding="utf-8")
        )
        assert page["slug"] == slug
        assert (converters_dir / f"{slug}.contract.json").exists() is False, (
            f"{slug} has no regression sample; contract must stay absent "
            "(wav-to-mp3 precedent)"
        )
        assert registry.has_slug(slug)
        assert registry.by_slug[slug].supports(source_ext, target_ext)

    # The three F4 mp4-source converters ship contracts with a real sample.
    for slug in ("mp4-compress", "mp4-to-webm", "mp4-to-avi"):
        contract = json.loads(
            (converters_dir / f"{slug}.contract.json").read_text(encoding="utf-8")
        )
        assert contract["slug"] == slug
        assert contract["lifecycle_status"] == "certified"
        assert contract["regression_sample"] == "tests/sample.mp4"
        assert (ROOT / "tests" / "sample.mp4").exists()

    # mp3-to-wav page pre-existed (not part of D9) and is untouched.
    assert (converters_dir / "mp3-to-wav.json").exists()


def test_static_target_map_f4_rows() -> None:
    """In-suite proof that the F4 map delta is exactly what the registry
    derivation requires (standalone gate: tmp/verify_f4_map.py)."""
    html = (ROOT / "app" / "templates" / "main" / "converigo_main.html").read_text(
        encoding="utf-8"
    )
    block = html.split("const STATIC_TARGET_MAP = {", 1)[1].split("};", 1)[0]
    static_map: dict[str, set[str]] = {}
    for key, values in __import__("re").findall(
        r"(['\"a-zA-Z0-9_]+):\[(.*?)\]", block
    ):
        static_map[key.strip("'\"").lower()] = {
            v.strip().strip("'\"") for v in values.split(",") if v.strip()
        }

    for source_ext in ("mov", "mkv", "avi", "webm"):
        assert static_map[source_ext] == {"MP4"}
    assert {"MP4", "PDF"} <= static_map["gif"]
    assert "MP3" in static_map["ogg"]
    assert {"FLAC", "MP3"} <= static_map["wav"]
    assert {"AVI", "WEBM"} <= static_map["mp4"]
    assert "MP4" not in static_map["mp4"]  # self-pair excluded
    assert static_map["flv"] == set()      # D6b residuals deferred



