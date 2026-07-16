import json
from pathlib import Path

from app.services.deployment_validation_service import DeploymentValidationService


def _write_contract(contracts_dir: Path, slug: str, source: str, target: str) -> None:
    contracts_dir.mkdir(parents=True, exist_ok=True)

    contract = {
        "id": slug,
        "slug": slug,
        "name": f"{source.upper()} to {target.upper()}",
        "category": "image",
        "description": f"Convert {source.upper()} to {target.upper()}.",
        "input_formats": [source],
        "output_formats": [target],
        "accepted_mime_types": ["image/jpeg"],
        "max_upload_size": 5242880,
        "conversion_engine": "imagemagick",
        "landing_path": f"/{slug}",
        "canonical_url": f"https://converigo.com/{slug}",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.png",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }

    data = {
        "slug": slug,
        "title": f"{source.upper()} to {target.upper()}",
        "description": contract["description"],
        "source": source,
        "target": target,
        "faq": [{"question": "What is this?", "answer": "A conversion tool."}],
        "related_tools": [],
        "hero": {"title": "Convert now", "text": "Easy conversion."},
        "cta": {"title": "Convert now", "text": "Start conversion."},
        "active": True,
    }

    (contracts_dir / f"{slug}.contract.json").write_text(json.dumps(contract), encoding="utf-8")
    (contracts_dir / f"{slug}.json").write_text(json.dumps(data), encoding="utf-8")


def test_deployment_validation_runs_all_stages(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    _write_contract(contracts_dir, "jpg-to-png", "jpg", "png")

    service = DeploymentValidationService(
        contracts_dir=contracts_dir,
        output_dir=tmp_path / "outputs",
    )

    report = service.run_all_checks()

    assert report["stage_count"] == 16
    assert report["failures"] == 0
    assert report["all_passed"] is True
    assert report["warnings"] >= 0
    assert report["deployment_status"] in {"PASS", "WARNING", "FAIL"}
    assert report["production_health"] in {"READY", "WARNING", "NOT READY", "UNKNOWN"}
    assert isinstance(report["seo_publication_report"], dict)
    assert any(stage["name"] == "Production audit summary" for stage in report["stages"])


def test_generate_markdown_report_includes_stage_names(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "contracts"
    _write_contract(contracts_dir, "jpg-to-png", "jpg", "png")

    service = DeploymentValidationService(
        contracts_dir=contracts_dir,
        output_dir=tmp_path / "outputs",
    )

    report = service.run_all_checks()
    markdown = service.generate_markdown_report(report)

    assert "# Deployment Validation Report" in markdown
    assert "1. Contract schema validation" in markdown
    assert "16. Production audit summary" in markdown
    assert "Deployment status:" in markdown
    assert "Production health:" in markdown
    assert "SEO publication ready:" in markdown
