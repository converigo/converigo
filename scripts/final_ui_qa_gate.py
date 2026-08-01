from pathlib import Path
import json
import subprocess
import sys
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()
SCREENSHOT_DIR = ROOT / "validation_assets"
SCREENSHOT_DIR.mkdir(exist_ok=True)
TMP_DIR = ROOT / "tmp_validation_files"
TMP_DIR.mkdir(exist_ok=True)

URL = "http://127.0.0.1:8000/"

DUMMY_FILE = TMP_DIR / "qa_dummy_upload.jpg"
if not DUMMY_FILE.exists():
    DUMMY_FILE.write_bytes(b"JPEGDATA-QA")

RESULTS_PATH = SCREENSHOT_DIR / "final_qa_results.json"


def capture_empty_state(page, name, viewport):
    page.set_viewport_size(viewport)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1200)
    screenshot_path = SCREENSHOT_DIR / f"empty_{name}.png"
    page.screenshot(path=str(screenshot_path), full_page=True)
    state = page.evaluate("""() => {
        const footer = document.getElementById('fileListFooter');
        const fileList = document.getElementById('fileList');
        const body = document.body;
        return {
            footerVisible: !!footer,
            fileListExists: !!fileList,
            pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
            pageOverflowY: document.documentElement.scrollHeight > document.documentElement.clientHeight,
            bodyOverflowX: body.scrollWidth > body.clientWidth,
            footerBottom: footer ? footer.getBoundingClientRect().bottom : null,
            viewportWidth: window.innerWidth,
            viewportHeight: window.innerHeight
        };
    }""")
    return {"screenshot": str(screenshot_path), "state": state}


def capture_cross_browser(p):
    results = []
    configs = [
        ("chrome", p.chromium, {"channel": "chrome"}),
        ("edge", p.chromium, {"channel": "msedge"}),
        ("firefox", p.firefox, {}),
    ]
    for name, engine, opts in configs:
        entry = {"browser": name, "available": False}
        try:
            browser = engine.launch(headless=True, **opts)
            entry["available"] = True
            page = browser.new_page(viewport={"width": 1366, "height": 900})
            page.goto(URL, wait_until="networkidle")
            page.wait_for_timeout(1000)
            screenshot = SCREENSHOT_DIR / f"cross_{name}_desktop_initial.png"
            page.screenshot(path=str(screenshot), full_page=True)
            entry["screenshotInitial"] = str(screenshot)
            entry["state"] = page.evaluate("""() => {
                const btn = document.getElementById('convertButton');
                const fileInput = document.getElementById('fileInput');
                const global = document.getElementById('globalOutputSelect');
                const footer = document.getElementById('fileListFooter');
                return {
                    convertVisible: !!btn,
                    convertDisabled: btn ? btn.disabled : null,
                    fileInputExists: !!fileInput,
                    globalExists: !!global,
                    footerVisible: !!footer,
                    pageOverflowX: document.documentElement.scrollWidth > document.documentElement.clientWidth,
                };
            }""")
            if page.query_selector('#fileInput'):
                try:
                    page.locator('#fileInput').set_input_files(str(DUMMY_FILE))
                    page.wait_for_timeout(1200)
                    upload_screenshot = SCREENSHOT_DIR / f"cross_{name}_desktop_uploaded.png"
                    page.screenshot(path=str(upload_screenshot), full_page=True)
                    entry["screenshotUploaded"] = str(upload_screenshot)
                except Exception as e:
                    entry["uploadError"] = str(e)
            browser.close()
        except Exception as e:
            entry["error"] = str(e)
        results.append(entry)
    return results


def find_convert_button(page):
    button = page.locator('#conversionStickyBar #convertButton').first
    if button.count() > 0:
        return button
    button = page.locator('#fileListFooter #convertButton').first
    if button.count() > 0:
        return button
    return page.locator('button#convertButton').first


def validate_keyboard_nav(page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1000)
    page.locator('body').click()
    focus_sequence = []
    for _ in range(8):
        page.keyboard.press('Tab')
        page.wait_for_timeout(150)
        focus_info = page.evaluate("""() => {
            const active = document.activeElement;
            if (!active) return null;
            const style = window.getComputedStyle(active);
            return {
                id: active.id || null,
                tag: active.tagName || null,
                ariaLabel: active.getAttribute('aria-label') || null,
                role: active.getAttribute('role') || null,
                outlineStyle: style.outlineStyle,
                outlineWidth: style.outlineWidth,
                boxShadow: style.boxShadow,
                height: Math.round(active.getBoundingClientRect().height),
                width: Math.round(active.getBoundingClientRect().width),
                accessibleName: active.getAttribute('aria-label') || active.textContent?.trim() || null,
            };
        }""")
        if focus_info:
            focus_sequence.append(focus_info)
    return focus_sequence


def validate_accessibility(page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1000)
    result = page.evaluate("""() => {
        const global = document.getElementById('globalOutputSelect');
        const convert = document.getElementById('convertButton');
        const remove = document.querySelector('.file-remove-btn');
        const choose = document.getElementById('chooseFile');
        const fieldset = document.querySelector('#fileList');
        return {
            globalAria: global ? global.getAttribute('aria-label') : null,
            globalRole: global ? global.getAttribute('role') : null,
            convertAria: convert ? convert.getAttribute('aria-label') : null,
            convertText: convert ? convert.textContent.trim() : null,
            chooseAria: choose ? choose.getAttribute('aria-label') : null,
            fileListRole: fieldset ? fieldset.getAttribute('role') : null,
            fileListExists: !!fieldset,
            removeButtonCount: document.querySelectorAll('.file-remove-btn').length,
        };
    }""")
    return result


