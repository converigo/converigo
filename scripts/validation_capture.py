from pathlib import Path
from playwright.sync_api import sync_playwright
import json

ROOT = Path.cwd()
SCREENSHOT_DIR = ROOT / 'validation_assets'
SCREENSHOT_DIR.mkdir(exist_ok=True)
TMP_DIR = ROOT / 'tmp_validation_files'
TMP_DIR.mkdir(exist_ok=True)

# Create 120 unique dummy files for upload validation
for count in [25, 100]:
    for i in range(1, count + 1):
        file_path = TMP_DIR / f'val_{count:03d}_{i:03d}.jpg'
        if not file_path.exists():
            file_path.write_bytes(b'JPEGDATA' + bytes(str(i), 'utf-8'))

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    results = []
    page = browser.new_page(viewport={'width': 1366, 'height': 900})
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    page.wait_for_timeout(1000)
    page.screenshot(path=str(SCREENSHOT_DIR / 'desktop_initial.png'), full_page=True)
    results.append({'page':'desktop_initial','width':1366,'height':900})

    page.locator('#fileInput').set_input_files(str(ROOT / 'tests' / 'assets' / 'real-test.jpg'))
    page.wait_for_timeout(1200)
    page.screenshot(path=str(SCREENSHOT_DIR / 'desktop_after_upload_single.png'), full_page=True)
    results.append({'page':'desktop_after_upload_single','files':1})

    state = page.evaluate('''() => {
        const footer = document.getElementById('fileListFooter');
        const fileList = document.getElementById('fileList');
        const convertBtn = document.getElementById('convertButton');
        const removeBtns = Array.from(document.querySelectorAll('.file-remove-btn'));
        const selects = Array.from(document.querySelectorAll('.file-output-select'));
        return {
            footerVisible: footer ? !footer.hidden : false,
            fileListVisible: fileList ? !fileList.hidden : false,
            convertVisible: convertBtn ? convertBtn.offsetParent !== null : false,
            convertDisabled: convertBtn ? convertBtn.disabled : null,
            removeCount: removeBtns.length,
            selectCount: selects.length,
            fileListOverflowX: fileList ? fileList.scrollWidth > fileList.clientWidth : null,
            pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            footerRect: footer ? footer.getBoundingClientRect().toJSON() : null
        };
    }''')
    results[-1]['state'] = state

    # Verify global output and individual output selectors exist
    outputState = page.evaluate('''() => {
        const global = document.getElementById('globalOutputSelect');
        const firstSelect = document.querySelector('.file-output-select');
        const removeBtn = document.querySelector('.file-remove-btn');
        return {
            globalExists: !!global,
            globalAria: global ? global.getAttribute('aria-label') : null,
            firstSelectExists: !!firstSelect,
            removeBtnAria: removeBtn ? removeBtn.getAttribute('aria-label') : null,
            touchTargets: {
                convert: document.getElementById('convertButton')?.getBoundingClientRect().height || 0,
                remove: removeBtn?.getBoundingClientRect().height || 0,
                global: global?.getBoundingClientRect().height || 0
            }
        };
    }''')
    results[-1]['controls'] = outputState

    # Capture desktop 25-file state
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    page.wait_for_timeout(1000)
    files25 = [str(TMP_DIR / f'val_025_{i:03d}.jpg') for i in range(1, 26)]
    page.locator('#fileInput').set_input_files(files25)
    page.wait_for_timeout(1500)
    page.screenshot(path=str(SCREENSHOT_DIR / 'desktop_25_files.png'), full_page=True)
    results.append({'page':'desktop_25_files','count':25})
    results[-1]['state'] = page.evaluate('''() => {
        const footer = document.getElementById('fileListFooter');
        const fileList = document.getElementById('fileList');
        return {
            fileCount: document.querySelectorAll('.file-item').length,
            footerVisible: footer ? !footer.hidden : false,
            footerBottom: footer ? footer.getBoundingClientRect().bottom : null,
            listScroll: fileList ? fileList.scrollHeight > fileList.clientHeight : null,
            pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth
        };
    }''')

    # Capture desktop 100-file state
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    page.wait_for_timeout(1000)
    files100 = [str(TMP_DIR / f'val_100_{i:03d}.jpg') for i in range(1, 101)]
    page.locator('#fileInput').set_input_files(files100)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(SCREENSHOT_DIR / 'desktop_100_files.png'), full_page=True)
    results.append({'page':'desktop_100_files','count':100})
    results[-1]['state'] = page.evaluate('''() => {
        const footer = document.getElementById('fileListFooter');
        const fileList = document.getElementById('fileList');
        return {
            fileCount: document.querySelectorAll('.file-item').length,
            footerVisible: footer ? !footer.hidden : false,
            listScroll: fileList ? fileList.scrollHeight > fileList.clientHeight : null,
            pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth
        };
    }''')

    for name, viewport in [('tablet', {'width': 768, 'height': 1024}), ('mobile_390', {'width': 390, 'height': 844}), ('mobile_412', {'width': 412, 'height': 844}), ('mobile_430', {'width': 430, 'height': 844})]:
        page.set_viewport_size(viewport)
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.locator('#fileInput').set_input_files(str(ROOT / 'tests' / 'assets' / 'real-test.jpg'))
        page.wait_for_timeout(1200)
        page.screenshot(path=str(SCREENSHOT_DIR / f'{name}_single.png'), full_page=True)
        info = page.evaluate('''() => {
            const footer = document.getElementById('fileListFooter');
            const fileList = document.getElementById('fileList');
            return {
                footerVisible: footer ? !footer.hidden : false,
                pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                footerBottom: footer ? footer.getBoundingClientRect().bottom : null,
                viewHeight: window.innerHeight,
                listScroll: fileList ? fileList.scrollHeight > fileList.clientHeight : null
            };
        }''')
        results.append({'page': name, 'viewport': viewport, 'state': info})

    # Keyboard navigation focus test
    page.set_viewport_size({'width': 1366, 'height': 900})
    page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
    page.wait_for_timeout(1000)
    page.locator('#chooseFile').focus()
    page.keyboard.press('Tab')
    page.keyboard.press('Tab')
    focus = page.evaluate('''() => {
        const active = document.activeElement;
        return {
            activeId: active ? active.id : null,
            activeTag: active ? active.tagName : null,
            outline: window.getComputedStyle(active).outlineStyle
        };
    }''')
    results.append({'keyboard_focus': focus})

    browser.close()

out_file = ROOT / 'validation_assets' / 'validation_capture_results.json'
out_file.write_text(json.dumps(results, indent=2))
print('Wrote captures and results to', out_file)
