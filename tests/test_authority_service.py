from pathlib import Path
import json

from app.services.authority_service import AuthorityService


def _write_contracts(contracts_dir: Path, contracts: list[dict]) -> None:
    contracts_dir.mkdir(parents=True, exist_ok=True)
    for contract in contracts:
        (contracts_dir / f"{contract['slug']}.contract.json").write_text(json.dumps(contract), encoding="utf-8")


def test_every_known_format_generates_authority_payload(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
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
            "description": "Convert PNG images into JPG images.",
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
    _write_contracts(contracts_dir, contracts)

    service = AuthorityService(contracts_dir)
    payloads = service.generate_all()

    assert "mp4" in payloads
    assert "mp3" in payloads
    assert "png" in payloads
    assert "jpg" in payloads
    for payload in payloads.values():
        assert all(section in payload for section in AuthorityService.REQUIRED_SECTIONS)


def test_authority_payload_is_deterministic(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contract = {
        "id": "pdf-to-docx",
        "slug": "pdf-to-docx",
        "name": "PDF to DOCX",
        "category": "document",
        "description": "Convert PDF documents into Word files.",
        "input_formats": ["pdf"],
        "output_formats": ["docx"],
        "accepted_mime_types": ["application/pdf"],
        "max_upload_size": 104857600,
        "conversion_engine": "document",
        "landing_path": "/pdf-to-docx",
        "canonical_url": "https://converigo.com/pdf-to-docx",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.pdf",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    _write_contracts(contracts_dir, [contract])

    service = AuthorityService(contracts_dir)
    first = service.generate_payload("pdf")
    second = service.generate_payload("pdf")

    assert first == second


def test_authority_payload_has_no_duplicate_sections(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contract = {
        "id": "pdf-to-docx",
        "slug": "pdf-to-docx",
        "name": "PDF to DOCX",
        "category": "document",
        "description": "Convert PDF documents into Word files.",
        "input_formats": ["pdf"],
        "output_formats": ["docx"],
        "accepted_mime_types": ["application/pdf"],
        "max_upload_size": 104857600,
        "conversion_engine": "document",
        "landing_path": "/pdf-to-docx",
        "canonical_url": "https://converigo.com/pdf-to-docx",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.pdf",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    _write_contracts(contracts_dir, [contract])

    service = AuthorityService(contracts_dir)
    payload = service.generate_payload("pdf")

    assert len(payload) == len(set(payload.keys()))
