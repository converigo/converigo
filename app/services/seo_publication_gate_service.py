"""SEO publication gate - determine publish-ready SEO pages independently of deployment health."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.content_quality_service import ContentQualityService
from app.services.programmatic_seo_engine import ProgrammaticSeoEngine


class SeoPublicationGateService:
    """Determine individual SEO page readiness for publication."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.seo_engine = ProgrammaticSeoEngine(self.contracts_dir)
        self.content_quality_service = ContentQualityService(self.contracts_dir)

    def evaluate_page(self, format_name: str, page_type: str) -> dict[str, Any]:
        """Evaluate a single page against publication readiness criteria."""
        format_lower = str(format_name).lower()
        page = {}
        quality_eval = {}

        try:
            page = self.seo_engine.generate_page(format_lower, page_type)
        except Exception as exc:
            return {
                "format": format_lower,
                "page_type": page_type,
                "publication_status": "NOT_READY",
                "page_classification": "REJECTED",
                "quality_decision": "REJECT",
                "quality_score": 0,
                "issues": [f"Page generation failed: {exc}"],
            }

        try:
            quality_eval = self.content_quality_service.evaluate_page(format_lower, page_type)
        except Exception as exc:
            quality_eval = {
                "decision": "REJECT",
                "quality_score": 0,
                "metrics": {},
            }

        cqe_pass = str(quality_eval.get("decision", "REJECT")).upper() == "PASS"
        schema_pass = self._check_schema(page)
        faq_pass = self._check_faq(page)
        metadata_pass = self._check_metadata(page)
        canonical_pass = self._check_canonical(page)
        internal_links_pass = self._check_internal_links(page)
        comparison_pass = self._check_comparison(page)
        topic_cluster_pass = self._check_topic_cluster(page)

        checks = {
            "cqe_pass": cqe_pass,
            "schema_pass": schema_pass,
            "faq_pass": faq_pass,
            "metadata_pass": metadata_pass,
            "canonical_pass": canonical_pass,
            "internal_links_pass": internal_links_pass,
            "comparison_pass": comparison_pass,
            "topic_cluster_pass": topic_cluster_pass,
        }

        critical_failures = [key for key, passed in checks.items() if not passed and key in {
            "cqe_pass",
            "schema_pass",
            "faq_pass",
            "metadata_pass",
            "canonical_pass",
        }]
        draft_failures = [key for key, passed in checks.items() if not passed and key in {
            "internal_links_pass",
            "comparison_pass",
            "topic_cluster_pass",
        }]

        if not critical_failures and not draft_failures:
            publication_status = "READY"
            page_classification = "READY"
        elif critical_failures:
            publication_status = "NOT_READY"
            page_classification = "REJECTED"
        else:
            publication_status = "NOT_READY"
            page_classification = "DRAFT"

        issues = []
        if not cqe_pass:
            issues.append("Content quality engine did not pass.")
        if not schema_pass:
            issues.append("Schema requirements not met.")
        if not faq_pass:
            issues.append("FAQ content is missing or incomplete.")
        if not metadata_pass:
            issues.append("SEO metadata is incomplete.")
        if not canonical_pass:
            issues.append("Canonical URL is missing or invalid.")
        if not internal_links_pass:
            issues.append("Internal links are insufficient.")
        if not comparison_pass:
            issues.append("Comparison/related converter references are incomplete.")
        if not topic_cluster_pass:
            issues.append("Topic cluster integration is incomplete.")

        return {
            "format": format_lower,
            "page_type": page_type,
            "publication_status": publication_status,
            "page_classification": page_classification,
            "quality_decision": quality_eval.get("decision", "REJECT"),
            "quality_score": quality_eval.get("quality_score", 0),
            "checks": checks,
            "issues": issues,
            "page_url": page.get("url", f"/{page_type}/{format_lower}"),
        }

    def evaluate_all_pages(self) -> dict[str, Any]:
        """Evaluate every generated SEO page and aggregate publication readiness."""
        formats = self.seo_engine._collect_all_formats()
        page_types = self.seo_engine.PAGE_TYPES
        results: list[dict[str, Any]] = []

        for fmt in formats:
            for page_type in page_types:
                results.append(self.evaluate_page(fmt, page_type))

        total_pages = len(results)
        ready_pages = sum(1 for page in results if page["publication_status"] == "READY")
        rejected_pages = sum(1 for page in results if page["page_classification"] == "REJECTED")
        draft_pages = sum(1 for page in results if page["page_classification"] == "DRAFT")

        ready_percentage = round((ready_pages / total_pages * 100), 2) if total_pages else 0.0
        draft_percentage = round((draft_pages / total_pages * 100), 2) if total_pages else 0.0
        rejected_percentage = round((rejected_pages / total_pages * 100), 2) if total_pages else 0.0

        return {
            "total_pages_evaluated": total_pages,
            "ready_pages": ready_pages,
            "draft_pages": draft_pages,
            "rejected_pages": rejected_pages,
            "ready_percentage": ready_percentage,
            "draft_percentage": draft_percentage,
            "rejected_percentage": rejected_percentage,
            "results": results,
        }

    def _check_schema(self, page: dict[str, Any]) -> bool:
        seo = page.get("seo") or {}
        json_ld = page.get("json_ld")
        breadcrumb = page.get("breadcrumb")
        return bool(json_ld and breadcrumb and seo.get("title") and seo.get("meta_description"))

    def _check_faq(self, page: dict[str, Any]) -> bool:
        faq_items = page.get("content", {}).get("faq") or page.get("faq")
        if isinstance(faq_items, list):
            return len([item for item in faq_items if item]) > 0
        return False

    def _check_metadata(self, page: dict[str, Any]) -> bool:
        seo = page.get("seo") or {}
        return bool(
            seo.get("title") and
            seo.get("meta_description") and
            isinstance(seo.get("keywords"), list) and
            len(seo.get("keywords", [])) > 0
        )

    def _check_canonical(self, page: dict[str, Any]) -> bool:
        seo = page.get("seo") or {}
        canonical = str(seo.get("canonical", "")).strip()
        return bool(canonical)

    def _check_internal_links(self, page: dict[str, Any]) -> bool:
        links = page.get("internal_links")
        if not isinstance(links, dict):
            return False
        total_links = sum(
            len(items) for items in links.values() if isinstance(items, list)
        )
        return total_links >= 1

    def _check_comparison(self, page: dict[str, Any]) -> bool:
        related_converters = page.get("related_converters")
        if isinstance(related_converters, list) and len(related_converters) > 0:
            return True
        return False

    def _check_topic_cluster(self, page: dict[str, Any]) -> bool:
        related_topics = page.get("related_topics")
        if isinstance(related_topics, list) and len(related_topics) > 0:
            return True
        return False
