from pathlib import Path
import json

from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.growth_dashboard_service import GrowthDashboardService
from app.services.sitemap_service import SitemapService


def test_growth_dashboard_service_reports_expected_metrics(tmp_path: Path) -> None:
    registry = ConverterRegistry()
    registry.register(
        ConverterInfo(
            id="mp4-to-mp3",
            name="MP4 to MP3",
            category="audio",
            source_format="mp4",
            target_format="mp3",
            enabled=True,
        )
    )
    registry.register(
        ConverterInfo(
            id="png-to-jpg",
            name="PNG to JPG",
            category="image",
            source_format="png",
            target_format="jpg",
            enabled=True,
        )
    )

    # Create test contracts in a temporary directory
    contracts_dir = tmp_path / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    
    (contracts_dir / "mp4-to-mp3.contract.json").write_text(json.dumps({
        "id": "mp4-to-mp3",
        "slug": "mp4-to-mp3",
        "name": "MP4 to MP3",
        "category": "audio",
        "description": "Convert MP4 to MP3",
        "input_formats": ["mp4"],
        "output_formats": ["mp3"],
        "accepted_mime_types": ["video/mp4"],
        "max_upload_size": 5242880,
        "conversion_engine": "ffmpeg",
        "landing_path": "/mp4-to-mp3",
        "canonical_url": "https://converigo.com/mp4-to-mp3",
        "seo_status": "ready",
        "schema_status": "ready",
        "faq_status": "ready",
        "regression_sample": "tests/sample.mp4",
        "supported_platforms": ["web"],
        "lifecycle_status": "active",
    }))
    
    (contracts_dir / "png-to-jpg.contract.json").write_text(json.dumps({
        "id": "png-to-jpg",
        "slug": "png-to-jpg",
        "name": "PNG to JPG",
        "category": "image",
        "description": "Convert PNG to JPG",
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
    }))

    output_dir = tmp_path / "sitemaps"
    output_dir.mkdir(parents=True, exist_ok=True)
    sitemap_service = SitemapService(output_dir=output_dir, registry_instance=registry)
    sitemap_service.generate_all(base_url="https://converigo.com")

    dashboard = GrowthDashboardService(
        registry_instance=registry,
        sitemap_service=sitemap_service,
        output_dir=tmp_path,
        contracts_dir=contracts_dir,
    ).build_dashboard()

    assert dashboard["total_converters"] == 2
    assert dashboard["converters_by_category"]["audio"] == 1
    assert dashboard["converters_by_category"]["image"] == 1
    assert dashboard["total_landing_pages"] == 2
    assert dashboard["total_hub_pages"] == 2
    assert dashboard["registry_health"]["status"] == "healthy"
    assert dashboard["contract_coverage"]["status"] == "healthy"
    assert dashboard["sitemap_coverage"]["status"] == "healthy"
    assert isinstance(dashboard["production_audit"]["landing_coverage"], dict)
    assert isinstance(dashboard["production_audit"]["knowledge_coverage"], dict)
    assert isinstance(dashboard["production_audit"]["hub_coverage"], dict)
    assert dashboard["authority_coverage"]["rate"] == 100.0
    assert dashboard["format_encyclopedia_coverage"]["status"] == "healthy"
    assert dashboard["regression_summary"]["status"] == "healthy"
