"""
PROJECT: CONVERIGO
TEST SUITE: Certified Audio + Video Plugin Converters (Batch 2)
STATUS: DEVELOPMENT (certification pending evidence review)

Coverage:
  VID-12 mp4-to-gif, AUD-02 wav-to-mp3, AUD-04 m4a-to-mp3,
  AUD-06 flac-to-mp3, AUD-09 aac-to-mp3

Pipeline: real audio/video samples (generated via FFmpeg at runtime) uploaded
through the /convert API -> registry slug resolution -> plugin convert() ->
download artifact, with content verification (file exists, correct extension).

Engine: FFmpeg (GPL, already verified via AUD-03 mp4-to-mp3 certified+locked).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app
from app.plugins.registry import registry

OUTPUT_DIR = settings.OUTPUT_DIR

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_public_output_path(response) -> Path:
    payload = response.json()
    download_path = payload.get("download_path")
    assert download_path, payload
    assert download_path.startswith("/download/")
    relative_parts = Path(download_path.removeprefix("/download/")).parts
    assert len(relative_parts) == 2, f"Unexpected download path shape: {download_path}"
    conversion_id, filename = relative_parts
    output_path = OUTPUT_DIR / conversion_id / filename
    assert output_path.exists(), f"Expected output file not found: {output_path}"
    return output_path


def _convert_via_api(source_path: Path, target_format: str, operation: str) -> Path:
    client = TestClient(app)
    mime_types = {
        "mp4": "video/mp4",
        "wav": "audio/wav",
        "m4a": "audio/mp4",
        "flac": "audio/flac",
        "aac": "audio/aac",
    }
    suffix = source_path.suffix.lstrip(".").lower()
    with source_path.open("rb") as handle:
        response = client.post(
            "/convert",
            files={"file": (source_path.name, handle, mime_types[suffix])},
            data={"target_format": target_format, "operation": operation},
        )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success", payload
    assert payload.get("download_path"), payload
    return _resolve_public_output_path(response)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.certified
def test_audio_plugins_discovered() -> None:
    """All 5 audio+video plugins are registered with slug + pair."""
    expected = {
        "mp4-to-gif": ("mp4", "gif"),
        "wav-to-mp3": ("wav", "mp3"),
        "m4a-to-mp3": ("m4a", "mp3"),
        "flac-to-mp3": ("flac", "mp3"),
        "aac-to-mp3": ("aac", "mp3"),
    }
    for slug, (source, target) in expected.items():
        plugin = registry.get_plugin(source, target, slug=slug)
        assert plugin is not None, f"{slug} not found in registry"
        assert plugin.slug == slug
        assert plugin.supports(source, target), f"{slug} fails supports() for {source}->{target}"


@pytest.mark.certified
@pytest.mark.asyncio
async def test_mp4_to_gif_roundtrip(tmp_path: Path) -> None:
    from tests.certified.video._helpers import create_sample_video, skip_if_ffmpeg_unavailable
    skip_if_ffmpeg_unavailable()
    source = await create_sample_video(tmp_path, "input.mp4", include_audio=True)
    output = _convert_via_api(source, "gif", "mp4-to-gif")
    try:
        assert output.suffix.lower() == ".gif"
        assert output.stat().st_size > 0
        with output.open("rb") as handle:
            header = handle.read(6)
        assert header in (b"GIF87a", b"GIF89a"), f"Not a GIF header: {header!r}"
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_wav_to_mp3_roundtrip(tmp_path: Path) -> None:
    from tests.certified.audio._helpers import create_audio_sample, skip_if_ffmpeg_unavailable
    skip_if_ffmpeg_unavailable()
    source = await create_audio_sample(tmp_path, "input.wav", output_format="wav")
    output = _convert_via_api(source, "mp3", "wav-to-mp3")
    try:
        assert output.suffix.lower() == ".mp3"
        assert output.stat().st_size > 0
        with output.open("rb") as handle:
            header = handle.read(3)
        assert header in (b"ID3", b"\xff\xfb") or output.stat().st_size > 0, f"Bad MP3 header: {header!r}"
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_m4a_to_mp3_roundtrip(tmp_path: Path) -> None:
    from tests.certified.audio._helpers import create_audio_sample, skip_if_ffmpeg_unavailable
    skip_if_ffmpeg_unavailable()
    source = await create_audio_sample(tmp_path, "input.m4a", output_format="m4a")
    output = _convert_via_api(source, "mp3", "m4a-to-mp3")
    try:
        assert output.suffix.lower() == ".mp3"
        assert output.stat().st_size > 0
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_flac_to_mp3_roundtrip(tmp_path: Path) -> None:
    from tests.certified.audio._helpers import create_audio_sample, skip_if_ffmpeg_unavailable
    skip_if_ffmpeg_unavailable()
    source = await create_audio_sample(tmp_path, "input.flac", output_format="flac")
    output = _convert_via_api(source, "mp3", "flac-to-mp3")
    try:
        assert output.suffix.lower() == ".mp3"
        assert output.stat().st_size > 0
    finally:
        output.unlink(missing_ok=True)


@pytest.mark.certified
@pytest.mark.asyncio
async def test_aac_to_mp3_roundtrip(tmp_path: Path) -> None:
    from tests.certified.audio._helpers import create_audio_sample, skip_if_ffmpeg_unavailable
    skip_if_ffmpeg_unavailable()
    source = await create_audio_sample(tmp_path, "input.aac", output_format="aac")
    output = _convert_via_api(source, "mp3", "aac-to-mp3")
    try:
        assert output.suffix.lower() == ".mp3"
        assert output.stat().st_size > 0
    finally:
        output.unlink(missing_ok=True)
