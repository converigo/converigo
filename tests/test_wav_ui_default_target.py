"""WS1 regression: homepage default target for .wav uploads must be MP3.

Production incident (2026-09-06): uploading a .wav on the homepage produced
a FLAC file. Verdict (f7_evidence/WS1_WAV_MP3_AUDIT_REPORT.md): NOT a
conversion bug — the backend (operation=wav-to-mp3) is correct; the FLAC
output was genuine FLAC produced by wav-to-flac because the homepage UI
defaulted to the first non-self entry of STATIC_TARGET_MAP.wav, which
commit 368475b (Factory F4) had reordered to ['FLAC', 'MP3'].

Root cause chain (converigo_main.html):
    const targets = getValidTargets(ext);            // = STATIC_TARGET_MAP[ext]
    let target = targets.find(t => t.toLowerCase() !== ext.toLowerCase()) || targets[0];
So the ARRAY ORDER of STATIC_TARGET_MAP *is* the homepage default-target
policy. The old certified test
(tests/certified/audio/test_audio_plugin_certified.py::test_wav_to_mp3_roundtrip)
exercises the FFmpegEngine with an explicit operation/target and could never
catch this — the regression lived entirely in the UI default-target chain.

These tests lock the full chain instead:
1. The SERVED homepage's STATIC_TARGET_MAP.wav must list MP3 first
   (array order locked explicitly, not just set membership).
2. Replaying the homepage's own default choice (first non-self target,
   ``target_format`` only, no ``operation`` — exactly what the homepage
   form posts) against the real /convert endpoint must yield a GENUINE
   MP3 file: magic bytes ID3 / MPEG frame sync, never fLaC or RIFF.
   This assertion is content-level on purpose (not filename/extension).
3. (Real browser) Dropping a .wav on the homepage must pre-select MP3
   in the row's format dropdown, with options ordered ['MP3', 'FLAC'].

Backlog (recorded, out of scope here): the certified suite should cover the
UI default-target for EVERY source with more than one target, not just wav —
see f7_evidence/BACKLOG.md.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import settings
from app.main import app


def get_base_url() -> str:
    import os

    return os.environ.get("CONVERIGO_BASE_URL", "http://127.0.0.1:8000")


# ---------------------------------------------------------------------------
# Helpers — mirror of the homepage UI contract
# ---------------------------------------------------------------------------

_MAP_BLOCK_RE = re.compile(r"const STATIC_TARGET_MAP = \{(.*?)\};", re.S)
_ENTRY_RE = re.compile(r"([A-Za-z0-9_]+):\[([^\]]*)\]")


def _served_static_target_map(client: TestClient) -> dict[str, list[str]]:
    """Parse STATIC_TARGET_MAP out of the SERVED homepage HTML.

    Parsing the rendered artifact (not a copy of the source) means any
    regression in what production actually ships is caught, not just the
    file in the repo.
    """
    response = client.get("/")
    assert response.status_code == 200
    match = _MAP_BLOCK_RE.search(response.text)
    assert match, "STATIC_TARGET_MAP not found in served homepage HTML"
    mapping: dict[str, list[str]] = {}
    for key, values in _ENTRY_RE.findall(match.group(1)):
        mapping[key] = [v.strip().strip("'\"") for v in values.split(",") if v.strip()]
    return mapping


def _homepage_default_target(targets: list[str], ext: str) -> str | None:
    """Exact Python mirror of converigo_main.html addFiles():
    ``targets.find(t => t.toLowerCase() !== ext.toLowerCase()) || targets[0]``.
    """
    return next(
        (t for t in targets if t.lower() != ext.lower()),
        targets[0] if targets else None,
    )


def _make_wav(tmp_path: Path) -> Path:
    from tests.certified.audio._helpers import create_audio_sample

    return asyncio.run(
        create_audio_sample(tmp_path, "homepage_default.wav", output_format="wav")
    )


def _resolve_output(download_path: str) -> Path:
    parts = [p for p in download_path.split("/") if p]
    assert len(parts) == 3 and parts[0] == "download", download_path
    return settings.OUTPUT_DIR / parts[1] / parts[2]


# ---------------------------------------------------------------------------
# 1. Served map: wav order locked (MP3 first)
# ---------------------------------------------------------------------------

def test_served_homepage_wav_default_target_is_mp3() -> None:
    client = TestClient(app)
    mapping = _served_static_target_map(client)
    # Full order lock — the whole point of WS1. FLAC must stay AVAILABLE,
    # but must not be the default.
    assert mapping["wav"] == ["MP3", "FLAC"], mapping["wav"]
    default = _homepage_default_target(mapping["wav"], "wav")
    assert default == "MP3", (
        f"Homepage default target for .wav resolved to {default!r}, expected 'MP3'"
    )


# ---------------------------------------------------------------------------
# 2. Homepage default flow e2e: .wav + UI-derived default => genuine MP3
# ---------------------------------------------------------------------------

def test_wav_uploaded_via_homepage_default_flow_yields_mp3_magic_bytes(tmp_path: Path) -> None:
    from tests.certified.audio._helpers import skip_if_ffmpeg_unavailable

    skip_if_ffmpeg_unavailable()
    sample = _make_wav(tmp_path)

    client = TestClient(app)
    mapping = _served_static_target_map(client)
    default = _homepage_default_target(mapping["wav"], "wav")
    assert default == "MP3"
    # Sanity: the input really is a WAV (RIFF), so MP3 magic in the output
    # cannot be explained by the input itself.
    assert sample.read_bytes()[:4] == b"RIFF"

    with sample.open("rb") as handle:
        response = client.post(
            "/convert",
            files={"file": (sample.name, handle, "audio/wav")},
            data={"target_format": default.lower()},  # homepage form: target only, NO operation
        )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload.get("status") == "success", payload
    assert payload.get("target_format") == "mp3", payload
    assert payload.get("filename", "").lower().endswith(".mp3"), payload

    download = client.get(payload["download_path"])
    assert download.status_code == 200
    body = download.content
    # Content-level assertions (magic bytes), never filename/extension:
    assert not body.startswith(b"fLaC"), "Homepage default produced FLAC — WS1 regression reintroduced"
    assert not body.startswith(b"RIFF"), "Output is still a WAV file"
    assert body[:3] == b"ID3" or body[:2] == b"\xff\xfb", (
        f"Output is not a genuine MP3 (header bytes: {body[:8].hex(' ')})"
    )


# ---------------------------------------------------------------------------
# 3. Real browser: .wav row pre-selects MP3
# ---------------------------------------------------------------------------

def test_browser_wav_row_defaults_to_mp3(tmp_path: Path, app_base_url) -> None:
    pytest.importorskip("playwright.sync_api")
    from tests.certified.audio._helpers import skip_if_ffmpeg_unavailable

    skip_if_ffmpeg_unavailable()
    sample = _make_wav(tmp_path)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#fileInput", state="attached", timeout=60000)
        page.locator("#fileInput").set_input_files(str(sample))
        page.wait_for_selector("#rows .row", timeout=30000)
        page.wait_for_timeout(500)
        row = page.locator("#rows .row").first
        select = row.locator("select.fmt")
        options = select.evaluate("el => Array.from(el.options).map(o => o.value)")
        selected = select.evaluate("el => el.value")
        browser.close()

    assert options == ["MP3", "FLAC"], f"Unexpected dropdown order: {options}"
    assert selected == "MP3", f"Homepage default selected {selected!r}, expected 'MP3'"

