from starlette.testclient import TestClient
from app.main import app

def main():
    client = TestClient(app)
    print('ROUTES:', len(app.routes))
    for r in app.routes:
        print(getattr(r, 'path', None), getattr(r, 'methods', None), getattr(r, 'name', None))
    res = client.get('/health')
    print('HEALTH:', res.status_code, res.json() if res.status_code == 200 else res.text[:200])

if __name__ == '__main__':
    main()
