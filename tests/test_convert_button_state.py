import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")


def get_base_url() -> str:
    return os.environ.get("CONVERIGO_BASE_URL", "http://127.0.0.1:8000")


def test_convert_button_becomes_visible_after_format_selection():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        file_path = Path("tests/assets/real-test.jpg").resolve()
        page.locator("#fileInput").set_input_files(str(file_path))

        page.wait_for_selector(".format-chip", timeout=15000)
        page.locator(".format-chip").first.click()

        convert_button = page.locator("#convertButton")
        assert convert_button.is_visible(), "Convert button should become visible after format selection"
        assert not convert_button.is_disabled(), "Convert button should be enabled after format selection"

        browser.close()
