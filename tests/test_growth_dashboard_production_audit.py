from pathlib import Path
import json

from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.growth_dashboard_service import GrowthDashboardService


def _write_contract(contracts_dir: Path, slug: str, name: str, category: str, faq_status: str = "ready") -> None:
    contracts_dir.mkdir(parents=True, exist_ok=True)
    contract = {
        "id": slug,
        "slug": slug,
        "name": name,
        "category": category,
        "description": f"Description for {name}",
        "input_formats": ["png"],
        "output_formats": ["jpg"],
        "accepted_mime_types": ["image/png"],
        "max_upload_size": 5242880,
        "conversion_engine": "imagemagick",
        "landing_path": f"/{slug}",
        "canonical_url": f"https://converigo.com/{slug}",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": faq_status,
        "regression_sample": "tests/sample.png",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }
    (contracts_dir / f"{slug}.contract.json").write_text(json.dumps(contract), encoding="utf-8")


def test_dashboard_metrics_match_audit_summary(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    converter_data_dir = tmp_path / "converter-data"
    converter_data_dir.mkdir(parents=True, exist_ok=True)

    _write_contract(contracts_dir, "ready-tool", "Ready Tool", "image", faq_status="ready")
    _write_contract(contracts_dir, "warning-tool", "Warning Tool", "image", faq_status="pending")
    _write_contract(contracts_dir, "not-ready-tool", "Not Ready Tool", "image", faq_status="pending")

    (converter_data_dir / "ready-tool.json").write_text(json.dumps({
        "slug": "ready-tool",
        "title": "Ready Tool",
        "description": "Description for ready-tool",
        "source": "png",
        "target": "jpg",
        "faq": [{"question": "Test", "answer": "Answer"}],
        "related_tools": [{"slug": "png-to-jpg", "name": "PNG to JPG"}],
        "hero": {"title": "Ready tool converter"},
        "cta": {"title": "Convert now", "text": "Now"},
        "active": True,
    }), encoding="utf-8")

    (converter_data_dir / "warning-tool.json").write_text(json.dumps({
        "slug": "warning-tool",
        "title": "Warning Tool",
        "description": "Description for warning-tool",
        "source": "png",
        "target": "jpg",
        "related_tools": [],
        "hero": {"title": "Warning tool converter"},
        "cta": {"title": "Convert now", "text": "Now"},
        "active": True,
    }), encoding="utf-8")

    registry = ConverterRegistry()
    registry.register(ConverterInfo(id="ready-tool", name="Ready Tool", category="image", source_format="png", target_format="jpg", enabled=True))
    registry.register(ConverterInfo(id="warning-tool", name="Warning Tool", category="image", source_format="png", target_format="jpg", enabled=True))
    registry.register(ConverterInfo(id="not-ready-tool", name="Not Ready Tool", category="image", source_format="png", target_format="jpg", enabled=True))

    dashboard_service = GrowthDashboardService(
        registry_instance=registry,
        output_dir=tmp_path / "outputs",
        contracts_dir=contracts_dir,
        converter_data_dir=converter_data_dir,
    )
    dashboard = dashboard_service.build_dashboard()

    audit_summary = dashboard["production_audit"]
    assert audit_summary["total_converters"] == 3
    assert audit_summary["counts_by_status"]["READY"] >= 1
    assert audit_summary["counts_by_status"]["NOT READY"] >= 1
    assert sum(audit_summary["counts_by_status"].values()) == 3
    assert audit_summary["average_quality_score"] >= 0
