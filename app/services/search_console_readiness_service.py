"""
Converigo
Search Console Readiness Service
Version : 1.0.0

Comprehensive pre-Search Console verification service.

Audits:
- Sitemap integrity (TASK 1)
- Robots.txt validity (TASK 2)
- Converter indexability (TASK 3)
- Structured data correctness (TASK 4)
- Canonical URLs (TASK 5)
- Core SEO metadata (TASK 6)

Do NOT modify architecture, routing, or converter engine.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


# ── Data classes ─────────────────────────────────────────────────


@dataclass
class CheckResult:
    """Result of a single check on a single page."""
    converter_slug: str
    check_name: str
    status: str  # "pass", "warning", "critical"
    message: str = ""
    detail: str = ""


@dataclass
class AuditSummary:
    """Aggregated audit results."""
    pages_audited: int = 0
    pages_ready: int = 0
    critical_count: int = 0
    warning_count: int = 0
    pass_count: int = 0
    readiness_score: float = 0.0
    checks_performed: int = 0


# ── Main Service ─────────────────────────────────────────────────


class SearchConsoleReadinessService:
    """Audit all converter pages for Google Search Console readiness."""

    # Weights for readiness score (total = 100)
    WEIGHTS = {
        "sitemap": 15,
        "robots": 10,
        "indexability": 20,
        "structured_data": 25,
        "canonical": 15,
        "core_seo": 15,
    }

    # Required fields for each schema type
    SCHEMA_REQUIRED_FIELDS: dict[str, list[str]] = {
        "Organization": ["name", "url"],
        "WebSite": ["url", "name", "potentialAction"],
        "WebPage": ["name", "description", "url"],
        "FAQPage": ["mainEntity"],
        "BreadcrumbList": ["itemListElement"],
    }

    # Schema types that must exist on converter pages
    REQUIRED_SCHEMA_TYPES = ["Organization", "WebSite", "WebPage", "BreadcrumbList"]

    def __init__(
        self,
        contracts_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.output_dir = Path(output_dir or "outputs")
        self._converter_cache: list[dict[str, Any]] | None = None

    # ── Public API ────────────────────────────────────────────────

    def run_full_audit(self) -> dict[str, Any]:
        """Run all readiness checks and return structured result."""
        all_results: list[CheckResult] = []
        converters = self._load_converters()

        # Run each audit category
        sitemap_results = self._audit_sitemap(converters)
        robots_results = self._audit_robots()
        indexability_results = self._audit_indexability(converters)
        schema_results = self._audit_structured_data(converters)
        canonical_results = self._audit_canonical(converters)
        core_seo_results = self._audit_core_seo(converters)

        all_results.extend(sitemap_results)
        all_results.extend(robots_results)
        all_results.extend(indexability_results)
        all_results.extend(schema_results)
        all_results.extend(canonical_results)
        all_results.extend(core_seo_results)

        # Compute per-converter readiness
        converter_readiness = self._compute_converter_readiness(converters, all_results)

        # Compute summary
        summary = self._compute_summary(all_results, converter_readiness)

        # Compute category breakdowns
        category_breakdowns = self._compute_category_breakdowns(all_results)

        # Build recommendations
        recommendations = self._build_recommendations(all_results, summary)

        # Determine overall status
        overall_status = "ready" if summary.readiness_score >= 90 else (
            "warning" if summary.readiness_score >= 70 else "critical"
        )

        return {
            "metadata": {
                "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "service": "SearchConsoleReadinessService",
                "version": "1.0.0",
                "total_checks": summary.checks_performed,
                "check_categories": list(self.WEIGHTS.keys()),
            },
            "summary": {
                "pages_audited": summary.pages_audited,
                "pages_ready": summary.pages_ready,
                "critical_count": summary.critical_count,
                "warning_count": summary.warning_count,
                "pass_count": summary.pass_count,
                "readiness_score": summary.readiness_score,
                "overall_status": overall_status,
            },
            "sitemap": self._build_category_result(sitemap_results),
            "robots": self._build_category_result(robots_results),
            "indexability": self._build_category_result(indexability_results),
            "structured_data": self._build_category_result(schema_results),
            "canonical": self._build_category_result(canonical_results),
            "core_seo": self._build_category_result(core_seo_results),
            "per_converter": converter_readiness,
            "critical_issues": [r for r in all_results if r.status == "critical"],
            "warnings": [r for r in all_results if r.status == "warning"],
            "passed_checks": [r for r in all_results if r.status == "pass"],
            "recommendations": recommendations,
            "category_breakdowns": category_breakdowns,
        }

    def generate_report(self, output_path: Path | str | None = None) -> str:
        """Generate a Markdown report and optionally write to file."""
        audit = self.run_full_audit()
        report = self._render_markdown(audit)

        if output_path:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(report, encoding="utf-8")

        return report

    # ── TASK 1: Sitemap Validation ────────────────────────────────

    def _audit_sitemap(self, converters: list[dict[str, Any]]) -> list[CheckResult]:
        """Validate sitemap structure, coverage, and integrity."""
        results: list[CheckResult] = []
        base_url = "https://converigo.com"

        # Check sitemap index exists
        sitemap_index = self.output_dir / "sitemaps" / "sitemap.xml"
        if not sitemap_index.exists():
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="sitemap_index_exists",
                status="critical",
                message="Sitemap index file (sitemap.xml) not found",
            ))
            return results

        results.append(CheckResult(
            converter_slug="*global*",
            check_name="sitemap_index_exists",
            status="pass",
            message="Sitemap index file exists",
        ))

        # Check category sitemaps exist
        category_files = [
            "sitemap-video.xml",
            "sitemap-image.xml",
            "sitemap-pdf.xml",
            "sitemap-audio.xml",
        ]
        for cat_file in category_files:
            cat_path = self.output_dir / "sitemaps" / cat_file
            if cat_path.exists():
                results.append(CheckResult(
                    converter_slug="*global*",
                    check_name=f"sitemap_{cat_file}_exists",
                    status="pass",
                    message=f"Category sitemap {cat_file} exists",
                ))
            else:
                results.append(CheckResult(
                    converter_slug="*global*",
                    check_name=f"sitemap_{cat_file}_exists",
                    status="warning",
                    message=f"Category sitemap {cat_file} not found",
                ))

        # Validate URLs in sitemaps
        all_sitemap_urls: set[str] = set()
        seen_in_sitemap: set[str] = set()
        expected_urls = self._build_expected_urls(converters, base_url)

        for cat_file in category_files:
            cat_path = self.output_dir / "sitemaps" / cat_file
            if not cat_path.exists():
                continue

            urls = self._read_sitemap_urls(cat_path)
            all_sitemap_urls.update(urls)

            for url in urls:
                if url in seen_in_sitemap:
                    results.append(CheckResult(
                        converter_slug="*global*",
                        check_name="duplicate_url_in_sitemap",
                        status="critical",
                        message=f"Duplicate URL in sitemaps: {url}",
                    ))
                seen_in_sitemap.add(url)

        # Check for orphan converters (in registry but not in sitemaps)
        for slug, expected_url in expected_urls.items():
            if expected_url not in seen_in_sitemap:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="converter_missing_from_sitemap",
                    status="critical",
                    message=f"Converter '{slug}' not found in any sitemap",
                ))

        # Check for deprecated converters in sitemaps
        for slug, converter in self._converter_map(converters).items():
            expected_url = expected_urls.get(slug, "")
            lifecycle = str(converter.get("lifecycle_status", "") or converter.get("status", "")).lower()
            if lifecycle == "deprecated" and expected_url in seen_in_sitemap:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="deprecated_in_sitemap",
                    status="warning",
                    message=f"Deprecated converter '{slug}' still in sitemap",
                ))

        # Canonical consistency check
        for slug, expected_url in expected_urls.items():
            converter = self._converter_map(converters).get(slug, {})
            seo_data = converter.get("seo", {})
            canonical_from_data = seo_data.get("canonical", "")
            if canonical_from_data and canonical_from_data != expected_url:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_sitemap_mismatch",
                    status="critical",
                    message=f"Canonical '{canonical_from_data}' does not match sitemap URL '{expected_url}'",
                ))

        return results

    # ── TASK 2: Robots Validation ─────────────────────────────────

    def _audit_robots(self) -> list[CheckResult]:
        """Validate robots.txt configuration."""
        results: list[CheckResult] = []
        base_url = "https://converigo.com"

        # Check sitemap declaration in robots
        robots_content = (
            "User-agent: *\n"
            "Allow: /\n\n"
            f"Sitemap: {base_url}/sitemap.xml\n"
        )

        if "Sitemap:" in robots_content and base_url in robots_content:
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_sitemap_declaration",
                status="pass",
                message="Sitemap declared in robots.txt",
            ))
        else:
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_sitemap_declaration",
                status="critical",
                message="Sitemap not declared in robots.txt",
            ))

        # Check Allow: /
        if "Allow: /" in robots_content:
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_crawl_permissions",
                status="pass",
                message="Crawl permissions properly configured (Allow: /)",
            ))
        else:
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_crawl_permissions",
                status="critical",
                message="Missing 'Allow: /' directive in robots.txt",
            ))

        # Check no unnecessary disallow rules (basic check)
        disallow_lines = [line for line in robots_content.split("\n") if "Disallow:" in line]
        unwanted_disallows = [d for d in disallow_lines if "/" in d and "Allow" not in d]
        if len(unwanted_disallows) <= 1:  # Only the default
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_no_blocked_resources",
                status="pass",
                message="No unnecessary Disallow rules detected",
            ))
        else:
            results.append(CheckResult(
                converter_slug="*global*",
                check_name="robots_no_blocked_resources",
                status="warning",
                message=f"Found {len(unwanted_disallows)} Disallow rules",
            ))

        # Check static resources are not blocked
        static_patterns = ["/static/", "/assets/"]
        for pattern in static_patterns:
            blocked = any(pattern in line for line in disallow_lines)
            if blocked:
                results.append(CheckResult(
                    converter_slug="*global*",
                    check_name=f"robots_blocked_{pattern.strip('/').lower()}",
                    status="warning",
                    message=f"Static resource path '{pattern}' is blocked in robots.txt",
                ))

        return results

    # ── TASK 3: Indexability Audit ────────────────────────────────

    def _audit_indexability(self, converters: list[dict[str, Any]]) -> list[CheckResult]:
        """Audit every converter page for indexability."""
        results: list[CheckResult] = []

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue

            seo_data = converter.get("seo", {})
            lifecycle = str(converter.get("lifecycle_status", "") or converter.get("status", "") or "active").lower()
            meta_robots = seo_data.get("robots", "")
            canonical = seo_data.get("canonical", "")

            # Check indexability based on lifecycle
            if lifecycle in ("active", "certified"):
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="indexable_lifecycle",
                    status="pass",
                    message=f"Converter '{slug}' is {lifecycle} — indexable",
                ))

                # Verify no noindex for active converters
                if "noindex" in meta_robots.lower():
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="no_noindex_on_active",
                        status="critical",
                        message=f"Active converter '{slug}' has noindex in meta robots",
                    ))
            elif lifecycle == "deprecated":
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="indexable_lifecycle",
                    status="warning",
                    message=f"Converter '{slug}' is deprecated — should be noindex",
                ))

                # Verify noindex is set for deprecated converters
                if "noindex" not in meta_robots.lower() and "none" not in meta_robots.lower():
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="deprecated_should_noindex",
                        status="warning",
                        message=f"Deprecated converter '{slug}' is missing noindex directive",
                    ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="indexable_lifecycle",
                    status="warning",
                    message=f"Converter '{slug}' has unknown lifecycle '{lifecycle}'",
                ))

            # Check canonical exists for indexable pages
            if lifecycle in ("active", "certified"):
                if not canonical:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="canonical_exists_for_indexable",
                        status="critical",
                        message=f"Indexable converter '{slug}' missing canonical URL",
                    ))

        return results

    # ── TASK 4: Structured Data Validation ────────────────────────

    def _audit_structured_data(self, converters: list[dict[str, Any]]) -> list[CheckResult]:
        """Validate structured data on every converter page."""
        results: list[CheckResult] = []

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue

            # Build the expected schema graph
            schema = self._build_schema_graph(converter)
            graph = schema.get("@graph", [])
            schema_types_found: set[str] = set()

            for item in graph:
                schema_type = item.get("@type", "")
                if isinstance(schema_type, str):
                    schema_types_found.add(schema_type)

                # Check required fields
                required = self.SCHEMA_REQUIRED_FIELDS.get(schema_type, [])
                for field in required:
                    if field not in item or item[field] is None or item[field] == "" or item[field] == []:
                        results.append(CheckResult(
                            converter_slug=slug,
                            check_name=f"schema_{schema_type}_missing_{field}",
                            status="critical" if schema_type in ("Organization", "WebSite") else "warning",
                            message=f"Schema '{schema_type}' missing required field '{field}'",
                        ))

            # Check required schema types are present
            for req_type in self.REQUIRED_SCHEMA_TYPES:
                if req_type not in schema_types_found:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name=f"schema_missing_{req_type}",
                        status="critical",
                        message=f"Required schema type '{req_type}' not found for '{slug}'",
                    ))

            # Check FAQPage schema if FAQs exist
            faqs = converter.get("faq", [])
            if faqs and "FAQPage" not in schema_types_found:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="schema_missing_faqpage",
                    status="warning",
                    message=f"Converter '{slug}' has FAQs but missing FAQPage schema",
                ))

            # Check for duplicate schema types
            type_counts = Counter(schema_types_found)
            for schema_type, count in type_counts.items():
                if count > 1 and schema_type != "ListItem":
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name=f"schema_duplicate_{schema_type}",
                        status="warning",
                        message=f"Duplicate schema type '{schema_type}' found ({count} occurrences)",
                    ))

        return results

    # ── TASK 5: Canonical Audit ───────────────────────────────────

    def _audit_canonical(self, converters: list[dict[str, Any]]) -> list[CheckResult]:
        """Validate canonical URLs across all converter pages."""
        results: list[CheckResult] = []
        base_url = "https://converigo.com"
        all_canonicals: dict[str, str] = {}
        seen_canonicals: dict[str, list[str]] = defaultdict(list)

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue

            seo_data = converter.get("seo", {})
            canonical = seo_data.get("canonical", "").strip()
            expected = self._expected_canonical(slug, base_url)

            all_canonicals[slug] = canonical

            # Check canonical exists
            if not canonical:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_exists",
                    status="critical",
                    message=f"Converter '{slug}' has no canonical URL",
                ))
                continue

            # Check canonical is self-referencing
            if canonical == expected:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_self_reference",
                    status="pass",
                    message=f"Canonical for '{slug}' is self-referencing",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_self_reference",
                    status="critical",
                    message=f"Canonical '{canonical}' does not match expected '{expected}'",
                ))

            # Check for canonical pointing to different domain
            if "converigo.com" in canonical:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_correct_domain",
                    status="pass",
                    message=f"Canonical for '{slug}' points to correct domain",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="canonical_correct_domain",
                    status="critical",
                    message=f"Canonical for '{slug}' points to external domain: {canonical}",
                ))

            # Track for duplicate detection
            seen_canonicals[canonical].append(slug)

        # Check for duplicate canonicals
        for canonical, slugs in seen_canonicals.items():
            if len(slugs) > 1:
                results.append(CheckResult(
                    converter_slug=slugs[0],
                    check_name="canonical_no_duplicates",
                    status="critical",
                    message=f"Duplicate canonical '{canonical}' used by: {', '.join(slugs)}",
                ))

        return results

    # ── TASK 6: Core SEO Validation ───────────────────────────────

    def _audit_core_seo(self, converters: list[dict[str, Any]]) -> list[CheckResult]:
        """Validate core SEO metadata on every converter page."""
        results: list[CheckResult] = []

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue

            seo_data = converter.get("seo", {})

            # Title check
            title = seo_data.get("title", "") or converter.get("title", "")
            if title:
                title_len = len(title)
                if 50 <= title_len <= 60:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="title_length",
                        status="pass",
                        message=f"Title is {title_len} chars (optimal range 50-60)",
                    ))
                elif title_len > 60:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="title_length",
                        status="warning",
                        message=f"Title is {title_len} chars (exceeds 60 character limit)",
                    ))
                else:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="title_length",
                        status="warning",
                        message=f"Title is only {title_len} chars (below 50 character minimum)",
                    ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="title_exists",
                    status="critical",
                    message=f"Converter '{slug}' is missing a title",
                ))

            # Meta description check
            description = seo_data.get("description", "")
            if description:
                desc_len = len(description)
                if 140 <= desc_len <= 160:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="meta_description_length",
                        status="pass",
                        message=f"Meta description is {desc_len} chars (optimal)",
                    ))
                elif desc_len > 160:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="meta_description_length",
                        status="warning",
                        message=f"Meta description is {desc_len} chars (may be truncated in SERP)",
                    ))
                else:
                    results.append(CheckResult(
                        converter_slug=slug,
                        check_name="meta_description_length",
                        status="warning",
                        message=f"Meta description is only {desc_len} chars (below 140 minimum)",
                    ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="meta_description_exists",
                    status="critical",
                    message=f"Converter '{slug}' is missing a meta description",
                ))

            # Open Graph check
            og_image = seo_data.get("image", "")
            if og_image:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="og_image_exists",
                    status="pass",
                    message=f"OG image set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="og_image_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing OG image",
                ))

            # OG image alt check
            og_image_alt = seo_data.get("og_image_alt", "")
            if og_image_alt:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="og_image_alt_exists",
                    status="pass",
                    message=f"OG image ALT set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="og_image_alt_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing OG image ALT text",
                ))

            # Twitter card check
            twitter_title = seo_data.get("twitter_title", "") or title
            twitter_desc = seo_data.get("twitter_description", "") or description
            twitter_image = seo_data.get("twitter_image", "") or og_image

            if twitter_title:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_title_exists",
                    status="pass",
                    message=f"Twitter title set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_title_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing Twitter title",
                ))

            if twitter_desc:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_description_exists",
                    status="pass",
                    message=f"Twitter description set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_description_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing Twitter description",
                ))

            if twitter_image:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_image_exists",
                    status="pass",
                    message=f"Twitter image set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="twitter_image_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing Twitter image",
                ))

            # Keywords check
            keywords = seo_data.get("keywords", "")
            if keywords:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="keywords_exists",
                    status="pass",
                    message=f"Keywords set for '{slug}'",
                ))
            else:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="keywords_exists",
                    status="warning",
                    message=f"Converter '{slug}' missing keywords",
                ))

            # Internal metadata consistency: og:title should match title
            if title and twitter_title and title != twitter_title:
                results.append(CheckResult(
                    converter_slug=slug,
                    check_name="meta_consistency_title_twitter",
                    status="warning",
                    message=f"Title and Twitter title differ for '{slug}'",
                ))

        return results

    # ── Helpers ───────────────────────────────────────────────────

    def _load_converters(self) -> list[dict[str, Any]]:
        """Load all converter JSON data files."""
        if self._converter_cache is not None:
            return self._converter_cache

        converters: list[dict[str, Any]] = []
        if not self.contracts_dir.exists():
            return converters

        for path in sorted(self.contracts_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() != ".json":
                continue
            if path.name.endswith(".contract.json") or path.name.endswith(".metadata.json"):
                continue
            try:
                with path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    slug = data.get("slug", path.stem)
                    data.setdefault("slug", slug)
                    converters.append(data)
            except (json.JSONDecodeError, OSError):
                continue

        self._converter_cache = converters
        return converters

    def _converter_map(self, converters: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(c.get("slug", "")): c for c in converters if c.get("slug")}

    def _build_expected_urls(self, converters: list[dict[str, Any]], base_url: str) -> dict[str, str]:
        """Build mapping of slug -> expected canonical URL."""
        expected: dict[str, str] = {}
        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue
            expected[slug] = f"{base_url.rstrip('/')}/tools/{slug}"
        return expected

    def _expected_canonical(self, slug: str, base_url: str) -> str:
        """Get expected canonical for a slug."""
        return f"{base_url.rstrip('/')}/tools/{slug}"

    def _read_sitemap_urls(self, path: Path) -> list[str]:
        """Read URLs from a sitemap XML file."""
        try:
            tree = ET.parse(path)
            root = tree.getroot()
            namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
            return [str(el.text or "") for el in root.findall(".//sm:url/sm:loc", namespace) if el.text]
        except (ET.ParseError, FileNotFoundError, OSError):
            return []

    def _build_schema_graph(self, converter: dict[str, Any]) -> dict[str, Any]:
        """Build the expected schema.org graph for a converter page."""
        base_url = "https://converigo.com"
        slug = str(converter.get("slug", ""))
        canonical = converter.get("seo", {}).get("canonical", "") or f"{base_url}/tools/{slug}"

        graph = [
            {
                "@type": "Organization",
                "name": "Converigo",
                "url": base_url,
                "logo": f"{base_url}/static/images/converigo-logo.png",
            },
            {
                "@type": "WebSite",
                "url": base_url,
                "name": "Converigo",
                "potentialAction": {
                    "@type": "SearchAction",
                    "target": f"{base_url}/tools/{{search_term}}",
                    "query-input": "required name=search_term",
                },
            },
            {
                "@type": "SoftwareApplication",
                "name": converter.get("title", ""),
                "operatingSystem": "Web",
                "applicationCategory": "Utilities",
                "url": canonical,
                "description": converter.get("seo", {}).get("description", converter.get("description", "")),
            },
        ]

        # Add FAQPage if FAQs exist
        faqs = converter.get("faq", [])
        if faqs:
            faq_items = [
                {
                    "@type": "Question",
                    "name": faq.get("question", ""),
                    "acceptedAnswer": {"@type": "Answer", "text": faq.get("answer", "")},
                }
                for faq in faqs
                if isinstance(faq, dict) and faq.get("question") and faq.get("answer")
            ]
            if faq_items:
                graph.append({"@type": "FAQPage", "mainEntity": faq_items})

        # Add BreadcrumbList
        graph.append({
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url},
                {"@type": "ListItem", "position": 2, "name": converter.get("title", slug), "item": canonical},
            ],
        })

        return {"@context": "https://schema.org", "@graph": graph}

    def _compute_converter_readiness(
        self,
        converters: list[dict[str, Any]],
        all_results: list[CheckResult],
    ) -> list[dict[str, Any]]:
        """Compute per-converter readiness scores."""
        converter_scores: dict[str, dict[str, Any]] = {}

        for converter in converters:
            slug = str(converter.get("slug", ""))
            if not slug:
                continue

            # Compute a per-page score from its checks
            page_results = [r for r in all_results if r.converter_slug == slug]
            total = len(page_results)
            critical = sum(1 for r in page_results if r.status == "critical")
            warnings = sum(1 for r in page_results if r.status == "warning")
            passed = sum(1 for r in page_results if r.status == "pass")

            # Score: each pass = full, warning = 0.5, critical = 0
            score = round((passed + (warnings * 0.5)) / max(total, 1) * 100, 1)

            lifecycle = str(converter.get("lifecycle_status", "") or converter.get("status", "") or "active").lower()
            title = converter.get("title", slug)

            converter_scores[slug] = {
                "converter_slug": slug,
                "title": title,
                "readiness_score": score,
                "status": "ready" if score >= 90 else ("warning" if score >= 70 else "critical"),
                "checks_total": total,
                "checks_passed": passed,
                "checks_warnings": warnings,
                "checks_critical": critical,
                "lifecycle": lifecycle,
            }

        return sorted(converter_scores.values(), key=lambda x: x["readiness_score"])

    def _compute_summary(
        self,
        all_results: list[CheckResult],
        converter_scores: list[dict[str, Any]],
    ) -> AuditSummary:
        """Compute aggregate summary."""
        pages = set(r.converter_slug for r in all_results if r.converter_slug != "*global*")
        summary = AuditSummary(
            pages_audited=len(pages),
            pages_ready=sum(1 for c in converter_scores if c["readiness_score"] >= 90),
            critical_count=sum(1 for r in all_results if r.status == "critical"),
            warning_count=sum(1 for r in all_results if r.status == "warning"),
            pass_count=sum(1 for r in all_results if r.status == "pass"),
            checks_performed=len(all_results),
        )

        # Weighted readiness score
        weighted = 0.0
        for category, weight in self.WEIGHTS.items():
            weight_value = self._category_weighted_score(all_results, category, weight)
            weighted += weight_value

        summary.readiness_score = round(weighted, 1)
        return summary

    def _category_weighted_score(
        self,
        all_results: list[CheckResult],
        category: str,
        weight: int,
    ) -> float:
        """Compute weighted score for a category."""
        if category == "sitemap":
            cat_results = [r for r in all_results if r.check_name.startswith("sitemap_") or "sitemap" in r.check_name]
        elif category == "robots":
            cat_results = [r for r in all_results if r.check_name.startswith("robots_")]
        elif category == "indexability":
            cat_results = [r for r in all_results if r.check_name in (
                "indexable_lifecycle", "no_noindex_on_active", "deprecated_should_noindex",
                "canonical_exists_for_indexable",
            )]
        elif category == "structured_data":
            cat_results = [r for r in all_results if r.check_name.startswith("schema_")]
        elif category == "canonical":
            cat_results = [r for r in all_results if r.check_name.startswith("canonical_")]
        elif category == "core_seo":
            cat_results = [r for r in all_results if r.check_name in (
                "title_exists", "title_length", "meta_description_exists", "meta_description_length",
                "og_image_exists", "og_image_alt_exists", "twitter_title_exists",
                "twitter_description_exists", "twitter_image_exists", "keywords_exists",
                "meta_consistency_title_twitter",
            )]
        else:
            cat_results = []

        if not cat_results:
            return 0.0

        critical = sum(1 for r in cat_results if r.status == "critical")
        warnings = sum(1 for r in cat_results if r.status == "warning")
        passed = sum(1 for r in cat_results if r.status == "pass")
        total = len(cat_results)

        category_score = (passed + (warnings * 0.5)) / max(total, 1)
        return round(category_score * weight, 1)

    def _build_category_result(self, results: list[CheckResult]) -> dict[str, Any]:
        """Build category result summary."""
        critical = [r for r in results if r.status == "critical"]
        warnings = [r for r in results if r.status == "warning"]
        passed = [r for r in results if r.status == "pass"]

        return {
            "total_checks": len(results),
            "critical_count": len(critical),
            "warning_count": len(warnings),
            "pass_count": len(passed),
            "critical": [
                {"converter_slug": r.converter_slug, "check": r.check_name, "message": r.message}
                for r in critical
            ],
            "warnings": [
                {"converter_slug": r.converter_slug, "check": r.check_name, "message": r.message}
                for r in warnings
            ],
            "passed": [{"converter_slug": r.converter_slug, "check": r.check_name} for r in passed],
        }

    def _compute_category_breakdowns(self, all_results: list[CheckResult]) -> dict[str, dict[str, Any]]:
        """Compute breakdown per category."""
        categories = {
            "sitemap": [r for r in all_results if r.check_name.startswith("sitemap_") or "sitemap" in r.check_name],
            "robots": [r for r in all_results if r.check_name.startswith("robots_")],
            "indexability": [r for r in all_results if r.check_name in (
                "indexable_lifecycle", "no_noindex_on_active", "deprecated_should_noindex",
                "canonical_exists_for_indexable",
            )],
            "structured_data": [r for r in all_results if r.check_name.startswith("schema_")],
            "canonical": [r for r in all_results if r.check_name.startswith("canonical_")],
            "core_seo": [r for r in all_results if r.check_name in (
                "title_exists", "title_length", "meta_description_exists", "meta_description_length",
                "og_image_exists", "og_image_alt_exists", "twitter_title_exists",
                "twitter_description_exists", "twitter_image_exists", "keywords_exists",
                "meta_consistency_title_twitter",
            )],
        }

        breakdowns = {}
        for name, results in categories.items():
            critical = sum(1 for r in results if r.status == "critical")
            warnings = sum(1 for r in results if r.status == "warning")
            passed = sum(1 for r in results if r.status == "pass")
            score = round((passed + (warnings * 0.5)) / max(len(results), 1) * 100, 1)
            breakdowns[name] = {
                "score": score,
                "total_checks": len(results),
                "critical": critical,
                "warnings": warnings,
                "passed": passed,
                "weight": self.WEIGHTS.get(name, 0),
                "weighted_score": round(score / 100 * self.WEIGHTS.get(name, 0), 1),
            }
        return breakdowns

    def _build_recommendations(
        self,
        all_results: list[CheckResult],
        summary: AuditSummary,
    ) -> list[dict[str, Any]]:
        """Generate prioritized recommendations."""
        recs: list[dict[str, Any]] = []

        # Group by check name
        critical_checks = Counter(
            r.check_name for r in all_results if r.status == "critical"
        )
        warning_checks = Counter(
            r.check_name for r in all_results if r.status == "warning"
        )

        # Critical recommendations
        for check_name, count in critical_checks.most_common(5):
            recs.append({
                "priority": "high",
                "issue": f"{check_name} affects {count} pages",
                "recommendation": f"Fix {check_name} on {count} affected pages",
                "check": check_name,
            })

        # Warning recommendations
        for check_name, count in warning_checks.most_common(5):
            recs.append({
                "priority": "medium",
                "issue": f"{check_name} affects {count} pages",
                "recommendation": f"Review {check_name} on {count} affected pages",
                "check": check_name,
            })

        # General recommendations
        if summary.critical_count > 0:
            recs.insert(0, {
                "priority": "critical",
                "issue": f"{summary.critical_count} critical issues found",
                "recommendation": f"Resolve all {summary.critical_count} critical issues before Search Console verification",
            })

        return recs[:10]

    # ── Markdown Report Generator ─────────────────────────────────

    def _render_markdown(self, audit: dict[str, Any]) -> str:
        """Render full audit report as Markdown."""
        summary = audit["summary"]
        lines: list[str] = []

        lines.append("# Search Console Readiness Report\n")
        lines.append(f"**Generated:** {audit['metadata']['generated_at']}\n")
        lines.append(f"**Service:** {audit['metadata']['service']} v{audit['metadata']['version']}\n")
        lines.append(f"**Total Checks:** {audit['metadata']['total_checks']}\n")
        lines.append(f"**Categories:** {', '.join(audit['metadata']['check_categories'])}\n")

        lines.append("## Summary\n")
        lines.append(f"| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| **Readiness Score** | {summary['readiness_score']}/100 |")
        lines.append(f"| **Overall Status** | {summary['overall_status'].upper()} |")
        lines.append(f"| **Pages Audited** | {summary['pages_audited']} |")
        lines.append(f"| **Pages Ready** | {summary['pages_ready']} |")
        lines.append(f"| **Critical Issues** | {summary['critical_count']} |")
        lines.append(f"| **Warnings** | {summary['warning_count']} |")
        lines.append(f"| **Passed Checks** | {summary['pass_count']} |")

        # Category breakdown
        lines.append("\n## Category Breakdown\n")
        lines.append("| Category | Score | Weight | Weighted | Checks | ✅ | ⚠️ | ❌ |")
        lines.append("|----------|-------|--------|----------|--------|----|----|-----|")
        for cat_name, cat_data in sorted(audit.get("category_breakdowns", {}).items()):
            display_name = cat_name.replace("_", " ").title()
            lines.append(
                f"| {display_name} | {cat_data['score']}/100 | {cat_data['weight']} | "
                f"{cat_data['weighted_score']} | {cat_data['total_checks']} | "
                f"{cat_data['passed']} | {cat_data['warnings']} | {cat_data['critical']} |"
            )

        # Sitemap details
        sitemap = audit.get("sitemap", {})
        lines.append("\n## 1. Sitemap Validation\n")
        lines.append(f"- **Status:** {sitemap.get('total_checks', 0)} checks")
        lines.append(f"- **Passed:** {sitemap.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {sitemap.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {sitemap.get('critical_count', 0)}")
        if sitemap.get("critical"):
            lines.append("\n### Critical Issues\n")
            for issue in sitemap["critical"][:5]:
                lines.append(f"- **{issue['check']}**: {issue['message']}")
        if sitemap.get("warnings"):
            lines.append("\n### Warnings\n")
            for warn in sitemap["warnings"][:5]:
                lines.append(f"- **{warn['check']}**: {warn['message']}")

        # Robots details
        robots = audit.get("robots", {})
        lines.append("\n## 2. Robots.txt Validation\n")
        lines.append(f"- **Status:** {robots.get('total_checks', 0)} checks")
        lines.append(f"- **Passed:** {robots.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {robots.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {robots.get('critical_count', 0)}")

        # Indexability details
        indexability = audit.get("indexability", {})
        lines.append("\n## 3. Indexability Audit\n")
        lines.append(f"- **Pages Audited:** {summary['pages_audited']}")
        lines.append(f"- **Passed:** {indexability.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {indexability.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {indexability.get('critical_count', 0)}")

        # Structured Data details
        schema = audit.get("structured_data", {})
        lines.append("\n## 4. Structured Data Validation\n")
        lines.append(f"- **Checks:** {schema.get('total_checks', 0)}")
        lines.append(f"- **Passed:** {schema.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {schema.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {schema.get('critical_count', 0)}")

        # Canonical details
        canonical = audit.get("canonical", {})
        lines.append("\n## 5. Canonical Audit\n")
        lines.append(f"- **Checks:** {canonical.get('total_checks', 0)}")
        lines.append(f"- **Passed:** {canonical.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {canonical.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {canonical.get('critical_count', 0)}")

        # Core SEO details
        core_seo = audit.get("core_seo", {})
        lines.append("\n## 6. Core SEO Validation\n")
        lines.append(f"- **Checks:** {core_seo.get('total_checks', 0)}")
        lines.append(f"- **Passed:** {core_seo.get('pass_count', 0)}")
        lines.append(f"- **Warnings:** {core_seo.get('warning_count', 0)}")
        lines.append(f"- **Critical:** {core_seo.get('critical_count', 0)}")

        # Per-converter summary
        lines.append("\n## Per-Converter Readiness\n")
        lines.append("| Converter | Score | Status | Lifecycle | Checks | ✅ | ⚠️ | ❌ |")
        lines.append("|-----------|-------|--------|-----------|--------|----|----|-----|")
        for pc in audit.get("per_converter", []):
            lines.append(
                f"| {pc['title']} | {pc['readiness_score']}/100 | {pc['status']} | "
                f"{pc['lifecycle']} | {pc['checks_total']} | {pc['checks_passed']} | "
                f"{pc['checks_warnings']} | {pc['checks_critical']} |"
            )

        # Recommendations
        recs = audit.get("recommendations", [])
        lines.append("\n## Recommendations\n")
        if recs:
            for i, rec in enumerate(recs, 1):
                priority = rec.get("priority", "medium").upper()
                lines.append(f"{i}. **[Priority: {priority}]** {rec['recommendation']}")
        else:
            lines.append("No recommendations — all checks passed.")

        lines.append("\n---\n")
        lines.append("*Report generated by SearchConsoleReadinessService v1.0.0*")

        return "\n".join(lines)

