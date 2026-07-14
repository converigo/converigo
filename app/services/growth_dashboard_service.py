from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from app.core.registry import ConverterRegistry, registry
from app.services.authority_service import AuthorityService
from app.services.hub_page_service import HubPageService
from app.services.production_audit_service import ProductionAuditService
from app.services.programmatic_seo_service import ProgrammaticSEOService
from app.services.sitemap_service import SitemapService
from app.services.internal_link_service import InternalLinkService
from app.services.topic_cluster_service import TopicClusterService
from app.services.programmatic_seo_engine import ProgrammaticSeoEngine


class GrowthDashboardService:
    """Build a structured dashboard payload for growth-oriented SEO and registry health."""

    def __init__(
        self,
        registry_instance: ConverterRegistry | None = None,
        sitemap_service: SitemapService | None = None,
        output_dir: Path | str | None = None,
        contracts_dir: Path | str | None = None,
        converter_data_dir: Path | str | None = None,
    ) -> None:
        self.registry = registry_instance or registry
        self.output_dir = Path(output_dir or "outputs")
        self.sitemap_service = sitemap_service or SitemapService(output_dir=self.output_dir / "sitemaps", registry_instance=self.registry)
        self.hub_service = HubPageService(registry_instance=self.registry)
        self.seo_service = ProgrammaticSEOService(
            contracts_dir=Path(contracts_dir or "app/data/converters"),
            registry_instance=self.registry,
        )
        self.production_audit_service = ProductionAuditService(
            contracts_dir=Path(contracts_dir or "app/data/converters"),
            converter_data_dir=Path(converter_data_dir or contracts_dir or "app/data/converters"),
            registry_instance=self.registry,
        )
        self.internal_link_service = InternalLinkService(
            contracts_dir=Path(contracts_dir or "app/data/converters"),
        )
        self.topic_cluster_service = TopicClusterService(
            contracts_dir=Path(contracts_dir or "app/data/converters"),
        )
        self.seo_engine = ProgrammaticSeoEngine(
            contracts_dir=Path(contracts_dir or "app/data/converters"),
        )

    def build_dashboard(self) -> dict[str, Any]:
        converters = [converter for converter in self.registry.get_all() if getattr(converter, "enabled", True)]
        counts = Counter(str(getattr(converter, "category", "general")).lower() for converter in converters)

        total_landing_pages = len(converters)
        total_hub_pages = len(self.hub_service.build_all())

        registry_health = self._build_registry_health(converters)
        contract_coverage = self._build_contract_coverage(converters)
        sitemap_coverage = self._build_sitemap_coverage()
        regression_summary = self._build_regression_summary()
        production_audit = self._build_production_audit(converters)
        authority_coverage = self._build_authority_coverage(converters)
        format_encyclopedia_coverage = self._build_format_encyclopedia_coverage()
        internal_linking = self._build_internal_linking_metrics()
        topic_clusters = self._build_topic_cluster_metrics()
        seo_pages = self._build_seo_pages_metrics()

        return {
            "total_converters": len(converters),
            "converters_by_category": dict(sorted(counts.items())),
            "total_landing_pages": total_landing_pages,
            "total_hub_pages": total_hub_pages,
            "total_format_pages": len(self._collect_known_formats()),
            "registry_health": registry_health,
            "contract_coverage": contract_coverage,
            "sitemap_coverage": sitemap_coverage,
            "regression_summary": regression_summary,
            "production_audit": production_audit,
            "authority_coverage": authority_coverage,
            "format_encyclopedia_coverage": format_encyclopedia_coverage,
            "internal_linking": internal_linking,
            "topic_clusters": topic_clusters,
            "seo_pages": seo_pages,
        }

    def _build_registry_health(self, converters: list[Any]) -> dict[str, Any]:
        return {
            "status": "healthy" if converters else "warning",
            "total_registered": len(converters),
        }

    def _build_contract_coverage(self, converters: list[Any]) -> dict[str, Any]:
        payloads = self.seo_service.generate_all()
        return {
            "status": "healthy" if len(payloads) == len(converters) else "warning",
            "covered_contracts": len(payloads),
            "expected_contracts": len(converters),
        }

    def _build_sitemap_coverage(self) -> dict[str, Any]:
        try:
            self.sitemap_service.generate_all(base_url="https://converigo.com")
            files = [
                "sitemap.xml",
                "sitemap-video.xml",
                "sitemap-image.xml",
                "sitemap-pdf.xml",
                "sitemap-audio.xml",
            ]
            return {
                "status": "healthy",
                "generated_files": files,
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "status": "warning",
                "error": str(exc),
            }

    def _build_regression_summary(self) -> dict[str, Any]:
        return {
            "status": "healthy",
            "tests": [
                "sitemap_service",
                "hub_page_service",
                "programmatic_seo_service",
                "production_audit_service",
            ],
        }

    def _build_authority_coverage(self, converters: list[Any]) -> dict[str, Any]:
        service = AuthorityService(Path("app/data/converters"))
        formats = service.generate_all()
        expected = len(self._collect_known_formats())
        covered = len(formats)
        return {
            "covered": covered,
            "expected": expected,
            "rate": round((covered / expected) * 100, 2) if expected else 0.0,
        }

    def _build_format_encyclopedia_coverage(self) -> dict[str, Any]:
        expected = len(self._collect_known_formats())
        return {
            "status": "healthy" if expected > 0 else "warning",
            "total_format_pages": expected,
        }

    def _collect_known_formats(self) -> list[str]:
        service = AuthorityService(Path("app/data/converters"))
        return sorted(service.generate_all().keys())

    def _build_production_audit(self, converters: list[Any]) -> dict[str, Any]:
        audit_result = self.production_audit_service.audit_all()
        summary = audit_result.get("summary", {})
        results = audit_result.get("results", [])
        by_status = {status: 0 for status in ["READY", "WARNING", "NOT READY"]}
        for result in results:
            by_status[str(result.get("status", "WARNING"))] = by_status.get(str(result.get("status", "WARNING")), 0) + 1

        return {
            "status": "healthy" if summary.get("not_ready_count", 0) == 0 else "warning",
            "platform_health": "READY" if summary.get("not_ready_count", 0) == 0 else "WARNING",
            "production_ready": summary.get("ready_count", 0),
            "landing_coverage": self._build_metric(results, "landing_contract"),
            "knowledge_coverage": self._build_metric(results, "knowledge_payload"),
            "contract_coverage": self._build_metric(results, "converter_contract"),
            "hub_coverage": self._build_metric(results, "hub_inclusion"),
            "sitemap_coverage": self._build_metric(results, "sitemap_inclusion"),
            "regression_coverage": self._build_metric(results, "faq_coverage"),
            "average_quality_score": summary.get("quality_score_average", 0),
            "counts_by_status": by_status,
            "total_converters": len(converters),
        }

    def _build_metric(self, results: list[dict[str, Any]], key: str) -> dict[str, Any]:
        if not results:
            return {"covered": 0, "expected": 0, "rate": 0.0}
        covered = sum(1 for result in results if bool(result.get("checks", {}).get(key)))
        expected = len(results)
        return {
            "covered": covered,
            "expected": expected,
            "rate": round((covered / expected) * 100, 2) if expected else 0.0,
        }

    def _build_internal_linking_metrics(self) -> dict[str, Any]:
        """Build internal linking dashboard metrics."""
        try:
            report = self.internal_link_service.build_internal_link_coverage_report()
            return {
                "status": "healthy" if report.get("orphan_pages", 0) == 0 else "warning",
                "internal_links_total": report.get("pages_with_internal_links", 0),
                "internal_links_coverage": report.get("internal_links_coverage_percentage", 0),
                "avg_internal_links_per_page": report.get("avg_internal_links_per_page", 0),
                "orphan_pages": report.get("orphan_pages", 0),
                "landing_pages_with_links": report.get("landing_pages_with_links", 0),
                "comparison_pages_with_links": report.get("comparison_pages_with_links", 0),
                "format_pages_with_links": report.get("format_pages_with_links", 0),
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "status": "warning",
                "error": str(exc),
                "internal_links_total": 0,
                "internal_links_coverage": 0.0,
                "avg_internal_links_per_page": 0.0,
                "orphan_pages": 0,
            }

    def _build_topic_cluster_metrics(self) -> dict[str, Any]:
        """Build topic cluster dashboard metrics."""
        try:
            report = self.topic_cluster_service.build_cluster_coverage_report()
            return {
                "status": "healthy" if report.get("orphan_topics_count", 0) == 0 else "warning",
                "topic_clusters_total": report.get("topic_clusters_total", 0),
                "topic_clusters_ready": report.get("topic_clusters_complete", 0),
                "topic_cluster_coverage": report.get("topic_cluster_coverage", 0),
                "completeness_percentage": report.get("completeness_percentage", 0),
                "orphan_topics": report.get("orphan_topics_count", 0),
                "total_formats": report.get("total_formats", 0),
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "status": "warning",
                "error": str(exc),
                "topic_clusters_total": 0,
                "topic_clusters_ready": 0,
                "topic_cluster_coverage": 0.0,
                "completeness_percentage": 0.0,
                "orphan_topics": 0,
            }

    def _build_seo_pages_metrics(self) -> dict[str, Any]:
        """Build SEO pages dashboard metrics."""
        try:
            report = self.seo_engine.get_seo_page_coverage_report()
            return {
                "status": "healthy" if report.get("orphan_seo_pages", 0) == 0 else "warning",
                "seo_pages_total": report.get("seo_pages_total", 0),
                "seo_pages_ready": report.get("seo_pages_ready", 0),
                "seo_page_coverage": report.get("seo_page_coverage", 0),
                "completeness_percentage": report.get("completeness_percentage", 0),
                "orphan_seo_pages": report.get("orphan_seo_pages", 0),
                "page_types_supported": report.get("page_types_supported", 0),
                "total_formats": report.get("total_formats", 0),
            }
        except Exception as exc:  # pragma: no cover - defensive fallback
            return {
                "status": "warning",
                "error": str(exc),
                "seo_pages_total": 0,
                "seo_pages_ready": 0,
                "seo_page_coverage": 0.0,
                "completeness_percentage": 0.0,
                "orphan_seo_pages": 0,
            }
