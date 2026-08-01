from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.get('/png-to-webp')
print('status', response.status_code)
print('has_benefits', 'Benefits' in response.text)
print('has_class', 'class="benefits-section"' in response.text)
print('has_item', 'Smaller file sizes' in response.text)
