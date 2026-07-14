from fastapi.testclient import TestClient

from app.main import app
from app.services.comparison_service import ComparisonService


def test_comparison_service_builds_expected_sections() -> None:
    service = ComparisonService()
    payload = service.build_payload("pdf-vs-docx")

    assert payload["h1"]
    assert payload["introduction"]["title"]
    assert payload["winner_summary"]["title"]
    assert payload["comparison_table"]
    assert payload["advantages"]
    assert payload["disadvantages"]
    assert payload["best_use_cases"]
    assert payload["faq"]
    assert payload["related_converters"]
    assert payload["related_formats"]
    assert payload["internal_links"]
    assert payload["json_ld"]["@context"] == "https://schema.org"
    assert payload["breadcrumb"]


def test_comparison_route_renders_the_expected_content() -> None:
    client = TestClient(app)

    response = client.get("/pdf-vs-docx")

    assert response.status_code == 200
    assert "Feature comparison" in response.text
    assert "Best use cases" in response.text
    assert "Winner summary" in response.text
    assert "application/ld+json" in response.text
