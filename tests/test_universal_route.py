from fastapi.testclient import TestClient

from app.main import app


def test_universal_route_renders_tool_page_for_known_converter():
    client = TestClient(app)
    response = client.get("/jpg-to-pdf")

    assert response.status_code == 200
    assert "Converter tool" in response.text
    assert "Frequently asked questions" in response.text
    assert "Other converters you may need" in response.text


def test_existing_tools_route_still_renders_for_same_converter():
    client = TestClient(app)
    response = client.get("/tools/jpg-to-pdf")

    assert response.status_code == 200
    assert "JPG to PDF Converter" in response.text


def test_universal_tool_page_renders_json_driven_sections():
    client = TestClient(app)
    response = client.get("/png-to-webp")

    assert response.status_code == 200
    assert "Benefits" in response.text
    assert "Use Cases" in response.text
    assert "About Formats" in response.text
