from fastapi.testclient import TestClient

from app.main import app


def test_recommend_pdf_endpoint_returns_200_and_recommendations():
    client = TestClient(app)
    response = client.get("/recommend/pdf")

    assert response.status_code == 200

    data = response.json()

    assert "best_choice" in data
    assert "alternatives" in data
    assert data["best_choice"]["source"] == "pdf"
    assert data["best_choice"]["target"] in {"xlsx", "jpg", "ppt", "docx", "odt", "pdf"}
    assert isinstance(data["alternatives"], list)
    assert len(data["alternatives"]) > 0

    alternative_targets = {item["target"] for item in data["alternatives"]}
    assert "jpg" in alternative_targets or "docx" in alternative_targets
