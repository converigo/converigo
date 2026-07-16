from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING

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
from app.services.internal_link_service import InternalLinkService
from app.services.topic_cluster_service import TopicClusterService
from app.services.programmatic_seo_engine import ProgrammaticSeoEngine

if TYPE_CHECKING:
    from app.services.content_quality_service import ContentQualityService


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
        self.internal_link_service = InternalLinkService(self.contracts_dir)
        self.topic_cluster_service = TopicClusterService(self.contracts_dir)
        self.seo_engine = ProgrammaticSeoEngine(self.contracts_dir)
        self._content_quality_service: ContentQualityService | None = None
        self._register_active_contracts()

    @property
    def content_quality_service(self) -> ContentQualityService:
        """Lazy load ContentQualityService to avoid circular imports."""
        if self._content_quality_service is None:
            # Import here to avoid circular import at module load time
            from app.services.content_quality_service import ContentQualityService as CQS
            self._content_quality_service = CQS(self.contracts_dir)
        return self._content_quality_service

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
            "topic_cluster_complete": False,
            "topic_cluster_links": False,
            "topic_cluster_quality": False,
            "seo_structure": False,
            "seo_metadata": False,
            "seo_internal_links": False,
            "seo_content_quality": False,
            "content_quality": False,
            "content_uniqueness": False,
            "content_density": False,
            "content_eligibility": False,
            "content_search_intent": False,
            "content_schema_quality": False,
            "duplicate_detection": False,
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

            # Check internal links using the comprehensive InternalLinkService
            try:
                internal_links = self.internal_link_service.get_links_for_landing(slug, contract)
                links_total = sum(len(items) for items in internal_links.values() if isinstance(items, list))
                checks["internal_links"] = links_total >= 3
            except Exception:
                checks["internal_links"] = bool(landing and landing.get("internal_links", {}).get("items")) if landing else False


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

        # Check topic cluster completeness
        try:
            input_formats = contract.get("input_formats", [])
            output_formats = contract.get("output_formats", [])
            formats_to_check = list(set(input_formats + output_formats))
            
            if formats_to_check:
                primary_format = str(formats_to_check[0]).lower()
                cluster = self.topic_cluster_service.build_cluster(primary_format)
                
                # Check if cluster is complete (has all 17 sections)
                sections = [
                    "knowledge", "faq", "mime", "file_extensions", "metadata",
                    "specification", "history", "security", "compression",
                    "accessibility", "software", "tutorials", "best_practices",
                    "comparisons", "related_formats", "related_converters", "hub"
                ]
                
                checks["topic_cluster_complete"] = all(section in cluster and cluster[section] for section in sections)
                checks["topic_cluster_links"] = bool(cluster.get("internal_links", {}).get("related_converters", []))
                checks["topic_cluster_quality"] = bool(cluster.get("knowledge", {}).get("overview")) and checks["topic_cluster_links"]
        except Exception:
            checks["topic_cluster_complete"] = False
            checks["topic_cluster_links"] = False
            checks["topic_cluster_quality"] = False

        # Check SEO pages for format
        try:
            input_formats = contract.get("input_formats", [])
            output_formats = contract.get("output_formats", [])
            formats_to_check = list(set(input_formats + output_formats))
            
            if formats_to_check:
                primary_format = str(formats_to_check[0]).lower()
                seo_pages_generated = 0
                
                # Check if SEO pages can be generated for this format
                for page_type in self.seo_engine.PAGE_TYPES:
                    try:
                        page = self.seo_engine.generate_page(primary_format, page_type)
                        if page:
                            seo_pages_generated += 1
                    except Exception:
                        continue
                
                # Check SEO structure (title, meta_description, canonical)
                if seo_pages_generated > 0:
                    sample_page = self.seo_engine.generate_page(primary_format, "how_to")
                    seo_data = sample_page.get("seo", {})
                    checks["seo_structure"] = bool(
                        seo_data.get("title") and 
                        seo_data.get("meta_description") and 
                        seo_data.get("canonical")
                    )
                    checks["seo_metadata"] = bool(seo_data.get("keywords", []))
                    checks["seo_internal_links"] = bool(sample_page.get("internal_links"))
                    checks["seo_content_quality"] = bool(
                        sample_page.get("content") and 
                        sample_page.get("json_ld") and
                        seo_pages_generated >= 5
                    )
        except Exception:
            checks["seo_structure"] = False
            checks["seo_metadata"] = False
            checks["seo_internal_links"] = False
            checks["seo_content_quality"] = False

        # Check content quality for all page types
        try:
            input_formats = contract.get("input_formats", [])
            if input_formats:
                primary_format = str(input_formats[0]).lower()
                
                # Evaluate quality for multiple page types
                quality_scores = []
                quality_decisions = {"PASS": 0, "NEEDS_REVIEW": 0, "NO_INDEX": 0, "REJECT": 0}
                
                for page_type in self.seo_engine.PAGE_TYPES[:3]:  # Sample 3 page types
                    try:
                        quality_eval = self.content_quality_service.evaluate_page(primary_format, page_type)
                        score = quality_eval.get("quality_score", 0)
                        decision = quality_eval.get("decision", "REJECT")
                        quality_scores.append(score)
                        quality_decisions[decision] = quality_decisions.get(decision, 0) + 1
                        
                        # Check individual metrics
                        metrics = quality_eval.get("metrics", {})
                        checks["content_uniqueness"] = max(checks.get("content_uniqueness", False), metrics.get("uniqueness_score", 0) >= 70)
                        checks["content_density"] = max(checks.get("content_density", False), metrics.get("data_density_score", 0) >= 60)
                        checks["content_eligibility"] = max(checks.get("content_eligibility", False), metrics.get("eligibility_score", 0) >= 80)
                        checks["content_search_intent"] = max(checks.get("content_search_intent", False), metrics.get("search_intent_score", 0) >= 70)
                        checks["content_schema_quality"] = max(checks.get("content_schema_quality", False), metrics.get("schema_score", 0) >= 80)
                        checks["duplicate_detection"] = max(checks.get("duplicate_detection", False), metrics.get("duplicate_score", 0) >= 80)
                    except Exception:
                        continue
                
                # Overall content quality check
                if quality_scores:
                    avg_quality = sum(quality_scores) / len(quality_scores)
                    checks["content_quality"] = avg_quality >= 80
        except Exception:
            checks["content_quality"] = False
            checks["content_uniqueness"] = False
            checks["content_density"] = False
            checks["content_eligibility"] = False
            checks["content_search_intent"] = False
            checks["content_schema_quality"] = False
            checks["duplicate_detection"] = False

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
        total = 17
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
            "topic_cluster_complete",
            "topic_cluster_links",
            "topic_cluster_quality",
            "seo_structure",
            "seo_metadata",
            "seo_internal_links",
            "seo_content_quality",
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

    def get_internal_linking_report(self) -> dict[str, Any]:
        """Get comprehensive internal linking coverage report."""
        return self.internal_link_service.build_internal_link_coverage_report()

    def get_topic_cluster_report(self) -> dict[str, Any]:
        """Get comprehensive topic cluster coverage report."""
        return self.topic_cluster_service.build_cluster_coverage_report()

    def get_seo_pages_report(self) -> dict[str, Any]:
        """Get comprehensive SEO pages coverage report."""
        return self.seo_engine.get_seo_page_coverage_report()
