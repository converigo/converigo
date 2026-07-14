import json
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
CONVERTER_DIR = REPO_ROOT / "app" / "data" / "converters"
CONTRACT_DOC = REPO_ROOT / "docs" / "CONVERTER_CONTRACT.md"
CONTRACT_EXAMPLE = CONVERTER_DIR / "mp4-to-mp3.contract.json"


REQUIRED_FIELDS = [
    "id",
    "slug",
    "name",
    "category",
    "description",
    "input_formats",
    "output_formats",
    "accepted_mime_types",
    "max_upload_size",
    "conversion_engine",
    "landing_path",
    "canonical_url",
    "seo_status",
    "schema_status",
    "faq_status",
    "regression_sample",
    "supported_platforms",
    "lifecycle_status",
]


def _load_contract(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_converter_contract_document_exists() -> None:
    assert CONTRACT_DOC.exists()


def test_converter_contract_example_exists_and_has_required_fields() -> None:
    contract = _load_contract(CONTRACT_EXAMPLE)

    for field in REQUIRED_FIELDS:
        assert field in contract

    assert isinstance(contract["input_formats"], list) and contract["input_formats"]
    assert isinstance(contract["output_formats"], list) and contract["output_formats"]
    assert isinstance(contract["accepted_mime_types"], list) and contract["accepted_mime_types"]
    assert isinstance(contract["supported_platforms"], list) and contract["supported_platforms"]
    assert contract["lifecycle_status"] in {"active", "deprecated", "beta"}


def test_all_converter_contract_files_in_data_dir_have_required_fields() -> None:
    contract_files = sorted(CONVERTER_DIR.glob("*.contract.json"))
    assert contract_files, "No converter contract files were found"

    for contract_file in contract_files:
        contract = _load_contract(contract_file)

        for field in REQUIRED_FIELDS:
            assert field in contract, f"Missing field {field} in {contract_file.name}"

        assert isinstance(contract["input_formats"], list) and contract["input_formats"]
        assert isinstance(contract["output_formats"], list) and contract["output_formats"]
        assert isinstance(contract["accepted_mime_types"], list) and contract["accepted_mime_types"]
        assert isinstance(contract["supported_platforms"], list) and contract["supported_platforms"]
        assert contract["lifecycle_status"] in {"active", "deprecated", "beta"}

        if contract.get("lifecycle_status") == "active":
            sample_path = REPO_ROOT / contract["regression_sample"]
            assert sample_path.exists(), f"Regression sample missing for {contract_file.name}"
