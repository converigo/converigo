import os
from pathlib import Path
import json
import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")


def get_base_url() -> str:
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError("CONVERIGO_BASE_URL is not set; tests require the app server fixture or an explicit environment var.")
    return base_url


TIMEOUT = 180000


def test_ui_partial_failure_shows_per_row_status(tmp_path):
    # Create a small corrupted 'jpg' file to trigger a realistic conversion failure
    corrupt = tmp_path / "corrupt.jpg"
    corrupt.write_bytes(b"this_is_not_a_valid_image_content")

    valid = Path(__file__).resolve().parent / "assets" / "real-test.jpg"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        # Upload valid image and corrupted image
        page.locator("#fileInput").set_input_files([str(valid.resolve()), str(corrupt.resolve())])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        # Choose first available target for each row
        rows = page.locator("#rows .row")
        count = rows.count()
        assert count >= 2
        for i in range(count):
            opts = rows.nth(i).locator("select.fmt").evaluate("el=>Array.from(el.options).map(o=>o.value).filter(v=>!!v)")
            if opts:
                rows.nth(i).locator("select.fmt").select_option(opts[0])

        page.locator("#goBtn").click()

        # Wait for final state: either .dl-main for success or .status-pill for failure per row
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        # Gather statuses
        rows = page.locator("#rows .row")
        found_success = False
        found_failure = False
        for i in range(rows.count()):
            name = rows.nth(i).locator(".row-name").inner_text()
            # If this is the corrupt file, expect failure indicator
            if "corrupt.jpg" in name:
                # Look for status-pill with 'Gagal' or row-error content
                if rows.nth(i).locator(".status-pill").count() or rows.nth(i).locator(".row-error").count():
                    found_failure = True
            else:
                # Expect download button to be present for success
                if rows.nth(i).locator(".dl-main").count():
                    found_success = True

        assert found_success, "Expected at least one successful row with download button"
        assert found_failure, "Expected at least one failed row with visible failure indicator"

        browser.close()
