from playwright.sync_api import sync_playwright
import time, json, os
BASE = os.environ.get('CONVERIGO_BASE_URL','http://127.0.0.1:8000')
res = {'base': BASE}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1366,'height':768})
    page.goto(BASE, wait_until='networkidle')
    time.sleep(0.3)
    res['flags'] = page.evaluate('() => ({flag: window.__ENABLE_DOWNLOAD_V2__, ConverigoFlags: window.ConverigoFlags})')
    try:
        page.set_input_files('input[type=file]', 'sample_image.png')
    except Exception as e:
        res['upload_error'] = str(e)
    btn = page.query_selector('#convertButton') or page.query_selector('#btnConvert')
    if btn:
        btn.click()
    seq = []
    start = time.time()
    seen_preparing = False
    seen_ready = False
    primary_enabled_when_ready = False
    while time.time() - start < 10:
        # check step items
        preparing = page.query_selector('[data-step="preparing"].is-active')
        ready = page.query_selector('[data-step="ready"].is-active')
        converting = page.query_selector('[data-step="converting"].is-active')
        if converting and 'converting' not in seq:
            seq.append('converting')
        if preparing and 'preparing' not in seq:
            seq.append('preparing'); seen_preparing = True
        if ready and 'ready' not in seq:
            seq.append('ready'); seen_ready = True
            # check primary button enabled
            pb = page.query_selector('#btnDownloadMain')
            if pb:
                enabled = page.evaluate('(el) => !el.disabled', pb)
                primary_enabled_when_ready = bool(enabled)
            break
        time.sleep(0.25)
    # legacy visibility
    legacy = page.query_selector('#downloadBtn')
    legacy_visible = False
    if legacy:
        legacy_visible = page.evaluate('(el) => !(el.hidden || (el.offsetWidth===0&&el.offsetHeight===0))', legacy)
    # take screenshot
    os.makedirs('ui_screenshots', exist_ok=True)
    page.screenshot(path='ui_screenshots/test2_transition.png', full_page=True)
    res['seq'] = seq
    res['seen_preparing'] = seen_preparing
    res['seen_ready'] = seen_ready
    res['primary_enabled_when_ready'] = primary_enabled_when_ready
    res['legacy_visible'] = legacy_visible
    browser.close()
print(json.dumps(res))
