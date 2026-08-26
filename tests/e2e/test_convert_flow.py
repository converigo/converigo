import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")

TIMEOUT = 180000


def get_base_url() -> str:
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError("CONVERIGO_BASE_URL is not set; tests require the app server fixture or an explicit environment var.")
    return base_url

BASE_DIR = Path(__file__).resolve().parent
ASSETS = {
    "jpg": (BASE_DIR / ".." / "assets" / "real-test.jpg").resolve(),
    "png": (BASE_DIR / ".." / "assets" / "real-test.png").resolve(),
    "pdf": (BASE_DIR / ".." / "assets" / "real-test.pdf").resolve(),
}


def collect_js_errors(page, errors):
    page.on("pageerror", lambda exception: errors.append(f"PAGE_ERROR: {exception}"))
    page.on(
        "console",
        lambda msg: errors.append(f"CONSOLE_ERROR: {msg.text}")
        if msg.type == "error"
        else None,
    )


def run_conversion_flow(page, file_paths):
    errors = []
    collect_js_errors(page, errors)

    page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

    page.wait_for_selector("#fileInput", state="attached", timeout=TIMEOUT)
    page.locator("#fileInput").set_input_files([str(path) for path in file_paths])
    # Wait until PanelZone renders the uploaded file as a `.row`
    page.wait_for_selector("#rows .row", timeout=TIMEOUT)
    first_row = page.locator("#rows .row").first
    assert first_row.is_visible(), "Uploaded file row should be visible in PanelZone"

    # Verify a format selector exists for the row and read default value.
    fmt_select = first_row.locator("select.fmt")
    # Ensure format selector is present in the row
    assert fmt_select.count() == 1, "Expected a format selector (`select.fmt`) inside `.row`"

    # Optionally enforce a deterministic selection:
    # Read current selected value via locator.evaluate for Playwright compatibility
    selected_value = fmt_select.evaluate("el => el.value || ''")
    if not selected_value:
        # choose the first option value (skip if option value is empty)
        options = fmt_select.evaluate("el => Array.from(el.options).map(o => o.value).filter(v => !!v)")
        if options:
            fmt_select.select_option(options[0])

    # Use PanelZone convert trigger
    convert_button = page.locator("#goBtn")
    assert convert_button.is_visible(), "PanelZone go button (#goBtn) should be visible"
    # If a global-format selector is visible and currently has an empty placeholder value,
    # pick the first non-empty option automatically so the Go button becomes enabled.
    global_sel = page.locator("#globalFmt")
    if global_sel.count() == 1 and global_sel.is_visible():
        global_val = global_sel.evaluate("el => el.value || ''")
        if not global_val:
            options = global_sel.evaluate("el => Array.from(el.options).map(o => o.value).filter(v => !!v)")
            if options:
                global_sel.select_option(options[0])

    assert not convert_button.is_disabled(), "PanelZone go button should be enabled when files pending"

    # Click and wait for backend /convert response and assert download_path exists
    with page.expect_response(lambda r: "/convert" in r.url and r.status in (200, 201), timeout=TIMEOUT) as resp_info:
        convert_button.click()
    convert_response = resp_info.value
    try:
        body = convert_response.json()
    except Exception:
        body = None

    assert body, f"Convert response missing JSON body: {convert_response.text()}"

    download_paths = []
    if isinstance(body, dict):
        if "download_path" in body:
            download_paths.append(body["download_path"])
        if "results" in body and isinstance(body["results"], list):
            for r in body["results"]:
                if isinstance(r, dict) and r.get("download_path"):
                    download_paths.append(r.get("download_path"))

    assert download_paths, f"No download_path found in convert response JSON: {body}"

    # Wait for UI completion affordances: `.dl-main` should appear (download primary button)
    page.wait_for_selector(".dl-main", timeout=TIMEOUT)
    dl_main = page.locator(".dl-main").first
    assert dl_main.is_visible(), "Download button (.dl-main) should be visible after conversion"

    page.wait_for_timeout(1500)
    assert not errors, f"JavaScript errors were detected: {errors}"


def test_jpg_conversion_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_conversion_flow(page, [ASSETS["jpg"]])
        browser.close()


def test_png_conversion_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_conversion_flow(page, [ASSETS["png"]])
        browser.close()


def test_pdf_conversion_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_conversion_flow(page, [ASSETS["pdf"]])
        browser.close()


def test_multi_file_upload_flow():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        run_conversion_flow(page, [ASSETS["jpg"], ASSETS["png"]])
        browser.close()
