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

        # The global "convert all" selector only appears when every pending
        # file shares the SAME default target. Here jpg defaults to ICO and
        # png defaults to BMP (first non-self target in the registry-derived
        # STATIC_TARGET_MAP), so the defaults diverge -> selector is hidden
        # and offers NO common batch target.
        global_sel = page.locator("#globalFmt")
        assert global_sel.count() == 1, "Expected a global format selector"
        # collect non-empty option values
        options = global_sel.evaluate("el => Array.from(el.options).map(o => o.value).filter(v=>!!v)")
        assert options == [], (
            f"Global selector should offer no options when per-file default "
            f"targets diverge (jpg->ICO, png->BMP), found: {options}"
        )

        # Per-row dropdowns must reflect the FIX 1 registry exactly:
        # - jpg row: NO BMP (no registered jpg->bmp converter)
        # - png row: includes PDF (registered via images_to_pdf plugin)
        rows = page.locator("#rows .row")
        row_opts = {}
        for i in range(rows.count()):
            name = rows.nth(i).locator(".row-name").inner_text()
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else name.lower()
            row_opts[ext] = rows.nth(i).locator("select.fmt").evaluate(
                "el => Array.from(el.options).map(o => o.value)"
            )
        assert "jpg" in row_opts and "png" in row_opts, (
            f"Expected jpg and png rows, got: {list(row_opts)}"
        )
        assert row_opts["jpg"] == ["ICO", "PDF", "PNG", "TIFF", "WEBP"], (
            f"jpg row dropdown must match registry (no BMP), got: {row_opts['jpg']}"
        )
        assert "PDF" in row_opts["png"], (
            f"png row dropdown should include PDF (images_to_pdf), got: {row_opts['png']}"
        )

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
        # PNG + M4A should have no overlapping global targets according to phase_a_matrix.json
        BASE_DIR = Path(__file__).resolve().parent
        png = (BASE_DIR / "assets" / "real-test.png").resolve()
        m4a = (BASE_DIR / "assets" / "regression" / "generated_tone.m4a").resolve()

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
