from pathlib import Path
import json

from fastapi.testclient import TestClient

from app.main import app
import app.routers.formats as formats_router
from app.services.authority_service import AuthorityService


def test_format_index_and_each_format_page(tmp_path: Path, monkeypatch) -> None:
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)

    contracts = [
        {
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
        },
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
    ]

    for contract in contracts:
        (contracts_dir / f"{contract['slug']}.contract.json").write_text(json.dumps(contract), encoding="utf-8")

    monkeypatch.setattr(formats_router, "CONTRACTS_DIR", contracts_dir)
    monkeypatch.setattr(formats_router, "_authority_service", lambda: AuthorityService(contracts_dir))
    monkeypatch.setattr(formats_router, "_converter_registry", lambda: formats_router.ConverterRegistryService(contracts_dir))

    client = TestClient(app)
    response = client.get("/formats")
    assert response.status_code == 200
    assert "Format Encyclopedia" in response.text

    service = AuthorityService(contracts_dir)
    payloads = service.generate_all()
    assert "pdf" in payloads
    assert "docx" in payloads
    assert "mp4" in payloads
    assert "mp3" in payloads

    for fmt in ["pdf", "docx", "mp4", "mp3"]:
        response = client.get(f"/formats/{fmt}")
        assert response.status_code == 200
        assert payloads[fmt]["title"] in response.text
        assert payloads[fmt]["description"] in response.text
        assert payloads[fmt]["mime_type"] in response.text


def test_format_page_404_for_unknown_format() -> None:
    client = TestClient(app)
    response = client.get("/formats/unknownformat")
    assert response.status_code == 404
