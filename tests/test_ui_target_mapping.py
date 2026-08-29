"""P1a: Verify the converter dropdown matches the registry for every source format.

This is a permanent regression test for P1a (STATIC_TARGET_MAP).
It derives the expected per-source target list DIRECTLY from the converter
plugin registry (app.plugins.discover_plugins), using the same enumeration
of source_formats/target_formats that was used to build the static map.
Self-conversions (source==target) are excluded.

Additionally, it verifies that the marquee, orbit, and morph badge are
unaffected (they still use the CATEGORY object, which is unchanged).
"""
import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

from app.plugins import discover_plugins

pytestmark = pytest.mark.usefixtures("app_base_url")


def _build_expected_targets() -> dict[str, list[str]]:
    """Derive expected per-source target list from the plugin registry.

    Iterates all discovered plugin classes, collects their source_formats and
    target_formats (which already enumerate alias tokens such as 'word',
    'spreadsheet', 'powerpoint'), and for each source format collects the set
    of unique target formats, excluding self-conversions (source==target).
    This exactly mirrors how the registry dump (audit_collect.json) was built
    and how STATIC_TARGET_MAP in the HTML was derived.
    """
    result = discover_plugins()
    raw: dict[str, set[str]] = {}
    for cls in result.plugin_classes:
        srcs = getattr(cls, "source_formats", []) or []
        tgts = getattr(cls, "target_formats", []) or []
        for src in srcs:
            src = src.lower()
            for tgt in tgts:
                tgt = tgt.lower()
                if src == tgt:
                    continue  # skip self-conversion
                raw.setdefault(src, set()).add(tgt.upper())
    return {k: sorted(v) for k, v in sorted(raw.items())}


def _expected_for(ext: str, expected_map: dict[str, list[str]]) -> list[str]:
    return expected_map.get(ext, [])


# ---------------------------------------------------------------------------
# Fixture mapping — mirrors audit_phase_a_matrix.py _fixture_for_source
# ---------------------------------------------------------------------------
TESTS_DIR = Path(__file__).resolve().parent

FIXTURE_MAP: dict[str, Path] = {
    "7z": TESTS_DIR / "sample.7z",
    "avif": TESTS_DIR / "sample.avif",
    "bmp": TESTS_DIR / "sample.bmp",
    "csv": TESTS_DIR / "sample.csv",
    "doc": TESTS_DIR / "sample.docx",
    "docx": TESTS_DIR / "sample.docx",
    "gz": TESTS_DIR / "sample.gz",
    "gzip": TESTS_DIR / "sample.gz",
    "heic": TESTS_DIR / "sample.heic",
    "heif": TESTS_DIR / "sample.heic",
    "ico": TESTS_DIR / "sample.jpg",
    "jpeg": TESTS_DIR / "sample.jpg",
    "jpg": TESTS_DIR / "sample.jpg",
    "m4a": TESTS_DIR / "assets" / "regression" / "generated_tone.m4a",
    "mp3": TESTS_DIR / "sample.mp3",
    "mp4": TESTS_DIR / "sample.mp4",
    "ods": TESTS_DIR / "sample.ods",
    "odt": TESTS_DIR / "sample.odt",
    "pdf": TESTS_DIR / "sample.pdf",
    "png": TESTS_DIR / "sample.png",
    "powerpoint": TESTS_DIR / "sample.pptx",
    "ppt": TESTS_DIR / "sample.pptx",
    "pptx": TESTS_DIR / "sample.pptx",
    "rar": TESTS_DIR / "sample.rar",
    "spreadsheet": TESTS_DIR / "sample.xlsx",
    "svg": TESTS_DIR / "sample.svg",
    "tar": TESTS_DIR / "sample.tar",
    "tiff": TESTS_DIR / "sample.tiff",
    "txt": TESTS_DIR / "sample.txt",
    "webp": TESTS_DIR / "sample.webp",
    "word": TESTS_DIR / "sample.docx",
    "xls": TESTS_DIR / "sample.xlsx",
    "xlsx": TESTS_DIR / "sample.xlsx",
    "zip": TESTS_DIR / "sample.zip",
}


def get_base_url() -> str:
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError(
            "CONVERIGO_BASE_URL is not set; requires the app_base_url fixture."
        )
    return base_url


TIMEOUT = 180000
# ---------------------------------------------------------------------------
# Test: dropdown matches registry per source format (0 FP / 0 FN)
# ---------------------------------------------------------------------------
def test_ui_target_mapping_matches_registry() -> None:
    """For every source format with a fixture, upload and verify the
    dropdown options exactly match the registry-derived expected list."""
    expected = _build_expected_targets()

    sources_to_test = sorted(
        s for s, p in FIXTURE_MAP.items() if p.exists() and s in expected
    )

    if not sources_to_test:
        pytest.skip("No fixture files found for any registry source format.")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#fileInput", state="attached", timeout=TIMEOUT)

        file_paths = [FIXTURE_MAP[s] for s in sources_to_test]
        page.locator("#fileInput").set_input_files([str(fp) for fp in file_paths])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)
        page.wait_for_timeout(500)

        rows = page.locator("#rows .row")
        row_count = rows.count()
        assert row_count == len(sources_to_test), (
            f"Expected {len(sources_to_test)} rows, got {row_count}"
        )

        for i in range(row_count):
            row = rows.nth(i)
            name = row.locator(".row-name").inner_text()
            ext = (name.rsplit(".", 1)[-1] if "." in name else name).lower()

            exp = _expected_for(ext, expected)
            if exp:
                opts = row.locator("select.fmt").evaluate(
                    "el => Array.from(el.options).map(o => o.value)"
                )
                assert opts == exp, (
                    f"FP ({ext}): dropdown options {opts} != expected {exp}"
                )
            else:
                select_count = row.locator("select.fmt").count()
                no_conv_count = row.locator(".no-converter").count()
                assert select_count == 0, (
                    f"FN ({ext}): unexpected select.fmt present (expected no-converter)"
                )
                assert no_conv_count == 1, (
                    f"FN ({ext}): expected .no-converter span but got select_count={select_count}, no_conv_count={no_conv_count}"
                )

        # 0 FP / 0 FN across all tested sources
        browser.close()


# ---------------------------------------------------------------------------
# Regression: marquee, orbit, morph badge unchanged
# ---------------------------------------------------------------------------
def test_marquee_orbit_morph_unchanged() -> None:
    """Verify marquee, orbit, and morph badge still render correctly
    (they use the CATEGORY object, which is untouched by P1a)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("#fileInput", state="attached", timeout=TIMEOUT)

        page.wait_for_timeout(2000)

        chips_a = page.locator("#trackA .chip").count()
        chips_b = page.locator("#trackB .chip").count()
        assert chips_a > 0, "trackA has no chips (marquee empty)"
        assert chips_b > 0, "trackB has no chips (marquee empty)"

        orbit_icons = page.locator("#orbitField .ic").count()
        assert orbit_icons >= 5, (
            f"Expected at least 5 orbit icons, got {orbit_icons}"
        )

        morph_text = page.evaluate(
            "() => (document.getElementById('morphLabel') || {}).textContent"
        )
        assert morph_text and len(morph_text.strip()) > 0, (
            "morphLabel is empty or missing"
        )

        cat_keys = page.evaluate(
            "() => { const c = typeof CATEGORY !== 'undefined' ? Object.keys(CATEGORY) : []; return c; }"
        )
        assert len(cat_keys) > 0, "CATEGORY object is missing or empty"

        browser.close()