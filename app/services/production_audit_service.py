from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.registry import ConverterInfo, ConverterRegistry, registry
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_service import KnowledgeService
from app.services.authority_service import AuthorityService
from app.services.landing_service import LandingPageBuilder
from app.services.related_converter_service import RelatedConverterService
from app.services.seo_service import SeoService
from app.services.sitemap_service import SitemapService
from app.services.hub_page_service import HubPageService


class ProductionAuditService:
    """Aggregate existing validation signals into lightweight production audit metrics."""

    def __init__(
        self,
        contracts_dir: Path | str | None = None,
        converter_data_dir: Path | str | None = None,
        registry_instance: ConverterRegistry | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_data_dir = Path(converter_data_dir or "app/data/converters")
        self.registry = registry_instance or registry
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.converter_data_service = ConverterDataService(self.converter_data_dir)
        self.seo_service = SeoService(self.converter_data_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.related_service = RelatedConverterService(self.converter_data_service)
        self.sitemap_service = SitemapService(output_dir=Path("outputs/sitemaps"), registry_instance=self.registry)
        self.hub_service = HubPageService(registry_instance=self.registry)
        self._register_active_contracts()

    def audit_all(self) -> dict[str, Any]:
        results = [self.audit_converter(contract) for contract in self.converter_registry_service.get_active()]
        ready_count = sum(1 for result in results if result.get("status") == "READY")
        warning_count = sum(1 for result in results if result.get("status") == "WARNING")
        not_ready_count = sum(1 for result in results if result.get("status") == "NOT READY")
        return {
            "summary": {
                "total_converters": len(results),
                "ready_count": ready_count,
                "warning_count": warning_count,
                "not_ready_count": not_ready_count,
                "quality_score_average": round(sum(result.get("quality_score", 0) for result in results) / len(results), 2) if results else 100,
            },
            "results": results,
        }

    def audit_converter(self, contract: dict[str, Any]) -> dict[str, Any]:
        slug = str(contract.get("slug", "")).strip()
        checks: dict[str, Any] = {
            "converter_contract": bool(contract.get("slug") and contract.get("name") and contract.get("description")),
            "landing_contract": False,
            "knowledge_payload": False,
            "authority_payload": False,
            "encyclopedia_page": False,
            "faq_coverage": False,
            "internal_links": False,
            "related_converters": False,
            "sitemap_inclusion": False,
            "hub_inclusion": False,
        }

        try:
            tool_data = self.converter_data_service.load_converter_by_slug(slug)
        except FileNotFoundError:
            tool_data = None

        landing: dict[str, Any] | None = None
        if tool_data:
            try:
                landing = self.landing_builder.build_context(type("Request", (), {})(), tool_data)
                self.landing_builder.validate_contract(landing)
                checks["landing_contract"] = True
            except Exception:
                checks["landing_contract"] = False

            if tool_data.get("faq") or str(contract.get("faq_status", "")).lower() == "ready":
                checks["faq_coverage"] = True

            if tool_data.get("related_tools"):
                checks["related_converters"] = True

            if landing is not None:
                checks["internal_links"] = bool(landing.get("internal_links", {}).get("items"))

            try:
                knowledge = self.knowledge_service.generate_payload(contract)
                checks["knowledge_payload"] = bool(knowledge)
            except Exception:
                checks["knowledge_payload"] = False

            authority_format = str((contract.get("input_formats") or [""])[0]).strip().lower() or str((contract.get("output_formats") or [""])[0]).strip().lower()
            if authority_format:
                try:
                    authority = self.authority_service.generate_payload(authority_format)
                    checks["authority_payload"] = bool(authority)
                    checks["encyclopedia_page"] = bool(authority)
                except Exception:
                    checks["authority_payload"] = False
                    checks["encyclopedia_page"] = False
            else:
                checks["authority_payload"] = False
                checks["encyclopedia_page"] = False

        try:
            self.sitemap_service.generate_all(base_url="https://converigo.com")
            checks["sitemap_inclusion"] = not bool(self.sitemap_service.validate())
        except Exception:
            checks["sitemap_inclusion"] = False

        try:
            hub_pages = self.hub_service.build_all()
            checks["hub_inclusion"] = self._is_converter_in_hub(slug, hub_pages)
        except Exception:
            checks["hub_inclusion"] = False

        if checks.get("related_converters") is False:
            related_tools = self.related_service.get_related_converters(tool_data or contract, limit=4) if tool_data else []
            checks["related_converters"] = bool(related_tools)

        quality_score = self._score_checks(checks)
        status = self._derive_status(quality_score)
        return {
            "slug": slug,
            "name": contract.get("name", slug),
            "checks": checks,
            "quality_score": quality_score,
            "status": status,
        }

    def _register_active_contracts(self) -> None:
        for contract in self.converter_registry_service.get_active():
            slug = str(contract.get("slug", "")).strip()
            if not slug:
                continue
            if self.registry.get(slug) is not None:
                continue
            source_format = str((contract.get("input_formats") or [""])[0]).strip()
            target_format = str((contract.get("output_formats") or [""])[0]).strip()
            self.registry.register(
                ConverterInfo(
                    id=slug,
                    name=str(contract.get("name", slug)),
                    category=str(contract.get("category", "general")).lower(),
                    source_format=source_format,
                    target_format=target_format,
                    enabled=True,
                )
            )

    def _is_converter_in_hub(self, slug: str, hub_pages: dict[str, Any]) -> bool:
        if not slug:
            return False
        for page in hub_pages.values():
            converter_list = page.get("converter_list") or []
            for converter in converter_list:
                converter_id = str(converter.get("id") or "").strip()
                converter_name = str(converter.get("name") or "").strip()
                if converter_id == slug or converter_id.replace("-", "") == slug.replace("-", "") or converter_name.lower() == slug.replace("-", " ").lower():
                    return True
        return False

    def _score_checks(self, checks: dict[str, Any]) -> int:
        total = 10
        score = 0
        for key in [
            "converter_contract",
            "landing_contract",
            "knowledge_payload",
            "authority_payload",
            "encyclopedia_page",
            "faq_coverage",
            "internal_links",
            "related_converters",
            "sitemap_inclusion",
            "hub_inclusion",
        ]:
            if checks.get(key):
                score += 1
        return int(round((score / total) * 100))

    def _derive_status(self, quality_score: int) -> str:
        if quality_score >= 90:
            return "READY"
        if quality_score >= 70:
            return "WARNING"
        return "NOT READY"
