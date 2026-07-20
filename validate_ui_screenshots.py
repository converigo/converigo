from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path.cwd()


def copy_asset(name: str, source: Path) -> Path:
    dest = ROOT / name
    dest.write_bytes(source.read_bytes())
    return dest


if __name__ == '__main__':
    copy_asset('file1.jpg', ROOT / 'tests' / 'assets' / 'real-test.jpg')
    copy_asset('file2.jpg', ROOT / 'tests' / 'assets' / 'regression' / 'sample.jpg')
    copy_asset('file3.jpg', ROOT / 'tests' / 'assets' / 'real-test.jpg')

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.screenshot(path=str(ROOT / 'validation_initial.png'), full_page=True)

        result = page.evaluate("""
        () => {
          const resultCard = document.getElementById('resultCard');
          const errorCard = document.getElementById('errorCard');
          const downloadBtn = document.getElementById('downloadBtn');
          const preview = document.getElementById('previewContainer');
          const fileList = document.getElementById('fileList');
          const uploadHint = document.getElementById('uploadHint');
          return {
            resultCardHidden: !!resultCard?.hidden,
            errorCardHidden: !!errorCard?.hidden,
            downloadBtnHidden: !!downloadBtn?.hidden,
            previewHidden: !!preview?.hidden,
            fileListHidden: !!fileList?.hidden,
            uploadHintHidden: !!uploadHint?.hidden
          };
        }
        """)
        print('initial_state', result)

        page.locator('#fileInput').set_input_files([
            str(ROOT / 'file1.jpg'),
            str(ROOT / 'file2.jpg'),
            str(ROOT / 'file3.jpg'),
        ])
        page.wait_for_timeout(1500)
        page.screenshot(path=str(ROOT / 'validation_multifile.png'), full_page=True)

        page.set_viewport_size({'width': 390, 'height': 844})
        page.goto('http://127.0.0.1:8000/', wait_until='networkidle')
        page.wait_for_timeout(1000)
        page.screenshot(path=str(ROOT / 'validation_mobile.png'), full_page=True)

        browser.close()
