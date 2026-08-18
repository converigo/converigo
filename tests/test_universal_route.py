from fastapi.testclient import TestClient

from app.main import app


def test_universal_route_redirects_legacy_jpg_to_pdf_url():
    client = TestClient(app)
    response = client.get("/jpg-to-pdf", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == "/tools/jpg-to-pdf"


def test_existing_tools_route_still_renders_for_same_converter():
    client = TestClient(app)
    response = client.get("/tools/jpg-to-pdf")

    assert response.status_code == 200
    assert "JPG to PDF Converter" in response.text


def test_universal_tool_page_redirects_legacy_png_to_webp_url():
    client = TestClient(app)
    response = client.get("/png-to-webp", follow_redirects=False)

    assert response.status_code == 301
    assert response.headers["location"] == "/tools/png-to-webp"
