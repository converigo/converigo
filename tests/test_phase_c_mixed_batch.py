import os
from pathlib import Path
import json
import requests
import pytest
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.usefixtures("app_base_url")


def get_base_url() -> str:
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError("CONVERIGO_BASE_URL is not set; tests require the app server fixture or an explicit environment var.")
    return base_url


TIMEOUT = 180000
RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


def _take_screenshot(page, name):
    path = RESULTS_DIR / name
    page.screenshot(path=str(path), full_page=True)
    return str(path)


def test_single_file_single_target():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        file_path = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        page.locator("#fileInput").set_input_files(str(file_path))
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        # Ensure a target exists and convert
        first_row = page.locator("#rows .row").first
        fmt = first_row.locator("select.fmt")
        opt = fmt.evaluate("el => Array.from(el.options).map(o=>o.value).filter(v=>!!v)[0]")
        assert opt, "No available target options"
        fmt.select_option(opt)

        page.locator("#goBtn").click()
        page.wait_for_selector("#rows .row .dl-main", timeout=TIMEOUT)
        _take_screenshot(page, "phasec_single.png")
        browser.close()


def test_two_files_same_target():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        a = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        b = (Path(__file__).resolve().parent / "assets" / "real-test.png").resolve()
        page.locator("#fileInput").set_input_files([str(a), str(b)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        # Select same target for both via globalFmt intersection if present
        global_sel = page.locator("#globalFmt")
        opts = global_sel.evaluate("el => Array.from(el.options).map(o=>o.value).filter(v=>!!v)")
        if opts and len(opts):
            global_sel.select_option(opts[0])
        else:
            # Fallback: set per-row to first option
            rows = page.locator("#rows .row")
            for i in range(rows.count()):
                rows.nth(i).locator("select.fmt").select_option(rows.nth(i).locator("select.fmt").evaluate("el=>Array.from(el.options).map(o=>o.value).filter(v=>!!v)[0]"))

        page.locator("#goBtn").click()
        page.wait_for_selector("#rows .row .dl-main", timeout=TIMEOUT)
        _take_screenshot(page, "phasec_two_same.png")
        browser.close()


def test_two_files_different_targets():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        a = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        b = (Path(__file__).resolve().parent / "assets" / "real-test.png").resolve()
        page.locator("#fileInput").set_input_files([str(a), str(b)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        rows = page.locator("#rows .row")
        # For first row pick first option, for second pick second option if available
        first_opts = rows.nth(0).locator("select.fmt").evaluate("el=>Array.from(el.options).map(o=>o.value).filter(v=>!!v)")
        second_opts = rows.nth(1).locator("select.fmt").evaluate("el=>Array.from(el.options).map(o=>o.value).filter(v=>!!v)")
        assert first_opts and second_opts, "Missing options"
        rows.nth(0).locator("select.fmt").select_option(first_opts[0])
        # Try to pick a different option for second if possible
        choice = second_opts[0] if second_opts[0] != first_opts[0] and len(second_opts) else (second_opts[1] if len(second_opts)>1 else second_opts[0])
        rows.nth(1).locator("select.fmt").select_option(choice)

        page.locator("#goBtn").click()
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)
        _take_screenshot(page, "phasec_two_diff.png")
        browser.close()


def test_three_files_mixed_targets():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(get_base_url(), wait_until="domcontentloaded", timeout=60000)

        a = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
        b = (Path(__file__).resolve().parent / "assets" / "real-test.png").resolve()
        c = (Path(__file__).resolve().parent / "assets" / "real-test.pdf").resolve()
        page.locator("#fileInput").set_input_files([str(a), str(b), str(c)])
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)

        rows = page.locator("#rows .row")
        for i in range(3):
            opts = rows.nth(i).locator("select.fmt").evaluate("el=>Array.from(el.options).map(o=>o.value).filter(v=>!!v)")
            if opts:
                rows.nth(i).locator("select.fmt").select_option(opts[0])

        page.locator("#goBtn").click()
        page.wait_for_selector("#rows .row", timeout=TIMEOUT)
        _take_screenshot(page, "phasec_three_mixed.png")
        browser.close()


def test_partial_success_via_api():
    # Directly post to /convert to simulate a mixed result: one supported, one unsupported
    url = get_base_url().rstrip('/') + '/convert'
    a = (Path(__file__).resolve().parent / "assets" / "real-test.jpg").resolve()
    b = (Path(__file__).resolve().parent / "assets" / "real-test.png").resolve()

    # Choose targets where png->pdf is unsupported (known in phase A matrix) and jpg->webp is supported
    targets = ["webp", "pdf"]
    files = {
        'file': (
            (a.name, open(a, 'rb'), 'application/octet-stream'),
            (b.name, open(b, 'rb'), 'application/octet-stream'),
        )
    }
    # Build multipart payload manually
    files = [
        ('file', (a.name, open(a, 'rb'), 'application/octet-stream')),
        ('file', (b.name, open(b, 'rb'), 'application/octet-stream')),
    ]
    resp = requests.post(url, files=files, data={'targets': json.dumps(targets)})
    assert resp.status_code == 201 or resp.status_code == 200
    data = resp.json()
    assert data.get('results') and len(data['results']) == 2
    # One success, one failed expected
    statuses = [r['status'] for r in data['results']]
    assert 'success' in statuses
    assert 'failed' in statuses
    # Save response for inspection
    (RESULTS_DIR / 'phasec_partial_api.json').write_text(json.dumps(data, indent=2))
