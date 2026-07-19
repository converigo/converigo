from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class ConverterRegistryError(ValueError):
    """Raised when a converter contract is invalid or duplicated."""


class ConverterRegistryService:
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
    VALID_LIFECYCLE_STATUSES = {"active", "deprecated", "beta", "certified"}

    def __init__(self, contracts_dir: Path | str) -> None:
        self.contracts_dir = Path(contracts_dir)
        self._contracts: list[dict[str, Any]] = []
        self._load_contracts()

    def _load_contracts(self) -> None:
        if not self.contracts_dir.exists():
            return

        contract_paths = sorted(self.contracts_dir.glob("*.contract.json"))
        contracts: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        seen_slugs: set[str] = set()

        for contract_path in contract_paths:
            contract = self._load_contract(contract_path)
            self._validate_contract(contract, contract_path)

            contract_id = str(contract["id"]).strip()
            slug = str(contract["slug"]).strip()
            if contract_id in seen_ids:
                raise ConverterRegistryError(f"Duplicate converter id: {contract_id}")
            if slug in seen_slugs:
                raise ConverterRegistryError(f"Duplicate converter slug: {slug}")

            seen_ids.add(contract_id)
            seen_slugs.add(slug)
            contracts.append(contract)

        self._contracts = contracts

    def _load_contract(self, contract_path: Path) -> dict[str, Any]:
        with contract_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _validate_contract(self, contract: dict[str, Any], contract_path: Path) -> None:
        for field in self.REQUIRED_FIELDS:
            if field not in contract:
                raise ConverterRegistryError(f"Missing required field '{field}' in {contract_path.name}")

        for field in ["id", "slug", "name", "category", "description", "conversion_engine", "landing_path", "canonical_url", "seo_status", "schema_status", "faq_status", "regression_sample", "lifecycle_status"]:
            value = contract.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ConverterRegistryError(f"Invalid value for '{field}' in {contract_path.name}")

        if not isinstance(contract.get("input_formats"), list) or not contract["input_formats"]:
            raise ConverterRegistryError(f"Invalid input_formats in {contract_path.name}")
        if not isinstance(contract.get("output_formats"), list) or not contract["output_formats"]:
            raise ConverterRegistryError(f"Invalid output_formats in {contract_path.name}")
        if not isinstance(contract.get("accepted_mime_types"), list) or not contract["accepted_mime_types"]:
            raise ConverterRegistryError(f"Invalid accepted_mime_types in {contract_path.name}")
        if not isinstance(contract.get("supported_platforms"), list) or not contract["supported_platforms"]:
            raise ConverterRegistryError(f"Invalid supported_platforms in {contract_path.name}")

        lifecycle_status = str(contract.get("lifecycle_status", "")).strip().lower()
        if lifecycle_status not in self.VALID_LIFECYCLE_STATUSES:
            raise ConverterRegistryError(f"Invalid lifecycle_status in {contract_path.name}")

        if not isinstance(contract.get("max_upload_size"), int) or contract["max_upload_size"] <= 0:
            raise ConverterRegistryError(f"Invalid max_upload_size in {contract_path.name}")

    def list_all(self) -> list[dict[str, Any]]:
        return list(self._contracts)

    def get_by_slug(self, slug: str) -> dict[str, Any] | None:
        for contract in self._contracts:
            if str(contract.get("slug", "")).strip().lower() == str(slug).strip().lower():
                return contract
        return None

    def get_by_id(self, id_: str) -> dict[str, Any] | None:
        for contract in self._contracts:
            if str(contract.get("id", "")).strip().lower() == str(id_).strip().lower():
                return contract
        return None

    def get_by_category(self, category: str) -> list[dict[str, Any]]:
        return [
            contract
            for contract in self._contracts
            if str(contract.get("category", "")).strip().lower() == str(category).strip().lower()
        ]

    def get_active(self) -> list[dict[str, Any]]:
        # Treat active, deprecated, and certified contracts as published items for registration,
        # hub pages, sitemap generation, and production audit checks.
        return [
            contract
            for contract in self._contracts
            if str(contract.get("lifecycle_status", "")).strip().lower() in {"active", "deprecated", "certified"}
        ]

    def get_beta(self) -> list[dict[str, Any]]:
        return [contract for contract in self._contracts if str(contract.get("lifecycle_status", "")).strip().lower() == "beta"]
