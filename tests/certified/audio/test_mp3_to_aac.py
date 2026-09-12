"""
PROJECT: CONVERIGO
TEST SUITE: Certified Audio Factory Converter - mp3-to-aac (Phase 21.2 Batch 1)

Factory-built converter (app/factory make_plugin_class + run_ffmpeg), so the
uniform factory contract is asserted through the shared HTTP harness
(tests/certified/_factory_harness.py):

    plugin discovered -> POST /convert 201 -> GET /download 200 ->
    content valid -> honest 422 UNSUPPORTED_CONVERSION.

The source sample is generated at runtime with FFmpeg (same convention as the
rest of tests/certified/audio), so no binary fixture is checked in.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.certified._factory_harness import (
    assert_honest_unsupported,
    assert_slug_discovered,
    cleanup_output,
    post_convert,
    run_happy_path,
)
from tests.certified.audio._helpers import (
    create_audio_sample,
    skip_if_ffmpeg_unavailable,
)

SLUG = "mp3-to-aac"


@pytest.mark.certified
def test_mp3_to_aac_plugin_discovered() -> None:
    assert_slug_discovered(SLUG, "mp3", "aac")


@pytest.mark.certified
@pytest.mark.asyncio
async def test_mp3_to_aac_happy_path(tmp_path: Path) -> None:
    skip_if_ffmpeg_unavailable()

    source = await create_audio_sample(tmp_path, "input.mp3", output_format="mp3")
    output = run_happy_path(source, "aac", SLUG)
    try:
        assert output.suffix.lower() == ".aac", output
        assert output.stat().st_size > 0, "AAC output is empty"
    finally:
        cleanup_output(output)


@pytest.mark.certified
def test_mp3_to_aac_honest_422_for_undecodable_input(tmp_path: Path) -> None:
    """Corrupt bytes must answer the honest UNSUPPORTED_CONVERSION class."""
    bad = tmp_path / "bad.mp3"
    bad.write_bytes(b"not-a-real-mp3-payload" * 16)

    response = post_convert(bad, "aac", SLUG)
    assert_honest_unsupported(response)