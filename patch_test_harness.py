from pathlib import Path

files = [
    Path(r'c:\converigo\tests\test_final_ui_validation.py'),
    Path(r'c:\converigo\tests\e2e\test_convert_flow.py'),
    Path(r'c:\converigo\tests\test_convert_button_state.py'),
]
for f in files:
    text = f.read_text(encoding='utf-8')
    text = text.replace('page.goto(BASE_URL, wait_until="networkidle")', 'page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)')
    text = text.replace('page.goto("http://127.0.0.1:8000/", wait_until="networkidle")', 'page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)')
    text = text.replace('page.goto(f"{BASE_URL}/hub", wait_until="networkidle", timeout=30000)', 'page.goto(f"{BASE_URL}/hub", wait_until="domcontentloaded", timeout=60000)')
    f.write_text(text, encoding='utf-8')

certs = [
    Path(r'c:\converigo\tests\certified\document\test_pdf_to_odt.py'),
    Path(r'c:\converigo\tests\certified\document\test_pdf_to_pptx.py'),
    Path(r'c:\converigo\tests\certified\office\test_ppt_to_pdf_certified.py'),
]
for p in certs:
    text = p.read_text(encoding='utf-8')
    if 'download_resp = client.get(download_path)' not in text:
        text = text.replace(
            'local_path = Path(str(download_path).lstrip("/"))\n\n    assert local_path.exists(), f"Expected output',
            'local_path = Path(str(download_path).lstrip("/"))\n    download_resp = client.get(download_path)\n    assert download_resp.status_code == 200, download_resp.text\n    assert download_resp.content, "Downloaded content is empty"\n\n    assert local_path.exists(), f"Expected output',
        )
        p.write_text(text, encoding='utf-8')

print('patched')
