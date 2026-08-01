import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('CONVERIGO_BASE_URL', 'http://127.0.0.1:8000')

def main():
    path = Path('tests/assets/real-test.jpg').resolve()
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE)
        page.locator('#fileInput').set_input_files(str(path))
        page.wait_for_selector('.recommendation-card', timeout=15000)
        card = page.locator('.recommendation-card').first
        print('cards', page.locator('.recommendation-card').count())
        print('first card html', card.evaluate('(el) => el.outerHTML'))
        browser.close()

if __name__ == '__main__':
    main()
