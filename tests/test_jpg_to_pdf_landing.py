from fastapi.testclient import TestClient

from app.main import app


def test_jpg_to_pdf_landing_page_redirects_to_canonical_tools_url():
    client = TestClient(app)
    response = client.get("/jpg-to-pdf", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == "/tools/jpg-to-pdf"
