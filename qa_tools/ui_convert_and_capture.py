from playwright.sync_api import sync_playwright
import time
import os

BASE = os.environ.get('CONVERIGO_BASE_URL', 'http://127.0.0.1:8000')

screenshot_dir = 'ui_screenshots'
os.makedirs(screenshot_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':390,'height':844})
    page.goto(f"{BASE}/", wait_until='networkidle')
    time.sleep(1)
    # Upload file
    page.set_input_files('input[type=file]', 'sample_image.png')
    time.sleep(1)
    page.screenshot(path=os.path.join(screenshot_dir, 'upload.png'), full_page=True)
    # Select JPG if necessary (select element)
    # Click convert button (site uses #convertButton)
    convert_btn = page.query_selector('#convertButton') or page.query_selector('#btnConvert') or page.query_selector('.convert-button')
    if convert_btn:
        convert_btn.click()
    else:
        # try clicking the actionBar button
        btn = page.query_selector('#btnConvert')
        if btn:
            btn.click()
    # Wait for download-ready event, poll for download stage visible
    for state, filename in [('preparing', 'preparing.png'), ('ready', 'download_ready.png')]:
        # wait up to 10s
        for _ in range(30):
            if page.query_selector('#downloadStage.is-visible') or page.query_selector('#downloadScreenBlueprint.is-visible'):
                break
            time.sleep(0.2)
        page.screenshot(path=os.path.join(screenshot_dir, filename), full_page=True)
    # Trigger download
    btn_dl = page.query_selector('#btnDownloadMain, #downloadBtn, .download-screen__button--primary')
    if btn_dl:
        try:
            btn_dl.click()
        except Exception:
            pass
    time.sleep(1)
    page.screenshot(path=os.path.join(screenshot_dir, 'downloaded.png'), full_page=True)
    browser.close()
    print('screenshots saved to', screenshot_dir)