def validate_animation(page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1000)
    result = page.evaluate("""() => {
        const row = document.querySelector('.file-item');
        const conversion = document.getElementById('conversionArea');
        const btn = document.getElementById('convertButton');
        const fileInput = document.getElementById('fileInput');
        return {
            fileRowTransition: row ? window.getComputedStyle(row).transitionDuration || null : null,
            fileRowAnimation: row ? window.getComputedStyle(row).animationDuration || null : null,
            conversionAnimation: conversion ? window.getComputedStyle(conversion).animationDuration || null : null,
            conversionTransition: conversion ? window.getComputedStyle(conversion).transitionDuration || null : null,
            convertButtonTouchHeight: btn ? Math.round(btn.getBoundingClientRect().height) : null,
            fileInputPresent: !!fileInput,
        };
    }""")
    return result


def validate_reduced_motion(p):
    entry = {"reduced_motion": {}}
    try:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(reduced_motion='reduce', viewport={"width": 1366, "height": 900})
        page = context.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        entry["reduced_motion"] = page.evaluate("""() => {
            const row = document.querySelector('.file-item');
            const conversion = document.getElementById('conversionArea');
            const btn = document.querySelector('#conversionStickyBar #convertButton') || document.getElementById('convertButton');
            return {
                prefersReducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
                rowAnimation: row ? window.getComputedStyle(row).animationDuration : null,
                rowTransition: row ? window.getComputedStyle(row).transitionDuration : null,
                conversionAnimation: conversion ? window.getComputedStyle(conversion).animationDuration : null,
                conversionTransition: conversion ? window.getComputedStyle(conversion).transitionDuration : null,
                convertButtonTransition: btn ? window.getComputedStyle(btn).transitionDuration : null,
            };
        }""")
        context.close()
        browser.close()
    except Exception as e:
        entry["reduced_motion_error"] = str(e)
    return entry


def validate_regression(page):
    data = {}
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(1000)
    file_input = page.locator('#fileInput')
    if file_input.count() == 0:
        data["uploadError"] = "#fileInput not found"
        return data
    try:
        file_input.set_input_files(str(DUMMY_FILE))
        page.wait_for_timeout(1200)
        data["uploadFilePresent"] = page.locator('.file-item').count() > 0
        data["formatChipCount"] = page.locator('.format-chip').count()
        data["stickyConvertButtonCount"] = page.locator('#conversionStickyBar #convertButton').count()
        data["footerConvertButtonCount"] = page.locator('#fileListFooter #convertButton').count()
        convert_button = find_convert_button(page)
        data["convertButtonEnabled"] = convert_button.count() > 0 and convert_button.is_enabled()
        if page.locator('.file-remove-btn').count() > 0:
            page.locator('.file-remove-btn').first.click()
            page.wait_for_timeout(800)
            data["removeFileWorked"] = page.locator('.file-item').count() == 0
    except Exception as e:
        data["uploadRemoveError"] = str(e)
    try:
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(1000)
        files = [str(DUMMY_FILE)] * 3
        page.locator('#fileInput').set_input_files(files)
        page.wait_for_timeout(1200)
        data["multiUploadCount"] = page.locator('.file-item').count()
    except Exception as e:
        data["multiUploadError"] = str(e)
    try:
        if page.locator('.file-item').count() > 0:
            if page.locator('.format-chip').count() > 0:
                page.locator('.format-chip').first.click()
                page.wait_for_timeout(300)
            convert_btn = find_convert_button(page)
            if convert_btn.count() > 0:
                convert_btn.click()
                download_btn = page.locator('#downloadBtn')
                download_btn.wait_for(state='visible', timeout=30000)
                data["downloadButtonVisible"] = download_btn.is_visible()
                data["downloadHref"] = download_btn.get_attribute('href')
            else:
                data["convertButtonNotFound"] = True
        else:
            data["convertSkipped"] = "no file rows"
    except Exception as e:
        data["convertError"] = str(e)
    return data


if __name__ == '__main__':
    results = {}
    with sync_playwright() as p:
        results["cross_browser"] = capture_cross_browser(p)
        results["empty_states"] = {}
        for name, viewport in [("desktop", {"width": 1366, "height": 900}), ("tablet", {"width": 768, "height": 1024}), ("mobile", {"width": 390, "height": 844})]:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport=viewport)
            results["empty_states"][name] = capture_empty_state(page, name, viewport)
            browser.close()
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        results["keyboard_navigation"] = validate_keyboard_nav(page)
        results["accessibility"] = validate_accessibility(page)
        results["animation"] = validate_animation(page)
        browser.close()
        results["reduced_motion"] = validate_reduced_motion(p)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1366, "height": 900})
        results["regression"] = validate_regression(page)
        browser.close()
    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    print(f"Final QA results written to {RESULTS_PATH}")
