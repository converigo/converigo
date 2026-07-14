import json
from pathlib import Path

import pytest

from app.services.converter_registry_service import ConverterRegistryError, ConverterRegistryService


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTERS_DIR = REPO_ROOT / "app" / "data" / "converters"


def test_registry_discovers_contract_files() -> None:
    registry = ConverterRegistryService(CONVERTERS_DIR)

    contracts = registry.list_all()

    assert contracts
    assert any(contract["slug"] == "mp4-to-mp3" for contract in contracts)


def test_registry_validates_required_fields() -> None:
    temp_dir = REPO_ROOT / "tests" / "tmp_registry"
    temp_dir.mkdir(exist_ok=True)
    contract_path = temp_dir / "invalid.contract.json"
    contract_path.write_text(json.dumps({"slug": "bad"}), encoding="utf-8")

    with pytest.raises(ConverterRegistryError):
        ConverterRegistryService(temp_dir)


def test_registry_rejects_duplicate_ids_and_slugs(tmp_path: Path) -> None:
    contract_one = tmp_path / "one.contract.json"
    contract_two = tmp_path / "two.contract.json"
    contract_one.write_text(
        json.dumps(
            {
                "id": "dup",
                "slug": "first",
                "name": "First",
                "category": "audio",
                "description": "A",
                "input_formats": ["mp4"],
                "output_formats": ["mp3"],
                "accepted_mime_types": ["video/mp4"],
                "max_upload_size": 1024,
                "conversion_engine": "ffmpeg",
                "landing_path": "/first",
                "canonical_url": "https://example.com/first",
                "seo_status": "ready",
                "schema_status": "ready",
                "faq_status": "ready",
                "regression_sample": "tests/sample.mp4",
                "supported_platforms": ["web"],
                "lifecycle_status": "active",
            }
        ),
        encoding="utf-8",
    )
    contract_two.write_text(
        json.dumps(
            {
                "id": "dup",
                "slug": "second",
                "name": "Second",
                "category": "audio",
                "description": "B",
                "input_formats": ["mp4"],
                "output_formats": ["mp3"],
                "accepted_mime_types": ["video/mp4"],
                "max_upload_size": 1024,
                "conversion_engine": "ffmpeg",
                "landing_path": "/second",
                "canonical_url": "https://example.com/second",
                "seo_status": "ready",
                "schema_status": "ready",
                "faq_status": "ready",
                "regression_sample": "tests/sample.mp4",
                "supported_platforms": ["web"],
                "lifecycle_status": "active",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConverterRegistryError):
        ConverterRegistryService(tmp_path)


def test_registry_lookup_functions() -> None:
    registry = ConverterRegistryService(CONVERTERS_DIR)

    assert registry.get_by_slug("mp4-to-mp3") is not None
    assert registry.get_by_id("mp4-to-mp3") is not None
    assert registry.get_by_category("audio")
    assert registry.get_active()
    assert registry.get_beta() is not None
