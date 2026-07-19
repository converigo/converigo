from pathlib import Path
import json
from starlette.testclient import TestClient
from app.main import app
from app.core.settings import settings

client = TestClient(app)

sample = Path('tests/assets/regression/sample.jpg')
if not sample.exists():
    print('Sample not found:', sample)
    raise SystemExit(1)

with sample.open('rb') as f:
    files = [('file', ('sample.jpg', f, 'image/jpeg'))]
    data = {'target_format': 'png'}
    resp = client.post('/convert', files=files, data=data)
    print('POST /convert ->', resp.status_code)
    try:
        body = resp.json()
    except Exception:
        print('Response not JSON')
        print(resp.text)
        raise
    print(json.dumps(body, indent=2))

    if resp.status_code != 201:
        raise SystemExit('Conversion request failed')

    result = body.get('results', [])[0]
    download_path = result.get('download_path')
    print('download_path:', download_path)

    # Resolve filesystem path
    if download_path and download_path.startswith('/outputs/'):
        rel = download_path[len('/outputs/'):]
        fs_path = settings.OUTPUT_DIR / Path(rel)
        print('Resolved FS path:', fs_path)
        print('Exists:', fs_path.exists(), 'size:', fs_path.stat().st_size if fs_path.exists() else None)
    else:
        print('Unexpected download_path format')

    # GET the download URL via TestClient
    get_resp = client.get(download_path)
    print('GET', download_path, '->', get_resp.status_code)
    print('Content-Length:', len(get_resp.content))

    if get_resp.status_code != 200:
        raise SystemExit('Download GET failed')

print('Local conversion + download check passed')
