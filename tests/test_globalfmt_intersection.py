import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")


def get_base_url() -> str:
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError("CONVERIGO_BASE_URL is not set; tests require the app server fixture or an explicit environment var.")
    return base_url


TIMEOUT = 180000


def _expected_common(*exts: str) -> set[str]:
    """D5: the bulk control must offer exactly the intersection of what every
    pending row can really reach, derived from the same authoritative capability
    the page renders from.

    This file used to hardcode {"TIFF", "WEBP"} for JPG+PNG, copied from a frozen
    "Phase A matrix" snapshot that both UI maps had long outgrown - so the test
    was red while the product was right. Deriving it keeps the test honest and
    makes it impossible for the expectation and the picker to drift apart again.
    """
    from app.services.target_capability import conversion_capability

    view = conversion_capability()
    sets = [set(view.get(ext, [])) for ext in exts]
    return set.intersection(*sets) if sets else set()


def test_globalfmt_no_common_target_for_jpg_png():
    BASE_DIR = Path(__file__).resolve().parent
    jpg = (BASE_DIR / "assets" / "real-test.jpg").resolve()
    png = (BASE_DIR / "assets" / "real-test.png").resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        page.locator("#fileInput").set_input_files([str(jpg), str(png)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        global_sel = page.locator("#globalFmt")
        assert global_sel.count() == 1, "Expected a global format selector"
        read_options = "el => Array.from(el.options).map(o => o.value).filter(v=>!!v)"

        # The bulk control summarises a consensus. While the two rows disagree
        # (jpg auto-defaults to ICO, png to BMP) it is legitimately empty: D5
        # removed the hardcoded cross-category list that used to fill it with
        # values valid for neither row. The old frozen {"TIFF","WEBP"} expectation
        # could not express this, which is why it sat red while the product was
        # right - see tests/test_target_capability_authority.py for the
        # authoritative version of this guarantee.
        options_before = global_sel.evaluate(read_options)
        assert options_before == [], (
            f"bulk control must stay empty until the rows agree, found: {options_before}"
        )

        # Once both rows agree, the control re-seeds and its options must be
        # exactly the capability intersection: no dead option, no reachable
        # option missing.
        common = sorted(_expected_common("jpg", "png"))
        assert common, "jpg + png are expected to share converters"
        rows = page.locator("#rows .row select.fmt")
        assert rows.count() == 2, "expected one target select per uploaded row"
        for i in range(rows.count()):
            rows.nth(i).select_option(common[0])
        page.wait_for_timeout(400)

        options = global_sel.evaluate(read_options)
        assert set(options) == set(common), (
            f"Global selector options mismatch for JPG+PNG, found: {options}, want: {common}"
        )
        assert "WORD" not in options, "placeholder-backed option must never be offered"

        browser.close()


def test_globalfmt_intersection_for_two_jpg():
    BASE_DIR = Path(__file__).resolve().parent
    jpg = (BASE_DIR / "assets" / "real-test.jpg").resolve()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        # upload two jpg files (same file twice)
        page.locator("#fileInput").set_input_files([str(jpg), str(jpg)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        global_sel = page.locator("#globalFmt")
        assert global_sel.count() == 1, "Expected a global format selector"
        options = global_sel.evaluate("el => Array.from(el.options).map(o => o.value).filter(v=>!!v)")
        assert len(options) > 0, "Global selector should offer common targets for two JPGs"

        browser.close()


def test_globalfmt_no_common_target_for_png_m4a():
    """D5: this case was defined *inside* test_globalfmt_intersection_for_two_jpg,
    so pytest never collected it and its assertion had never once run. Hoisted to
    module level and re-anchored on the derived capability rather than the frozen
    phase_a_matrix.json comment that used to justify it."""
    BASE_DIR = Path(__file__).resolve().parent
    png = (BASE_DIR / "assets" / "real-test.png").resolve()
    m4a = (BASE_DIR / "assets" / "regression" / "generated_tone.m4a").resolve()

    assert _expected_common("png", "m4a") == set(), (
        "expectation is stale: the capability now offers a common target for these"
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        page.locator("#fileInput").set_input_files([str(png), str(m4a)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        global_sel = page.locator("#globalFmt")
        assert global_sel.count() == 1, "Expected a global format selector"
        options = global_sel.evaluate("el => Array.from(el.options).map(o => o.value).filter(v=>!!v)")
        assert options == [], f"Global selector should not offer common targets for PNG+M4A batch, found: {options}"

        browser.close()
