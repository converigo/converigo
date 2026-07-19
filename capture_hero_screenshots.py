from playwright.sync_api import sync_playwright
import os, time

os.makedirs('screenshots', exist_ok=True)
sizes = [(1920, 1080, 'hero-1920x1080.png'), (1366, 768, 'hero-1366x768.png'), (390, 844, 'hero-390x844.png')]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for w, h, name in sizes:
        page = browser.new_page(viewport={'width': w, 'height': h})
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        time.sleep(1)
        page.screenshot(path=os.path.join('screenshots', name), full_page=True)
    browser.close()

print('saved', [s[2] for s in sizes])
