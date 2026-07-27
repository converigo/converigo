from fastapi.testclient import TestClient

from app.main import app


def test_seo_operations_dashboard_renders() -> None:
    client = TestClient(app)
    response = client.get("/dashboard/seo-operations")

    assert response.status_code == 200
    assert "SEO Operations Dashboard" in response.text
    assert "Total Learning Articles" in response.text
    assert "Internal Link Count" in response.text
    assert "Certified Converters" in response.text
    assert "Published This Month" in response.text
    assert "Indexed URLs" in response.text
    assert "Total Visitor" in response.text
