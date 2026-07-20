import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = os.environ.get("CONVERIGO_BASE_URL", "http://127.0.0.1:8000")
TIMEOUT = 180000

ASSETS = {
    "jpg": Path("tests/assets/real-test.jpg").resolve(),
    "png": Path("tests/assets/real-test.png").resolve(),
    "pdf": Path("tests/assets/real-test.pdf").resolve(),
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

    page.goto(BASE_URL, wait_until="networkidle")

    page.wait_for_selector("#fileInput", state="attached", timeout=TIMEOUT)
    page.locator("#fileInput").set_input_files([str(path) for path in file_paths])

    page.wait_for_selector(".format-chip", timeout=TIMEOUT)
    first_chip = page.locator(".format-chip").first

    assert first_chip.is_visible(), "Recommendation format chip should be visible"
    assert "active" in (first_chip.get_attribute("class") or ""), "Recommended format should be auto-selected"

    convert_button = page.locator("#convertButton")
    assert convert_button.is_visible(), "Convert button should be visible after recommendation"
    assert not convert_button.is_disabled(), "Convert button should be enabled after recommendation"

    convert_button.click()

    page.wait_for_timeout(10000)

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
