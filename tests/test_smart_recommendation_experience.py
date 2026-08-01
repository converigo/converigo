import os
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")


def get_base_url() -> str:
    return os.environ.get("CONVERIGO_BASE_URL", "http://127.0.0.1:8000")


def test_recommendation_panel_supports_search_and_persistence():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        file_path = Path("tests/assets/real-test.jpg").resolve()
        page.locator("#fileInput").set_input_files(str(file_path))

        page.wait_for_selector("#formatSearch", timeout=20000)
        page.wait_for_selector(".recommendation-card", timeout=20000)

        page.locator("#formatSearch").fill("png")
        visible_cards = page.locator(".recommendation-card").filter(has_not=page.locator("[hidden]"))
        assert visible_cards.count() > 0, "Search should surface matching recommendations"

        first_visible = visible_cards.first
        target = first_visible.get_attribute("data-target") or ""
        assert target, "Recommended cards should expose a target format"

        page.evaluate("""
        () => {
            const firstTarget = document.querySelector('.recommendation-card[data-target]')?.getAttribute('data-target') || '';
            const card = document.querySelector('.recommendation-card[data-target=\"' + firstTarget + '\"]');
            if (card) {
                card.querySelector('.recommendation-card-favorite')?.click();
            }
        }
        """)
        favorites_value = page.evaluate("() => window.localStorage.getItem('converigo_favorites')")
        assert target in favorites_value, "Favorite actions should persist to localStorage"

        page.evaluate("""
        () => {
            const firstTarget = document.querySelector('.recommendation-card[data-target]')?.getAttribute('data-target') || '';
            const card = document.querySelector('.recommendation-card[data-target=\"' + firstTarget + '\"]');
            if (card) {
                card.click();
            }
        }
        """)
        recent_value = page.evaluate("() => window.localStorage.getItem('converigo_recent_formats')")
        assert target in recent_value, "Selecting a recommendation should update recent history"

        browser.close()
