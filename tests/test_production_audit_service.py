from pathlib import Path
import json

from app.services.production_audit_service import ProductionAuditService


def _write_contracts(contracts_dir: Path, contracts: list[dict]) -> None:
    contracts_dir.mkdir(parents=True, exist_ok=True)
    for contract in contracts:
        (contracts_dir / f"{contract['slug']}.contract.json").write_text(json.dumps(contract), encoding="utf-8")


def test_audit_passes_for_valid_converters(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    contract = {
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
    }
    _write_contracts(contracts_dir, [contract])

    service = ProductionAuditService(contracts_dir=contracts_dir, converter_data_dir=Path("app/data/converters"))
    audit = service.audit_all()

    assert audit["summary"]["total_converters"] == 1
    assert audit["summary"]["ready_count"] == 1
    assert audit["results"][0]["status"] == "READY"
    assert audit["results"][0]["quality_score"] == 100


def test_missing_sections_reduce_score_and_detect_hub_issues(tmp_path: Path, monkeypatch) -> None:
    contracts_dir = tmp_path / "contracts"
    contract = {
        "id": "general-tool",
        "slug": "general-tool",
        "name": "General Tool",
        "category": "general",
        "description": "A general conversion tool.",
        "input_formats": ["png"],
        "output_formats": ["jpg"],
        "accepted_mime_types": ["image/png"],
        "max_upload_size": 5242880,
        "conversion_engine": "imagemagick",
        "landing_path": "/general-tool",
        "canonical_url": "https://converigo.com/general-tool",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.png",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    _write_contracts(contracts_dir, [contract])

    service = ProductionAuditService(contracts_dir=contracts_dir, converter_data_dir=Path("app/data/converters"))

    original_build = service.landing_builder.build_context

    def broken_build_context(request, tool_data, faq_items=None, canonical_path=None, meta_overrides=None):
        landing = original_build(request, tool_data, faq_items=faq_items, canonical_path=canonical_path, meta_overrides=meta_overrides)
        landing.pop("steps")
        landing.pop("benefits")
        return landing

    monkeypatch.setattr(service.landing_builder, "build_context", broken_build_context)

    result = service.audit_converter(contract)

    assert result["quality_score"] < 100
    assert result["status"] in {"WARNING", "NOT READY"}
    assert result["checks"]["landing_contract"] is False
    assert result["checks"]["hub_inclusion"] is False
