"""Phase 25.x RC-1: the homepage bulk selector must mirror the row consensus.

Production incident (audited in Phase 25.x): on the homepage, uploading an MP4
and choosing MP3 in the row still converted to AAC.

Root cause (``app/templates/main/converigo_main.html``, ``buildGlobalFmt()``):
the function computes ``pendingTargets`` / ``sameTarget`` - the target every
pending row already agrees on - and then throws that value away, seeding the
visible ``#globalFmt`` from ``STATIC_TARGET_MAP`` array order instead.
``convertAll()`` gives an unhidden ``#globalFmt`` unconditional precedence
over ``job.target`` (intentional), so the array-order default silently replaced
the user's row-level choice before the request was ever sent.

These tests lock the whole chain - displayed selector, persisted job state and
the emitted payload - rather than the map ordering that
``tests/test_wav_ui_default_target.py`` already covers.

Layers:
1. ``test_bulk_selector_seeded_from_row_consensus`` - always-on structural
   guard on the template source (works with no Node and no browser).
2. ``test_node_behavioural_suite`` - executes the REAL sliced template code
   (addFiles -> row change -> buildGlobalFmt -> convertAll -> convertJob) in a
   Node DOM stub and asserts display/state/payload agreement across the audio,
   image and document families, plus the P5/P6 non-regression cases.
3. ``test_node_suite_is_not_vacuous`` - re-applies the pre-fix block into a
   scratch copy and proves layer 2 actually fails on the broken logic.
4. ``test_browser_row_pick_survives_bulk_selector`` - real Chromium against a
   real server: MP4 + MP3 row pick must show MP3, post target_format=MP3 and
   deliver genuine MP3 bytes.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "app" / "templates" / "main" / "converigo_main.html"
HARNESS = Path(__file__).resolve().parent / "js" / "globalfmt_rc1_harness.mjs"
SUITE = Path(__file__).resolve().parent / "js" / "globalfmt_rc1.test.mjs"

# The pre-fix seeding block, verbatim from origin/main@dc1433b. Only used to
# prove the suite fails when the bug is present (layer 3); it is never imported
# into a live assertion.
PREFIX_BLOCK = """    const current = sel.value;
    sel.innerHTML = opts.map(t=>`<option value="${t}">${t}</option>`).join('');
    if(opts.includes(current)) {
      sel.value = current;
    } else {
      const sourceFormats = new Set(
        pending.map(j => String(j.ext || '').toLowerCase().replace(/^\\./, ''))
      );
      sel.value = opts.find(option => !sourceFormats.has(option.toLowerCase())) || opts[0];
    }
