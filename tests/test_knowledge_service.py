from pathlib import Path

from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_service import KnowledgeService


def test_every_active_converter_generates_knowledge_payload(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    contracts = [
        {
            "id": "mp4-to-mp3",
            "slug": "mp4-to-mp3",
            "name": "MP4 to MP3",
            "category": "audio",
            "description": "Convert MP4 video files into MP3 audio.",
            "input_formats": ["mp4"],
            "output_formats": ["mp3"],
            "accepted_mime_types": ["video/mp4"],
            "max_upload_size": 104857600,
            "conversion_engine": "ffmpeg",
            "landing_path": "/mp4-to-mp3",
            "canonical_url": "https://converigo.com/mp4-to-mp3",
            "seo_status": "ready",
            "schema_status": "ready",
            "faq_status": "ready",
            "regression_sample": "tests/sample.mp4",
            "supported_platforms": ["web"],
            "lifecycle_status": "active",
        },
        {
            "id": "png-to-jpg",
            "slug": "png-to-jpg",
            "name": "PNG to JPG",
            "category": "image",
            "description": "Convert PNG image files into JPG images.",
            "input_formats": ["png"],
            "output_formats": ["jpg"],
            "accepted_mime_types": ["image/png"],
            "max_upload_size": 5242880,
            "conversion_engine": "imagemagick",
            "landing_path": "/png-to-jpg",
            "canonical_url": "https://converigo.com/png-to-jpg",
            "seo_status": "ready",
            "schema_status": "ready",
            "faq_status": "ready",
            "regression_sample": "tests/sample.png",
            "supported_platforms": ["web"],
            "lifecycle_status": "active",
        },
    ]

    for contract in contracts:
        (contracts_dir / f"{contract['slug']}.contract.json").write_text(__import__("json").dumps(contract), encoding="utf-8")

    service = KnowledgeService(contracts_dir)
    payloads = service.generate_all()

    assert set(payloads) == {"mp4-to-mp3", "png-to-jpg"}
    for payload in payloads.values():
        assert payload["slug"]
        assert payload["source_format"]
        assert payload["target_format"]
        assert payload["what_is_source"]["title"]
        assert payload["what_is_target"]["title"]
        assert payload["differences"]
        assert payload["advantages"]
        assert payload["limitations"]
        assert payload["best_practices"]
        assert payload["common_mistakes"]
        assert payload["tips"]
        assert payload["faq_enrichment"]
        assert payload["glossary"]


def test_knowledge_payload_is_deterministic(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    contract = {
        "id": "jpg-to-pdf",
        "slug": "jpg-to-pdf",
        "name": "JPG to PDF",
        "category": "document",
        "description": "Convert JPG images into PDF documents.",
        "input_formats": ["jpg"],
        "output_formats": ["pdf"],
        "accepted_mime_types": ["image/jpeg"],
        "max_upload_size": 10485760,
        "conversion_engine": "imagemagick",
        "landing_path": "/jpg-to-pdf",
        "canonical_url": "https://converigo.com/jpg-to-pdf",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.jpg",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    (contracts_dir / "jpg-to-pdf.contract.json").write_text(__import__("json").dumps(contract), encoding="utf-8")

    service = KnowledgeService(contracts_dir)
    first = service.generate_payload(contract)
    second = service.generate_payload(contract)
    assert first == second
