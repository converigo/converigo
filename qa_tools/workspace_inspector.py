import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get('CONVERIGO_BASE_URL', 'http://127.0.0.1:8000')

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={'width': 1366, 'height': 900})
        page.goto(f"{BASE}/", wait_until='networkidle', timeout=60000)
        page.wait_for_timeout(1000)
        info = page.evaluate('''() => ({
            bodyClass: document.body.className,
            fileInputExists: !!document.querySelector('#fileInput'),
            workspaceHeader: !!document.querySelector('.workspace-header'),
            fileListPanelHidden: document.getElementById('fileListPanel')?.hidden || false
        })''')
        print('WORKSPACE INFO:', info)
        browser.close()

if __name__ == '__main__':
    main()
