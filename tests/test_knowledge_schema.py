from pathlib import Path

from app.services.knowledge_service import KnowledgeService
from app.services.knowledge_schema import KNOWLEDGE_REQUIRED_SECTIONS


def test_knowledge_service_builds_expected_structure(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    contract = {
        "id": "pdf-to-word",
        "slug": "pdf-to-word",
        "name": "PDF to Word",
        "category": "document",
        "description": "Convert PDF documents into editable Word files.",
        "input_formats": ["pdf"],
        "output_formats": ["docx"],
        "accepted_mime_types": ["application/pdf"],
        "max_upload_size": 104857600,
        "conversion_engine": "document",
        "landing_path": "/pdf-to-word",
        "canonical_url": "https://converigo.com/pdf-to-word",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.pdf",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    (contracts_dir / "pdf-to-word.contract.json").write_text(__import__("json").dumps(contract), encoding="utf-8")

    service = KnowledgeService(contracts_dir)
    payload = service.generate_payload(contract)

    assert payload["slug"] == "pdf-to-word"
    assert payload["overview"]["title"] == "Overview of PDF to Word"
    assert payload["source_format"]["format"] == "PDF"
    assert payload["target_format"]["format"] == "DOCX"
    assert payload["advantages"]
    assert payload["limitations"]
    assert payload["use_cases"]
    assert payload["faq"]
    assert payload["related_converters"]
    assert payload["internal_links"]["title"] == "Related resources"
    assert payload["hub_reference"]["href"] == "/pdf-tools"
    for section in KNOWLEDGE_REQUIRED_SECTIONS:
        assert section in payload
