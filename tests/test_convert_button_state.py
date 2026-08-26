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


def test_convert_button_becomes_visible_after_format_selection():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        file_path = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        page.locator("#fileInput").set_input_files(str(file_path))
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        first_row = page.locator("#rows .row").first
        fmt = first_row.locator("select.fmt")
        assert fmt.count() == 1, "Expected a format selector (`select.fmt`) inside `.row`"

        selected_value = fmt.evaluate("el => el.value || ''")
        if not selected_value:
            options = fmt.evaluate("el => Array.from(el.options).map(o => o.value).filter(v => !!v)")
            if options:
                fmt.select_option(options[0])

        go_btn = page.locator("#goBtn")
        assert go_btn.count() > 0, "PanelZone go button should exist"
        assert go_btn.is_visible(), "Go button should become visible after format selection"
        assert not go_btn.is_disabled(), "Go button should be enabled after format selection"

        browser.close()


def test_jpg_row_hides_broken_docx_target_from_matrix():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        file_path = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        page.locator("#fileInput").set_input_files(str(file_path))
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        row_select = page.locator("#rows .row select.fmt").first
        options = row_select.evaluate("el => Array.from(el.options).map(o => o.value)")
        assert "DOCX" not in options, "Matrix-approved JPG targets must exclude DOCX; it is classified as BROKEN ENGINE"
        assert "PNG" in options, "Matrix-approved JPG targets should still include PNG"

        browser.close()
