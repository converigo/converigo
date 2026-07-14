import json
from pathlib import Path

from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.programmatic_seo_service import ProgrammaticSEOService


def test_programmatic_seo_service_generates_payloads_for_active_contracts(tmp_path: Path) -> None:
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
        {
            "id": "pdf-to-jpg",
            "slug": "pdf-to-jpg",
            "name": "PDF to JPG",
            "category": "pdf",
            "description": "Convert PDF documents into JPG images.",
            "input_formats": ["pdf"],
            "output_formats": ["jpg"],
            "accepted_mime_types": ["application/pdf"],
            "max_upload_size": 10485760,
            "conversion_engine": "imagemagick",
            "landing_path": "/pdf-to-jpg",
            "canonical_url": "https://converigo.com/pdf-to-jpg",
            "seo_status": "ready",
            "schema_status": "ready",
            "faq_status": "ready",
            "regression_sample": "tests/sample.pdf",
            "supported_platforms": ["web"],
            "lifecycle_status": "active",
        },
    ]

    for contract in contracts:
        (contracts_dir / f"{contract['slug']}.contract.json").write_text(json.dumps(contract), encoding="utf-8")

    registry = ConverterRegistry()
    registry.register(
        ConverterInfo(id="mp4-to-mp3", name="MP4 to MP3", category="audio", source_format="mp4", target_format="mp3", enabled=True)
    )
    registry.register(
        ConverterInfo(id="png-to-jpg", name="PNG to JPG", category="image", source_format="png", target_format="jpg", enabled=True)
    )

    service = ProgrammaticSEOService(contracts_dir=contracts_dir, registry_instance=registry)
    payloads = service.generate_all()

    assert set(payloads) == {"mp4-to-mp3", "png-to-jpg"}

    for payload in payloads.values():
        assert payload["seo_title"]
        assert payload["meta_description"]
        assert payload["intro"]
        assert payload["steps"]
        assert payload["benefits"]
        assert payload["supported_formats"]
        assert payload["tips"]
        assert payload["common_problems"]
        assert payload["faq"]
        assert 8 <= len(payload["faq"]) <= 12
        assert payload["cta"]
        assert payload["related_keywords"]
        assert payload["related_converters"]
        assert payload["breadcrumb"]
        assert payload["json_ld"]
        assert payload["canonical_url"].startswith("https://converigo.com/")

    first_run = service.generate_all()
    second_run = service.generate_all()
    assert first_run == second_run
