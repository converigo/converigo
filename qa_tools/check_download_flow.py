from playwright.sync_api import sync_playwright
import os, time, json
BASE = os.environ.get('CONVERIGO_BASE_URL','http://127.0.0.1:8000')

result = {"base_url": BASE}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width':1280,'height':800})
    page.goto(BASE, wait_until='networkidle')
    time.sleep(0.5)
    # capture flags
    flags = page.evaluate("() => ({flag: window.__ENABLE_DOWNLOAD_V2__, ConverigoFlags: window.ConverigoFlags})")
    result['flags'] = flags
    # perform upload
    try:
        page.set_input_files('input[type=file]', 'sample_image.png')
    except Exception as e:
        result['upload_error'] = str(e)
    time.sleep(0.5)
    # click convert button if present
    convert = page.query_selector('#convertButton') or page.query_selector('#btnConvert') or page.query_selector('button.convert-button')
    if convert:
        try:
            convert.click()
        except Exception:
            pass
    # wait for processing
    time.sleep(2)
    # check for download manager legacy button
    legacy = page.query_selector('#downloadBtn')
    v2_blueprint = page.query_selector('#downloadScreenBlueprint')
    v2_stage = page.query_selector('#downloadStage')
    result['legacy_present'] = bool(legacy)
    # check visibility
    def is_visible(el):
        if not el: return False
        return page.evaluate('(el) => { const r = el.getBoundingClientRect(); return !(el.hidden || r.width===0 && r.height===0) }', el)
    result['legacy_visible'] = is_visible(legacy) if legacy else False
    result['v2_blueprint_present'] = bool(v2_blueprint)
    result['v2_blueprint_visible'] = is_visible(v2_blueprint) if v2_blueprint else False
    result['v2_stage_present'] = bool(v2_stage)
    result['v2_stage_visible'] = is_visible(v2_stage) if v2_stage else False
    # take screenshot
    path = 'ui_screenshots/check_flow.png'
    os.makedirs('ui_screenshots', exist_ok=True)
    page.screenshot(path=path, full_page=True)
    result['screenshot'] = path
    browser.close()

print(json.dumps(result))
