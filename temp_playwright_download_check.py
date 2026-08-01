from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError
import json

base_url = 'http://127.0.0.1:8003/tools/png-to-jpg'
file_path = Path('tests/assets/real-test.jpg').resolve()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    try:
        page.goto(base_url, wait_until='domcontentloaded', timeout=60000)
        page.locator('#fileInput').set_input_files(str(file_path))
        page.wait_for_selector('.format-chip', timeout=30000, state='attached')
        page.locator('.format-chip').first.click()
        page.wait_for_selector('#convertButton:not([hidden])', timeout=15000, state='attached')
        page.locator('#convertButton').click()

        info = {
            'downloadBtnExists': page.locator('#downloadBtn').count() > 0,
            'downloadBtnVisible': False,
            'downloadBtnHidden': None,
            'downloadHref': None,
            'downloadAttr': None,
            'resultCardVisible': page.locator('#resultCard').is_visible() if page.locator('#resultCard').count() else False,
            'errorCardVisible': page.locator('#errorCard').is_visible() if page.locator('#errorCard').count() else False,
            'resultText': page.locator('#resultCard').inner_text().strip()[:400] if page.locator('#resultCard').count() else None,
            'errorText': page.locator('#errorCard').inner_text().strip()[:400] if page.locator('#errorCard').count() else None,
        }

        try:
            page.wait_for_selector('#downloadBtn:not([hidden])', timeout=90000)
            download_btn = page.locator('#downloadBtn')
            info.update({
                'downloadBtnVisible': download_btn.is_visible(),
                'downloadBtnHidden': page.evaluate('e => e.hidden', download_btn),
                'downloadHref': download_btn.get_attribute('href'),
                'downloadAttr': download_btn.get_attribute('download'),
            })
        except TimeoutError:
            pass

        print(json.dumps(info, indent=2))
    finally:
        browser.close()
