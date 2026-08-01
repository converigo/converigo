from fastapi.testclient import TestClient
from app.main import app
from pathlib import Path

def main():
    client = TestClient(app)
    p = Path('test_files/sample.mp4')
    if not p.exists():
        print('sample missing', p)
        return
    with p.open('rb') as fh:
        resp = client.post('/convert', files={'file': (p.name, fh, 'video/mp4')}, data={'target_format':'mp3'})
        print('status', resp.status_code)
        print(resp.text[:1000])

if __name__ == '__main__':
    main()