"""

node_available = shutil.which("node") is not None
needs_node = pytest.mark.skipif(not node_available, reason="node runtime not available")


def _seed_block() -> str:
    """Return the option-seeding tail of buildGlobalFmt() from the template."""
    src = TEMPLATE.read_text(encoding="utf-8")
    start = src.index("function buildGlobalFmt()")
    end = src.index("function conversionErrorMessage", start)
    return src[start:end]


def _reverted_template_text() -> str:
    """Current template with the RC-1 seeding block swapped back to pre-fix logic."""
    src = TEMPLATE.read_text(encoding="utf-8").replace("\r\n", "\n")
    pattern = re.compile(
        r"    const current = sel\.value;\n.*?    sel\.dataset\.consensus = consensus;\n",
        re.S,
    )
    reverted, count = pattern.subn(PREFIX_BLOCK, src)
    assert count == 1, (
        "RC-1 seeding block not found in the template - the revert fixture is "
        "stale and layer 3 can no longer prove anything; update PREFIX_BLOCK."
    )
    return reverted


def _run_node_suite(tmp_path: Path | None = None, template_text: str | None = None,
                    env_extra: dict | None = None):
    """Run the behavioural suite; returns (returncode, parsed summary, stderr)."""
    cmd = ["node", str(SUITE)]
    if tmp_path is not None:
        # Mirror the layout the harness resolves TEMPLATE from:
        # <root>/tests/js/*.mjs  +  <root>/app/templates/main/*.html
        (tmp_path / "tests" / "js").mkdir(parents=True, exist_ok=True)
        (tmp_path / "app" / "templates" / "main").mkdir(parents=True, exist_ok=True)
        shutil.copy(HARNESS, tmp_path / "tests" / "js" / HARNESS.name)
        shutil.copy(SUITE, tmp_path / "tests" / "js" / SUITE.name)
        target = tmp_path / "app" / "templates" / "main" / TEMPLATE.name
        if template_text is None:
            shutil.copy(TEMPLATE, target)
        else:
            target.write_text(template_text, encoding="utf-8")
        cmd = ["node", str(tmp_path / "tests" / "js" / SUITE.name)]
    env = {**os.environ, **(env_extra or {})}
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env)
    try:
        summary = json.loads(proc.stdout)
    except json.JSONDecodeError:
        summary = None
    return proc.returncode, summary, proc.stderr


# ---------------------------------------------------------------------------
# 1. Structural guard on the template (no Node, no browser required).
# ---------------------------------------------------------------------------

def test_bulk_selector_seeded_from_row_consensus() -> None:
    """buildGlobalFmt() must seed #globalFmt from pendingTargets[0].

    Guards the exact shape of the RC-1 defect: computing the row consensus and
    then ignoring it while seeding the visible selector from array order.
    """
    body = _seed_block()
    assert "const consensus = pendingTargets[0];" in body, (
        "buildGlobalFmt() no longer derives the row consensus from pendingTargets[0]; "
        "the bulk selector cannot mirror what the rows agree on."
    )
    assert re.search(r"if\s*\(.*?\)\s*\{\s*sel\.value\s*=\s*consensus\s*;", body, re.S), (
        "#globalFmt is not seeded from the row consensus. Pre-fix behaviour "
        "(STATIC_TARGET_MAP array-order seeding) lets convertAll()'s bulk-wins "
        "precedence overwrite a correct row target."
    )
    # The array-order value may only remain the last-resort fallback, i.e. it
    # must sit after the consensus arm and inside a trailing else-branch.
    consensus_at = body.index("sel.value = consensus")
    array_order_at = body.index("sel.value = opts.find(option => !sourceFormats.has")
    assert consensus_at < array_order_at, (
        "array-order seeding must stay a fallback, not the primary seed"
    )
    assert re.search(r"\}\s*else(?:\s*if)?\s*\{", body[consensus_at:array_order_at]), (
        "array-order seeding is no longer guarded behind an else-branch"
    )


def test_row_precedence_is_untouched() -> None:
    """P5/P6 are explicitly out of scope: convertAll() must stay as it was."""
    src = TEMPLATE.read_text(encoding="utf-8")
    start = src.index("function convertAll()")
    body = src[start:src.index("/* ---------------- download", start)]
    assert "globalFormat?.offsetParent !== null && globalFormat?.value" in body, (
        "convertAll() bulk precedence changed - RC-1 is frontend seeding only"
    )
    assert "rowFormat" in body, "convertAll() row fallback removed (P6 must stay)"


# ---------------------------------------------------------------------------
# 2/3. Behavioural suite over the real sliced template code.
# ---------------------------------------------------------------------------

EXPECTED_CASES = {
    "seed: mp4 + user picks MP3",
    "P1 auto-default policy untouched (mp4 still auto-picks AAC)",
    "image: jpg + user picks WEBP",
    "document: pdf + user picks DOCX",
    "audio: wav + user picks FLAC",
    "two rows agreeing on MP3 -> bulk shows and sends MP3",
    "rows disagree -> selector hidden, row targets win",
    "explicit bulk pick still wins (P5 intact)",
    "untouched render still shows the auto default",
}


@needs_node
def test_node_behavioural_suite() -> None:
    code, summary, stderr = _run_node_suite()
    assert summary is not None, f"suite produced no JSON summary; stderr:\n{stderr}"
    ran = {case["name"] for case in summary["results"]}
    assert EXPECTED_CASES <= ran, f"suite silently skipped cases: {EXPECTED_CASES - ran}"
    failed = [case for case in summary["results"] if not case["pass"]]
    assert not failed, "homepage target-selection regression:\n" + json.dumps(failed, indent=2)
    assert code == 0


@needs_node
def test_node_suite_is_not_vacuous(tmp_path: Path) -> None:
    """The same suite must fail loudly when the pre-fix logic is restored."""
    code, summary, stderr = _run_node_suite(
        tmp_path=tmp_path,
        template_text=_reverted_template_text(),
        env_extra={"RC1_ALLOW_PREFIX": "1"},
    )
    assert summary is not None, f"reverted suite produced no JSON; stderr:\n{stderr}"
    assert code != 0, "the behavioural suite passes against the PRE-FIX template - it proves nothing"
    by_name = {case["name"]: case for case in summary["results"]}
    seed = by_name["seed: mp4 + user picks MP3"]
    assert not seed["pass"], "MP4 + row pick MP3 did not regress without the fix"
    assert any('want "MP3"' in message for message in seed["failures"]), seed["failures"]
    # P6 is untouched by the fix, so that case must still pass pre-fix too.
    assert by_name["rows disagree -> selector hidden, row targets win"]["pass"]


# ---------------------------------------------------------------------------
# 4. Real browser + real server + real conversion.
# ---------------------------------------------------------------------------

_TARGET_FIELD_RE = re.compile(rb'name="target_format"\r\n\r\n([^\r\n]*)')


def _make_mp4(tmp_path: Path) -> Path:
    probe = subprocess.run(["ffmpeg", "-version"], capture_output=True)
    if probe.returncode != 0:
        pytest.skip("ffmpeg not available to synthesise a real MP4")
    out = tmp_path / "rc1_sample.mp4"
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", "sine=frequency=440:duration=1",
            "-f", "lavfi", "-i", "color=c=black:s=16x16:d=1",
            "-shortest", "-pix_fmt", "yuv420p", str(out),
        ],
        check=True, capture_output=True,
    )
    assert out.exists() and out.stat().st_size > 0
    return out


def test_browser_row_pick_survives_bulk_selector(tmp_path: Path, app_base_url) -> None:
    """Full AC chain in a real browser: row pick -> bulk display -> payload -> bytes."""
    pytest.importorskip("playwright.sync_api")
    from playwright.sync_api import sync_playwright

    mp4 = _make_mp4(tmp_path)
    posted: dict[str, str | None] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def capture(route):
            body = route.request.post_data_buffer or b""
            match = _TARGET_FIELD_RE.search(body)
            posted["target_format"] = match.group(1).decode() if match else None
            route.continue_()

        page.route("**/convert", capture)
        page.goto(app_base_url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#fileInput", state="attached", timeout=60000)
        page.set_input_files("#fileInput", str(mp4))
        page.wait_for_selector("#rows .row", timeout=60000)
        page.wait_for_timeout(400)

        auto_default = page.locator("#globalFmt").input_value()
        page.select_option("#rows .row select.fmt", "MP3")
        page.wait_for_timeout(400)
        shown_bulk = page.locator("#globalFmt").input_value()
        bulk_visible = page.locator("#globalFmt").is_visible()

        with page.expect_response(
            lambda r: r.url.endswith("/convert") and r.request.method == "POST",
            timeout=180000,
        ) as info:
            page.click("#goBtn")
        response = info.value
        result = response.json()
        download_path = result.get("download_path") or ""
        delivered = page.request.get(app_base_url.rstrip("/") + download_path).body()
        browser.close()

    assert response.status == 201, result
    # P1 (auto default) is intentionally unchanged by RC-1...
    assert auto_default == "AAC", f"auto default changed: {auto_default!r}"
    # ...but once the user states a target, the bulk control must follow it.
    assert bulk_visible, "bulk selector should stay visible while one row is unopposed"
    assert shown_bulk == "MP3", (
        f"#globalFmt displayed {shown_bulk!r} while the row said MP3 - RC-1 reintroduced"
    )
    assert posted.get("target_format") == "MP3", f"payload target_format={posted.get('target_format')!r}"
    # The delivered bytes must be the truth, not just the label.
    assert delivered[:3] == b"ID3" or delivered[:2] in (b"\xff\xfb", b"\xff\xf3"), (
        f"delivered output is not MP3 (header {delivered[:8].hex(' ')})"
    )
    assert not delivered.startswith(b"fLaC") and not delivered.startswith(b"RIFF")

