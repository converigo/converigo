from playwright.sync_api import sync_playwright
import os, time, json
from PIL import Image, ImageChops

BASE = os.environ.get('CONVERIGO_BASE_URL','http://127.0.0.1:8000')
OUT = {}
os.makedirs('ui_screenshots', exist_ok=True)

sample = 'sample_image.png'
# create extra copies if needed
for i in range(1,4):
    dst = f'tmp_test_image_{i}.png'
    if not os.path.exists(dst):
        try:
            Image.open(sample).save(dst)
        except Exception:
            open(dst,'wb').write(open(sample,'rb').read())

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width':1366,'height':768})
    page = context.new_page()
    console_logs = []
    network_errors = []

    page.on('console', lambda msg: console_logs.append({'type': msg.type, 'text': msg.text}))
    def on_response(resp):
        try:
            status = resp.status
            if status >= 400:
                network_errors.append({'url': resp.url, 'status': status})
        except Exception:
            pass
    page.on('response', on_response)

    # Home page screenshot for regression (Test 3)
    page.goto(BASE, wait_until='networkidle')
    time.sleep(0.5)
    homepage_path = 'ui_screenshots/homepage_current.png'
    page.screenshot(path=homepage_path, full_page=True)

    # Visual diff Test 3
    baseline = 'validation_desktop_homepage.png'
    test3_pass = False
    if os.path.exists(baseline):
        d = Image.open(baseline).convert('RGB')
        c = Image.open(homepage_path).convert('RGB')
        if d.size != c.size:
            c = c.resize(d.size, Image.LANCZOS)
        diff = ImageChops.difference(d, c)
        diff.save('ui_screenshots/homepage_diff.png')
        total_pixels = d.size[0]*d.size[1]
        diff_pixels = sum(1 for px in diff.getdata() if px != (0,0,0))
        diff_pct = diff_pixels/total_pixels*100
        test3_pass = diff_pct < 1.0
        OUT['test3_diff_pct'] = diff_pct
    else:
        OUT['test3_error'] = 'Baseline missing: validation_desktop_homepage.png'

    # TEST 2: Feature Flag ON (V2 should be visible, legacy hidden)
    # ensure starting state
    page.reload(wait_until='networkidle')
    time.sleep(0.5)
    flags = page.evaluate('() => ({flag: window.__ENABLE_DOWNLOAD_V2__, ConverigoFlags: window.ConverigoFlags})')
    OUT['flags'] = flags

    # perform single-file conversion
    try:
        page.set_input_files('input[type=file]', sample)
    except Exception as e:
        OUT['test2_upload_error'] = str(e)
    # click convert
    btn = page.query_selector('#convertButton') or page.query_selector('#btnConvert') or page.query_selector('button.convert-button')
    if btn:
        btn.click()
    # wait for download-ready or v2 stage visible
    v2_visible = False
    legacy_visible = False
    preparing_seen = False
    download_seen = False
    start = time.time()
    while time.time() - start < 20:
        v2 = page.query_selector('#downloadStage')
        v2_visible = page.evaluate('(el) => !!(el && !el.hidden && el.offsetWidth>0 && el.offsetHeight>0)', v2) if v2 else False
        legacy = page.query_selector('#downloadBtn')
        legacy_visible = page.evaluate('(el) => !!(el && !el.hidden && el.offsetWidth>0 && el.offsetHeight>0)', legacy) if legacy else False
        # check text states
        btn_main = page.query_selector('#btnDownloadMain')
        if btn_main:
            try:
                txt = page.evaluate('(el) => el.textContent || ""', btn_main) or ''
                txt = txt.strip()
                if 'Preparing' in txt or 'Preparing…' in txt:
                    preparing_seen = True
                if 'Download' in txt and preparing_seen:
                    download_seen = True
            except Exception:
                pass
        if v2_visible or legacy_visible:
            time.sleep(0.5)
        else:
            time.sleep(0.5)
    # capture screenshot
    page.screenshot(path='ui_screenshots/test2_flow.png', full_page=True)
    OUT['test2_v2_visible'] = v2_visible
    OUT['test2_legacy_visible'] = legacy_visible
    OUT['test2_preparing_seen'] = preparing_seen
    OUT['test2_download_seen'] = download_seen

    # TEST 4: Multiple file conversion (3 files)
    page.goto(BASE, wait_until='networkidle')
    time.sleep(0.3)
    try:
        page.set_input_files('input[type=file]', [ 'tmp_test_image_1.png', 'tmp_test_image_2.png', 'tmp_test_image_3.png' ])
    except Exception as e:
        OUT['test4_upload_error'] = str(e)
    # click convert
    btn = page.query_selector('#convertButton') or page.query_selector('#btnConvert')
    if btn:
        btn.click()
    # wait and count download items
    start = time.time()
    download_count = 0
    while time.time() - start < 30:
        items = page.query_selector_all('.download-item')
        download_count = len(items)
        if download_count >= 3:
            break
        time.sleep(0.8)
    OUT['test4_download_count'] = download_count
    # check for duplicates/hrefs
    hrefs = []
    for it in page.query_selector_all('.download-item a'):
        h = page.evaluate('(el) => el.getAttribute("href")', it)
        hrefs.append(h)
    OUT['test4_hrefs'] = hrefs
    page.screenshot(path='ui_screenshots/test4_flow.png', full_page=True)

    # TEST 5 & 6: Console and Network
    # gather console_logs and network_errors
    OUT['console'] = [c for c in console_logs if c['type'] in ('error','warning')]
    OUT['network_errors'] = network_errors

    browser.close()

# Evaluate PASS/FAIL
results = {}
results['TEST 2'] = (OUT.get('test2_v2_visible') and not OUT.get('test2_legacy_visible') and OUT.get('test2_preparing_seen') and OUT.get('test2_download_seen'))
results['TEST 3'] = ('test3_diff_pct' in OUT and OUT['test3_diff_pct'] < 1.0)
results['TEST 4'] = (OUT.get('test4_download_count',0) >= 3 and len(set(OUT.get('test4_hrefs',[])))==len(OUT.get('test4_hrefs',[])) and all(OUT.get('test4_hrefs',[])))
results['TEST 5'] = (len(OUT.get('console',[]))==0)
results['TEST 6'] = (len(OUT.get('network_errors',[]))==0)

report = {'out': OUT, 'results': results}
print(json.dumps(report))
