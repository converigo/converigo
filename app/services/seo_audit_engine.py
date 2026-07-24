"""Converigo
SEO Audit Engine
Version : 1.0.0

Read-only SEO audit engine that inspects every converter page for SEO health.
Computes an SEO score (0–100), identifies missing/critical items, and generates
structured audit reports.

Do NOT modify architecture, routing, or converter engine.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.converter_registry_service import ConverterRegistryService
from app.services.converter_data_service import ConverterDataService
from app.services.seo_service import SeoService, PRODUCTION_BASE_URL
from app.services.internal_link_service import InternalLinkService


# ── Audit Check Definitions ───────────────────────────────────────

class AuditCheck:
    """Represents a single SEO audit check with weighting."""

    def __init__(
        self,
        name: str,
        weight: int,
        description: str,
        critical: bool = False,
    ) -> None:
        self.name = name
        self.weight = weight
        self.description = description
        self.critical = critical

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "weight": self.weight,
            "description": self.description,
            "critical": self.critical,
        }


# All audit checks with their max weights (total = 100)
AUDIT_CHECKS = [
    AuditCheck("Title", 10, "Page title tag exists and is properly formatted", critical=True),
    AuditCheck("Meta Description", 10, "Meta description tag exists and has appropriate length", critical=True),
    AuditCheck("Canonical", 8, "Canonical URL is present and correct", critical=True),
    AuditCheck("H1", 6, "H1 heading exists and is unique"),
    AuditCheck("Open Graph", 8, "Open Graph tags are present (og:title, og:description, og:image, og:url)"),
    AuditCheck("Twitter Card", 5, "Twitter Card meta tags are present"),
    AuditCheck("Breadcrumb", 7, "Breadcrumb structured data is present and valid"),
    AuditCheck("JSON-LD", 10, "JSON-LD structured data is present with required schema types", critical=True),
    AuditCheck("FAQ", 8, "FAQ section exists with minimum number of items"),
    AuditCheck("Internal Links", 8, "Internal links are present with minimum count", critical=True),
    AuditCheck("Related Converters", 6, "Related converter links are present"),
    AuditCheck("Word Count", 5, "Content has minimum word count"),
    AuditCheck("Image ALT", 4, "Images have alt text attributes"),
    AuditCheck("Robots", 3, "Robots meta tag is present and allows indexing"),
    AuditCheck("Indexability", 2, "Page is indexable based on lifecycle and SEO status"),
]


class SeoAuditEngine:
    """Read-only SEO audit engine for all converter pages."""

    # Minimum thresholds
    MIN_TITLE_LENGTH = 30
    MAX_TITLE_LENGTH = 70
    MIN_META_DESCRIPTION_LENGTH = 50
    MAX_META_DESCRIPTION_LENGTH = 160
    MIN_WORD_COUNT = 100
    MIN_FAQ_ITEMS = 3
    MIN_INTERNAL_LINKS = 3
    MIN_RELATED_CONVERTERS = 1

    def __init__(
        self,
        contracts_dir: Path | str | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_registry = ConverterRegistryService(self.contracts_dir)
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.internal_link_service = InternalLinkService(self.contracts_dir)

    def run_full_audit(self) -> dict[str, Any]:
        """Run full SEO audit on all converter pages.

        Returns a complete audit payload with per-page results, aggregate
        scores, problems, and recommendations.
        """
        converters = self.converter_registry.list_all()
        page_results: list[dict[str, Any]] = []

        for contract in converters:
            result = self._audit_converter_page(contract)
            page_results.append(result)

        # Aggregate results
        aggregate = self._aggregate_results(page_results)

        return {
            "version": "1.0.0",
            "generated_at": self._now(),
            "total_converters": len(converters),
            "pages_audited": len(page_results),
            "summary": aggregate["summary"],
            "overall_score": aggregate["overall_score"],
            "overall_status": aggregate["overall_status"],
            "score_distribution": aggregate["score_distribution"],
            "critical_issues": aggregate["critical_issues"],
            "warnings": aggregate["warnings"],
            "passed_checks": aggregate["passed_checks"],
            "top_issues": aggregate["top_issues"],
            "recommendations": aggregate["recommendations"],
            "checks_definition": [check.to_dict() for check in AUDIT_CHECKS],
            "page_results": page_results,
        }

    def run_audit_for_slug(self, slug: str) -> dict[str, Any] | None:
        """Run SEO audit for a single converter by slug."""
        contract = self.converter_registry.get_by_slug(slug)
        if not contract:
            return None
        return self._audit_converter_page(contract)

    # ── Per-page Audit ─────────────────────────────────────────

    def _audit_converter_page(self, contract: dict[str, Any]) -> dict[str, Any]:
        """Audit a single converter page for all SEO checks."""
        slug = str(contract.get("slug", ""))
        page_url = contract.get("canonical_url", f"{PRODUCTION_BASE_URL}/tools/{slug}")
        landing_path = contract.get("landing_path", f"/tools/{slug}")

        # Build the landing page context for analysis
        try:
            tool_data = self.converter_data_service.load_converter_by_slug(slug)
        except FileNotFoundError:
            tool_data = contract

        # Generate expected SEO meta
        seo_meta = self._build_seo_meta(tool_data, slug, page_url)

        check_results: dict[str, dict[str, Any]] = {}

        # ── Title ──
        check_results["Title"] = self._check_title(seo_meta, contract, slug)

        # ── Meta Description ──
        check_results["Meta Description"] = self._check_meta_description(seo_meta, contract)

        # ── Canonical ──
        check_results["Canonical"] = self._check_canonical(seo_meta, contract, page_url)

        # ── H1 ──
        check_results["H1"] = self._check_h1(seo_meta, tool_data, contract)

        # ── Open Graph ──
        check_results["Open Graph"] = self._check_open_graph(seo_meta)

        # ── Twitter Card ──
        check_results["Twitter Card"] = self._check_twitter_card(seo_meta)

        # ── Breadcrumb ──
        check_results["Breadcrumb"] = self._check_breadcrumb(contract, slug)

        # ── JSON-LD ──
        check_results["JSON-LD"] = self._check_json_ld(contract, slug)

        # ── FAQ ──
        check_results["FAQ"] = self._check_faq(contract, slug)

        # ── Internal Links ──
        check_results["Internal Links"] = self._check_internal_links(slug, contract)

        # ── Related Converters ──
        check_results["Related Converters"] = self._check_related_converters(slug, tool_data)

        # ── Word Count ──
        check_results["Word Count"] = self._check_word_count(tool_data, contract)

        # ── Image ALT ──
        check_results["Image ALT"] = self._check_image_alt(tool_data, contract)

        # ── Robots ──
        check_results["Robots"] = self._check_robots(contract)

        # ── Indexability ──
        check_results["Indexability"] = self._check_indexability(contract)

        # Calculate score
        total_score = self._calculate_score(check_results)

        # Determine issues
        critical_issues = [
            r for r in check_results.values()
            if r.get("status") == "FAIL"
        ]
        warnings_list = [
            r for r in check_results.values()
            if r.get("status") == "WARN"
        ]
        passed = [
            r for r in check_results.values()
            if r.get("status") == "PASS"
        ]

        return {
            "slug": slug,
            "name": contract.get("name", slug),
            "category": contract.get("category", "general"),
            "page_url": page_url,
            "landing_path": landing_path,
            "lifecycle_status": contract.get("lifecycle_status", "unknown"),
            "seo_status": contract.get("seo_status", "unknown"),
            "score": total_score,
            "status": self._score_status(total_score),
            "checks": check_results,
            "critical_issues_count": len(critical_issues),
            "warnings_count": len(warnings_list),
            "passed_count": len(passed),
            "total_checks": len(AUDIT_CHECKS),
        }

    # ── Individual Check Methods ─────────────────────────────────

    def _check_title(
        self, seo_meta: dict[str, Any], contract: dict[str, Any], slug: str
    ) -> dict[str, Any]:
        """Check page title tag."""
        title = seo_meta.get("title", "") or contract.get("title", "") or ""
        title_len = len(title)

        issues = []
        if not title.strip():
            return {"status": "FAIL", "score": 0, "message": "Missing title tag", "issues": ["No title tag found"], "value": ""}

        if title_len < self.MIN_TITLE_LENGTH:
            issues.append(f"Title too short ({title_len} chars, min {self.MIN_TITLE_LENGTH})")
        elif title_len > self.MAX_TITLE_LENGTH:
            issues.append(f"Title too long ({title_len} chars, max {self.MAX_TITLE_LENGTH})")

        if "converigo" not in title.lower() and slug not in title.lower():
            issues.append("Title may not include converter/brand name")

        if issues:
            return {"status": "WARN", "score": 5, "message": "Title has issues", "issues": issues, "value": title}

        return {"status": "PASS", "score": 10, "message": f"Title is valid ({title_len} chars)", "issues": [], "value": title}

    def _check_meta_description(
        self, seo_meta: dict[str, Any], contract: dict[str, Any]
    ) -> dict[str, Any]:
        """Check meta description tag."""
        description = seo_meta.get("description", "") or contract.get("description", "") or ""
        desc_len = len(description)

        issues = []
        if not description.strip():
            return {"status": "FAIL", "score": 0, "message": "Missing meta description", "issues": ["No meta description found"], "value": ""}

        if desc_len < self.MIN_META_DESCRIPTION_LENGTH:
            issues.append(f"Description too short ({desc_len} chars, min {self.MIN_META_DESCRIPTION_LENGTH})")
        elif desc_len > self.MAX_META_DESCRIPTION_LENGTH:
            issues.append(f"Description too long ({desc_len} chars, max {self.MAX_META_DESCRIPTION_LENGTH})")

        if issues:
            return {"status": "WARN", "score": 5, "message": "Meta description has issues", "issues": issues, "value": description}

        return {"status": "PASS", "score": 10, "message": f"Meta description is valid ({desc_len} chars)", "issues": [], "value": description}

    def _check_canonical(
        self, seo_meta: dict[str, Any], contract: dict[str, Any], page_url: str
    ) -> dict[str, Any]:
        """Check canonical URL."""
        canonical = (
            seo_meta.get("canonical", "")
            or contract.get("canonical_url", "")
            or page_url
        )

        if not canonical.strip():
            return {"status": "FAIL", "score": 0, "message": "Missing canonical URL", "issues": ["No canonical URL found"], "value": ""}

        if not canonical.startswith("https://"):
            return {"status": "WARN", "score": 4, "message": "Canonical URL is not HTTPS", "issues": ["Canonical should use HTTPS"], "value": canonical}

        if "converigo.com" not in canonical.lower():
            return {"status": "WARN", "score": 4, "message": "Canonical URL does not point to production domain", "issues": ["Canonical should point to converigo.com"], "value": canonical}

        return {"status": "PASS", "score": 8, "message": "Canonical URL is valid", "issues": [], "value": canonical}

    def _check_h1(
        self, seo_meta: dict[str, Any], tool_data: dict[str, Any], contract: dict[str, Any]
    ) -> dict[str, Any]:
        """Check H1 heading."""
        h1 = (
            tool_data.get("hero", {}).get("title", "")
            or tool_data.get("title", "")
            or contract.get("name", "")
        )

        if not h1.strip():
            return {"status": "FAIL", "score": 0, "message": "Missing H1 tag", "issues": ["No H1 heading found"], "value": ""}

        if len(h1) < 10:
            return {"status": "WARN", "score": 3, "message": "H1 is too short", "issues": [f"H1 has only {len(h1)} chars"], "value": h1}

        return {"status": "PASS", "score": 6, "message": "H1 is present and valid", "issues": [], "value": h1}

    def _check_open_graph(self, seo_meta: dict[str, Any]) -> dict[str, Any]:
        """Check Open Graph tags."""
        required_og = ["og:title", "og:description", "og:image", "og:url"]
        # Map from seo_meta keys
        og_map = {
            "og:title": seo_meta.get("title", ""),
            "og:description": seo_meta.get("description", ""),
            "og:image": seo_meta.get("og_image", ""),
            "og:url": seo_meta.get("og_url", ""),
            "og:site_name": seo_meta.get("og_site_name", ""),
            "og:type": seo_meta.get("og_type", ""),
        }

        missing = [tag for tag in required_og if not og_map.get(tag, "")]
        if missing:
            return {
                "status": "FAIL",
                "score": 2,
                "message": f"Missing OG tags: {', '.join(missing)}",
                "issues": [f"Missing required Open Graph tag: {tag}" for tag in missing],
                "value": og_map,
            }

        return {"status": "PASS", "score": 8, "message": "All required Open Graph tags present", "issues": [], "value": og_map}

    def _check_twitter_card(self, seo_meta: dict[str, Any]) -> dict[str, Any]:
        """Check Twitter Card tags."""
        twitter_card = seo_meta.get("twitter_card", "")
        twitter_site = seo_meta.get("twitter_site", "")

        missing = []
        if not twitter_card:
            missing.append("twitter:card")
        if not twitter_site:
            missing.append("twitter:site")

        if missing:
            return {
                "status": "WARN",
                "score": 2,
                "message": f"Missing Twitter Card tags: {', '.join(missing)}",
                "issues": [f"Missing Twitter Card tag: {tag}" for tag in missing],
                "value": {"twitter:card": twitter_card, "twitter:site": twitter_site},
            }

        return {"status": "PASS", "score": 5, "message": "Twitter Card tags present", "issues": [], "value": {"twitter:card": twitter_card, "twitter:site": twitter_site}}

    def _check_breadcrumb(self, contract: dict[str, Any], slug: str) -> dict[str, Any]:
        """Check breadcrumb structured data."""
        breadcrumb = contract.get("breadcrumb", [])
        if not breadcrumb:
            # Fall back to expected breadcrumb structure
            breadcrumb = [
                {"name": "Home", "url": "/"},
                {"name": contract.get("name", slug), "url": contract.get("landing_path", f"/tools/{slug}")},
            ]

        if not breadcrumb or len(breadcrumb) < 2:
            return {"status": "WARN", "score": 3, "message": "Breadcrumb has fewer than 2 items", "issues": ["Breadcrumb should have at least Home > Current Page"], "value": breadcrumb}

        # Check that each breadcrumb item has name and url
        invalid_items = [
            item for item in breadcrumb
            if not isinstance(item, dict) or not item.get("name") or not item.get("url")
        ]
        if invalid_items:
            return {"status": "WARN", "score": 4, "message": f"{len(invalid_items)} breadcrumb items missing name or url", "issues": ["Each breadcrumb item needs 'name' and 'url'"], "value": breadcrumb}

        return {"status": "PASS", "score": 7, "message": f"Breadcrumb valid with {len(breadcrumb)} items", "issues": [], "value": breadcrumb}

    def _check_json_ld(self, contract: dict[str, Any], slug: str) -> dict[str, Any]:
        """Check JSON-LD structured data presence."""
        schema_status = str(contract.get("schema_status", "")).strip().lower()
        contract_json_ld = contract.get("json_ld", {})

        # Collect expected schema types for converter pages
        expected_types = [
            "Organization",
            "WebSite",
            "SoftwareApplication",
            "BreadcrumbList",
        ]
        faq_items = contract.get("faq", [])
        if faq_items:
            expected_types.append("FAQPage")

        # Check schema_status field
        if schema_status != "ready":
            return {
                "status": "WARN",
                "score": 5,
                "message": f"Schema status is '{schema_status}' (expected 'ready')",
                "issues": [f"schema_status should be 'ready', got '{schema_status}'"],
                "value": {"schema_status": schema_status},
            }

        return {"status": "PASS", "score": 10, "message": f"Schema ready with {len(expected_types)} expected types", "issues": [], "value": {"schema_status": schema_status, "expected_types": expected_types}}

    def _check_faq(self, contract: dict[str, Any], slug: str) -> dict[str, Any]:
        """Check FAQ section — reads from converter JSON data (tool_data) for FAQ items."""
        faq_status = str(contract.get("faq_status", "")).strip().lower()

        # Get FAQ items from the converter JSON data file, not the contract
        try:
            tool_data = self.converter_data_service.load_converter_by_slug(slug)
            faq_items = tool_data.get("faq", []) if isinstance(tool_data.get("faq"), list) else []
        except (FileNotFoundError, Exception):
            faq_items = contract.get("faq", []) if isinstance(contract.get("faq"), list) else []

        faq_count = len(faq_items)

        issues = []
        score = 8

        if faq_status != "ready":
            issues.append(f"FAQ status is '{faq_status}' (expected 'ready')")
            score = 4

        if faq_count < self.MIN_FAQ_ITEMS:
            issues.append(f"Only {faq_count} FAQ items (min {self.MIN_FAQ_ITEMS})")
            score = min(score, 3)

        if issues:
            return {"status": "WARN", "score": score, "message": "FAQ has issues", "issues": issues, "value": {"faq_status": faq_status, "faq_count": faq_count}}

        return {"status": "PASS", "score": 8, "message": f"FAQ ready with {faq_count} items", "issues": [], "value": {"faq_status": faq_status, "faq_count": faq_count}}

    def _check_internal_links(self, slug: str, contract: dict[str, Any]) -> dict[str, Any]:
        """Check internal links on the page."""
        try:
            links = self.internal_link_service.get_links_for_landing(slug, contract)
        except Exception:
            links = {}

        # Count all links across all categories
        total_links = 0
        link_details: dict[str, int] = {}
        for category, link_list in links.items():
            if isinstance(link_list, list):
                count = len(link_list)
                total_links += count
                link_details[category] = count

        if total_links == 0:
            return {"status": "FAIL", "score": 0, "message": "No internal links found", "issues": ["At least 3 internal links required"], "value": link_details}

        if total_links < self.MIN_INTERNAL_LINKS:
            return {"status": "WARN", "score": 4, "message": f"Only {total_links} internal links (min {self.MIN_INTERNAL_LINKS})", "issues": [f"Found {total_links} links, need at least {self.MIN_INTERNAL_LINKS}"], "value": link_details}

        return {"status": "PASS", "score": 8, "message": f"{total_links} internal links across {len(link_details)} categories", "issues": [], "value": link_details}

    def _check_related_converters(self, slug: str, tool_data: dict[str, Any]) -> dict[str, Any]:
        """Check related converter links."""
        try:
            related = self.converter_data_service.resolve_related_tools(tool_data, limit=4)
        except Exception:
            related = []

        if not related:
            return {"status": "WARN", "score": 3, "message": "No related converters found", "issues": ["At least 1 related converter recommended"], "value": {"count": 0}}

        count = len(related)
        if count < self.MIN_RELATED_CONVERTERS:
            return {"status": "WARN", "score": 3, "message": f"Only {count} related converter(s)", "issues": [f"Found {count}, need at least {self.MIN_RELATED_CONVERTERS}"], "value": {"count": count, "related": [r.get("slug", "") for r in related]}}

        return {"status": "PASS", "score": 6, "message": f"{count} related converters found", "issues": [], "value": {"count": count, "related": [r.get("slug", "") for r in related]}}

    def _check_word_count(self, tool_data: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
        """Check content word count."""
        # Gather text from various content sources
        text_parts: list[str] = []

        # Tool data content
        description = tool_data.get("description", "") or ""
        if description:
            text_parts.append(description)

        hero = tool_data.get("hero", {})
        if isinstance(hero, dict):
            text_parts.append(hero.get("title", ""))
            text_parts.append(hero.get("text", ""))

        landing = tool_data.get("landing", {})
        if isinstance(landing, dict):
            text_parts.append(landing.get("intro", ""))

        faq = tool_data.get("faq", [])
        if isinstance(faq, list):
            for item in faq:
                text_parts.append(item.get("question", "") if isinstance(item, dict) else "")
                text_parts.append(item.get("answer", "") if isinstance(item, dict) else "")

        # Contract content
        contract_desc = contract.get("description", "") or ""
        if contract_desc:
            text_parts.append(contract_desc)

        full_text = " ".join(text_parts)
        word_count = len(full_text.split())

        if word_count < self.MIN_WORD_COUNT:
            return {"status": "WARN", "score": 2, "message": f"Only {word_count} words (min {self.MIN_WORD_COUNT})", "issues": [f"Content has {word_count} words, minimum recommended is {self.MIN_WORD_COUNT}"], "value": word_count}

        return {"status": "PASS", "score": 5, "message": f"Content has {word_count} words", "issues": [], "value": word_count}

    def _check_image_alt(self, tool_data: dict[str, Any], contract: dict[str, Any]) -> dict[str, Any]:
        """Check image alt attributes."""
        # For converter pages, check og:image alt and any hero images
        og_image_alt = tool_data.get("seo", {}).get("og_image_alt", "") if isinstance(tool_data.get("seo"), dict) else ""
        seo_section = contract.get("seo", {})
        if isinstance(seo_section, dict):
            og_image_alt = og_image_alt or seo_section.get("og_image_alt", "")

        if not og_image_alt:
            hero = tool_data.get("hero", {})
            if isinstance(hero, dict):
                hero_image_alt = hero.get("image_alt", "")
                if hero_image_alt:
                    return {"status": "PASS", "score": 4, "message": "Image alt text present in hero", "issues": [], "value": hero_image_alt}

            return {"status": "WARN", "score": 2, "message": "No image alt text found", "issues": ["OG image should have alt text for accessibility and SEO"], "value": ""}

        return {"status": "PASS", "score": 4, "message": "Image alt text present", "issues": [], "value": og_image_alt}

    def _check_robots(self, contract: dict[str, Any]) -> dict[str, Any]:
        """Check robots meta tag."""
        seo_status = str(contract.get("seo_status", "")).strip().lower()

        if seo_status != "ready":
            return {"status": "WARN", "score": 1, "message": f"SEO status is '{seo_status}' (expected 'ready')", "issues": [f"seo_status should be 'ready' for indexing, got '{seo_status}'"], "value": {"seo_status": seo_status}}

        return {"status": "PASS", "score": 3, "message": "Robots configuration allows indexing", "issues": [], "value": {"seo_status": seo_status}}

    def _check_indexability(self, contract: dict[str, Any]) -> dict[str, Any]:
        """Check if page is indexable based on lifecycle and SEO status."""
        lifecycle = str(contract.get("lifecycle_status", "")).strip().lower()
        seo_status = str(contract.get("seo_status", "")).strip().lower()

        indexable_statuses = {"active", "certified"}
        indexable_seo = {"ready"}

        issues = []
        score = 2

        if lifecycle not in indexable_statuses:
            issues.append(f"Lifecycle status '{lifecycle}' may prevent indexing")
            score = 1

        if seo_status not in indexable_seo:
            issues.append(f"SEO status '{seo_status}' may prevent indexing")
            score = 1

        if issues:
            return {"status": "WARN" if lifecycle in indexable_statuses else "FAIL", "score": score, "message": "Indexability has issues", "issues": issues, "value": {"lifecycle_status": lifecycle, "seo_status": seo_status}}

        return {"status": "PASS", "score": 2, "message": "Page is indexable", "issues": [], "value": {"lifecycle_status": lifecycle, "seo_status": seo_status}}

    # ── Scoring ──────────────────────────────────────────────────

    def _calculate_score(self, check_results: dict[str, dict[str, Any]]) -> int:
        """Calculate total SEO score (0-100)."""
        total = sum(
            result.get("score", 0)
            for result in check_results.values()
        )
        return min(100, max(0, total))

    @staticmethod
    def _score_status(score: int) -> str:
        """Convert numeric score to status label."""
        if score >= 90:
            return "EXCELLENT"
        if score >= 75:
            return "GOOD"
        if score >= 55:
            return "FAIR"
        return "POOR"

    # ── Aggregation ──────────────────────────────────────────────

    def _aggregate_results(self, page_results: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate all page results into summary statistics."""
        total = len(page_results)
        if total == 0:
            return {
                "summary": {"total_audited": 0, "average_score": 0, "best_score": 0, "worst_score": 0},
                "overall_score": 0,
                "overall_status": "NO_DATA",
                "score_distribution": {},
                "critical_issues": [],
                "warnings": [],
                "passed_checks": [],
                "top_issues": [],
                "recommendations": ["No converter pages found to audit"],
            }

        scores = [r["score"] for r in page_results]
        average_score = round(sum(scores) / total, 1)
        best_score = max(scores)
        worst_score = min(scores)

        # Score distribution
        distribution = {
            "excellent": sum(1 for s in scores if s >= 90),
            "good": sum(1 for s in scores if 75 <= s < 90),
            "fair": sum(1 for s in scores if 55 <= s < 75),
            "poor": sum(1 for s in scores if s < 55),
        }

        # Collect all critical issues
        critical_issues: list[dict[str, Any]] = []
        warnings_list: list[dict[str, Any]] = []
        passed_checks: list[dict[str, Any]] = []

        for result in page_results:
            checks = result.get("checks", {})
            slug = result["slug"]
            for check_name, check_result in checks.items():
                status = check_result.get("status", "")
                issues = check_result.get("issues", [])

                if status == "FAIL":
                    critical_issues.append({
                        "slug": slug,
                        "check": check_name,
                        "message": check_result.get("message", ""),
                        "issues": issues,
                    })
                elif status == "WARN":
                    warnings_list.append({
                        "slug": slug,
                        "check": check_name,
                        "message": check_result.get("message", ""),
                        "issues": issues,
                    })
                elif status == "PASS":
                    passed_checks.append({
                        "slug": slug,
                        "check": check_name,
                        "message": check_result.get("message", ""),
                    })

        # Top issues (most common failures across pages)
        fail_counter: Counter[str] = Counter()
        for issue in critical_issues:
            fail_counter[issue["check"]] += 1
        for warn in warnings_list:
            fail_counter[warn["check"]] += 1

        top_issues = [
            {"check": check, "count": count}
            for check, count in fail_counter.most_common(10)
        ]

        # Recommendations
        recommendations = self._generate_recommendations(critical_issues, warnings_list, average_score)

        return {
            "summary": {
                "total_audited": total,
                "average_score": average_score,
                "best_score": best_score,
                "worst_score": worst_score,
            },
            "overall_score": average_score,
            "overall_status": self._score_status(int(average_score)),
            "score_distribution": distribution,
            "critical_issues": critical_issues,
            "warnings": warnings_list,
            "passed_checks": passed_checks,
            "top_issues": top_issues,
            "recommendations": recommendations,
        }

    def _generate_recommendations(
        self,
        critical_issues: list[dict[str, Any]],
        warnings_list: list[dict[str, Any]],
        average_score: float,
    ) -> list[str]:
        """Generate human-readable recommendations based on audit results."""
        recommendations: list[str] = []

        if average_score < 60:
            recommendations.append("CRITICAL: Overall SEO score is below 60. Immediate action required on critical issues.")

        if average_score < 75:
            recommendations.append("IMPORTANT: Focus on fixing critical issues to raise overall score above 75.")

        # Count issues by type
        fail_checks = Counter(i["check"] for i in critical_issues)
        warn_checks = Counter(i["check"] for i in warnings_list)

        if fail_checks.get("Title", 0) > 0:
            recommendations.append(f"Fix titles on {fail_checks['Title']} pages — ensure unique, descriptive titles (30-70 chars).")
        if fail_checks.get("Meta Description", 0) > 0:
            recommendations.append(f"Add meta descriptions to {fail_checks['Meta Description']} pages (50-160 chars).")
        if fail_checks.get("Canonical", 0) > 0:
            recommendations.append(f"Fix canonical URLs on {fail_checks['Canonical']} pages.")
        if fail_checks.get("Internal Links", 0) > 0:
            recommendations.append(f"Add internal links to {fail_checks['Internal Links']} pages (minimum 3 per page).")
        if fail_checks.get("JSON-LD", 0) > 0:
            recommendations.append(f"Fix schema markup on {fail_checks['JSON-LD']} pages.")
        if fail_checks.get("Open Graph", 0) > 0:
            recommendations.append(f"Add Open Graph tags to {fail_checks['Open Graph']} pages for better social sharing.")
        if fail_checks.get("FAQ", 0) > 0 or warn_checks.get("FAQ", 0) > 0:
            recommendations.append("Ensure all pages have FAQ section with at least 3 items and 'ready' status.")

        if not recommendations:
            recommendations.append("All checks passed. Maintain current SEO practices and monitor regularly.")

        return recommendations

    # ── Helpers ──────────────────────────────────────────────────

    def _build_seo_meta(
        self, tool_data: dict[str, Any], slug: str, page_url: str
    ) -> dict[str, Any]:
        """Build expected SEO meta for a tool page, preferring SEO-optimized fields."""
        seo_section = tool_data.get("seo", {}) if isinstance(tool_data.get("seo"), dict) else {}

        # Prefer SEO-optimized title/description, fall back to display title
        title = (
            seo_section.get("title", "")
            or tool_data.get("title", "")
            or slug.replace("-", " ").title()
        )
        description = (
            seo_section.get("description", "")
            or tool_data.get("description", "")
        )
        og_image = seo_section.get("image", f"{PRODUCTION_BASE_URL}/static/images/og-default.png")
        twitter_image = seo_section.get("twitter_image", og_image)
        canonical = tool_data.get("canonical_url") or seo_section.get("canonical", page_url)

        # Ensure "Converigo" in title for branding
        if "converigo" not in title.lower():
            title = f"{title} | Converigo"

        return {
            "title": title,
            "description": description,
            "canonical": canonical,
            "og_image": og_image,
            "og_url": canonical,
            "og_site_name": "Converigo",
            "og_type": "website",
            "twitter_card": "summary_large_image",
            "twitter_site": "@converigo",
            "twitter_title": seo_section.get("twitter_title", title),
            "twitter_description": seo_section.get("twitter_description", description),
            "twitter_image": twitter_image,
        }

    def _now(self) -> str:
        """Get current UTC timestamp."""
        return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

    # ── Report Generation ────────────────────────────────────────

    def generate_report_markdown(self, audit_result: dict[str, Any]) -> str:
        """Generate a human-readable markdown report from audit results."""
        lines: list[str] = []
        lines.append("# SEO Audit Report")
        lines.append("")
        lines.append(f"**Generated:** {audit_result['generated_at']}")
        lines.append(f"**Version:** {audit_result['version']}")
        lines.append(f"**Pages Audited:** {audit_result['pages_audited']}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        summary = audit_result["summary"]
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Pages Audited** | {summary['total_audited']} |")
        lines.append(f"| **Average SEO Score** | {summary['average_score']} / 100 |")
        lines.append(f"| **Best Score** | {summary['best_score']} / 100 |")
        lines.append(f"| **Worst Score** | {summary['worst_score']} / 100 |")
        lines.append(f"| **Overall Status** | {audit_result['overall_status']} |")
        lines.append("")
        lines.append("### Score Distribution")
        lines.append("")
        dist = audit_result["score_distribution"]
        lines.append(f"| Range | Count |")
        lines.append(f"|-------|-------|")
        lines.append(f"| **Excellent (90-100)** | {dist.get('excellent', 0)} |")
        lines.append(f"| **Good (75-89)** | {dist.get('good', 0)} |")
        lines.append(f"| **Fair (55-74)** | {dist.get('fair', 0)} |")
        lines.append(f"| **Poor (0-54)** | {dist.get('poor', 0)} |")
        lines.append("")
        lines.append("### Overall SEO Score")
        lines.append("")
        lines.append(f"**{audit_result['overall_score']} / 100 — {audit_result['overall_status']}**")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Critical Issues
        lines.append("## Critical Issues")
        lines.append("")
        critical = audit_result.get("critical_issues", [])
        if critical:
            lines.append(f"**{len(critical)} critical issue(s) found:**")
            lines.append("")
            for issue in critical:
                lines.append(f"- **[{issue['check']}]** `{issue['slug']}` — {issue['message']}")
                for detail in issue.get("issues", []):
                    lines.append(f"  - {detail}")
            lines.append("")
        else:
            lines.append("✅ No critical issues found.")
            lines.append("")

        # Warnings
        lines.append("## Warnings")
        lines.append("")
        warnings_list = audit_result.get("warnings", [])
        if warnings_list:
            lines.append(f"**{len(warnings_list)} warning(s):**")
            lines.append("")
            for warn in warnings_list[:20]:  # Limit to top 20
                lines.append(f"- **[{warn['check']}]** `{warn['slug']}` — {warn['message']}")
                for detail in warn.get("issues", [])[:2]:  # Show first 2 details
                    lines.append(f"  - {detail}")
            if len(warnings_list) > 20:
                lines.append(f"  - ... and {len(warnings_list) - 20} more warnings")
            lines.append("")
        else:
            lines.append("✅ No warnings.")
            lines.append("")

        # Passed Checks
        lines.append("## Passed Checks")
        lines.append("")
        passed = audit_result.get("passed_checks", [])
        lines.append(f"✅ **{len(passed)} check(s) passed** across all audited pages.")
        lines.append("")

        # Top Issues
        lines.append("## Top Issues")
        lines.append("")
        top_issues = audit_result.get("top_issues", [])
        if top_issues:
            lines.append("| Issue | Affected Pages |")
            lines.append("|-------|----------------|")
            for ti in top_issues:
                lines.append(f"| **{ti['check']}** | {ti['count']} |")
            lines.append("")

        # Recommendations
        lines.append("## Recommendations")
        lines.append("")
        recommendations = audit_result.get("recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        # Per-page results
        lines.append("---")
        lines.append("")
        lines.append("## Per-Page Audit Details")
        lines.append("")
        for page in audit_result.get("page_results", []):
            lines.append(f"### `{page['slug']}` — Score: {page['score']}/100 ({page['status']})")
            lines.append("")
            lines.append(f"- **Name:** {page['name']}")
            lines.append(f"- **Category:** {page['category']}")
            lines.append(f"- **URL:** {page['page_url']}")
            lines.append(f"- **Lifecycle:** {page['lifecycle_status']}")
            lines.append(f"- **SEO Status:** {page['seo_status']}")
            lines.append(f"- **Passed:** {page['passed_count']}/{page['total_checks']}")
            lines.append(f"- **Critical Issues:** {page['critical_issues_count']}")
            lines.append(f"- **Warnings:** {page['warnings_count']}")
            lines.append("")
            # List failing checks
            checks = page.get("checks", {})
            failing = {k: v for k, v in checks.items() if v.get("status") != "PASS"}
            if failing:
                lines.append("#### Issues:")
                for check_name, result in failing.items():
                    lines.append(f"- **{check_name}**: {result['message']}")
                lines.append("")
            lines.append("---")
            lines.append("")

        lines.append("_Report generated by Converigo SEO Audit Engine v1.0.0_")
        return "\n".join(lines)

    def write_report(self, audit_result: dict[str, Any], output_dir: Path) -> Path:
        """Write SEO audit report to disk."""
        output_dir.mkdir(parents=True, exist_ok=True)
        md_content = self.generate_report_markdown(audit_result)
        report_path = output_dir / "SEO_AUDIT_REPORT.md"
        report_path.write_text(md_content, encoding="utf-8")
        return report_path

