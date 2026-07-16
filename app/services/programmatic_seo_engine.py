"""Production Programmatic SEO Engine - Generate deterministic SEO pages from metadata."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, TYPE_CHECKING

from app.services.authority_service import AuthorityService
from app.services.comparison_service import ComparisonService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.internal_link_service import InternalLinkService
from app.services.knowledge_service import KnowledgeService
from app.services.landing_service import LandingPageBuilder
from app.services.seo_service import SeoService
from app.services.topic_cluster_service import TopicClusterService

if TYPE_CHECKING:
    from app.services.content_quality_service import ContentQualityService


class ProgrammaticSeoEngine:
    """Generate deterministic SEO pages for all formats and converters."""

    # Page types supported
    PAGE_TYPES = [
        "how_to",
        "tutorials",
        "best_practices",
        "troubleshooting",
        "file_format_guides",
        "use_cases",
        "faqs",
        "metadata_guides",
        "mime_guides",
        "software_guides",
    ]

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.comparison_service = ComparisonService(self.contracts_dir)
        self.internal_link_service = InternalLinkService(self.contracts_dir)
        self.topic_cluster_service = TopicClusterService(self.contracts_dir)
        self._content_quality_service: ContentQualityService | None = None

    @property
    def content_quality_service(self) -> ContentQualityService:
        """Lazy load ContentQualityService to avoid circular imports."""
        if self._content_quality_service is None:
            # Import here to avoid circular import at module load time
            from app.services.content_quality_service import ContentQualityService as CQS
            self._content_quality_service = CQS(self.contracts_dir)
        return self._content_quality_service

    def generate_page(
        self, format_name: str, page_type: str
    ) -> dict[str, Any]:
        """Generate a single SEO page for a format."""
        format_lower = format_name.lower()

        if page_type not in self.PAGE_TYPES:
            raise ValueError(f"Unsupported page type: {page_type}")

        try:
            cluster = self.topic_cluster_service.get_cluster(format_lower)
        except Exception:
            cluster = {}

        # Build page based on type
        if page_type == "how_to":
            return self._generate_how_to_page(format_lower, format_name, cluster)
        elif page_type == "tutorials":
            return self._generate_tutorials_page(format_lower, format_name, cluster)
        elif page_type == "best_practices":
            return self._generate_best_practices_page(format_lower, format_name, cluster)
        elif page_type == "troubleshooting":
            return self._generate_troubleshooting_page(format_lower, format_name, cluster)
        elif page_type == "file_format_guides":
            return self._generate_file_format_guide_page(format_lower, format_name, cluster)
        elif page_type == "use_cases":
            return self._generate_use_cases_page(format_lower, format_name, cluster)
        elif page_type == "faqs":
            return self._generate_faqs_page(format_lower, format_name, cluster)
        elif page_type == "metadata_guides":
            return self._generate_metadata_guide_page(format_lower, format_name, cluster)
        elif page_type == "mime_guides":
            return self._generate_mime_guide_page(format_lower, format_name, cluster)
        elif page_type == "software_guides":
            return self._generate_software_guide_page(format_lower, format_name, cluster)

        raise ValueError(f"Unknown page type: {page_type}")

    def generate_all_pages(self) -> dict[str, dict[str, dict[str, Any]]]:
        """Generate all SEO pages for all formats."""
        formats = self._collect_all_formats()
        all_pages = {}

        for fmt in formats:
            all_pages[fmt] = {}
            for page_type in self.PAGE_TYPES:
                try:
                    all_pages[fmt][page_type] = self.generate_page(fmt, page_type)
                except Exception:
                    # Skip pages that fail to generate
                    continue

        return all_pages

    def generate_page_with_quality_check(
        self, format_name: str, page_type: str
    ) -> dict[str, Any]:
        """Generate page with quality evaluation before returning.
        
        Evaluates page quality, attaches quality metrics, and determines publication status.
        """
        page = self.generate_page(format_name, page_type)
        quality_eval = self.content_quality_service.evaluate_page(format_name, page_type)
        
        # Attach quality metrics to page
        page["quality_evaluation"] = quality_eval
        page["quality_score"] = quality_eval.get("quality_score", 0)
        page["quality_decision"] = quality_eval.get("decision", "REJECT")
        page["publication_status"] = self._publication_status_for_decision(
            page["quality_decision"], page["quality_score"]
        )
        
        return page

    def generate_all_pages_with_quality_control(
        self, min_quality_score: float = 60
    ) -> dict[str, dict[str, Any]]:
        """Generate all pages with quality control filtering.
        
        Returns pages with explicit CQE publication status assigned.
        """
        formats = self._collect_all_formats()
        all_pages = {}

        for fmt in formats:
            all_pages[fmt] = {}
            for page_type in self.PAGE_TYPES:
                try:
                    page = self.generate_page_with_quality_check(fmt, page_type)
                    page["publication_status"] = self._publication_status_for_decision(
                        page["quality_decision"], page["quality_score"], min_quality_score
                    )
                    all_pages[fmt][page_type] = page
                except Exception:
                    continue

        return all_pages

    def _publication_status_for_decision(
        self, decision: str, quality_score: float, min_quality_score: float = 60
    ) -> str:
        """Map CQE decision and score into a publication status."""
        if decision == "PASS" and quality_score >= min_quality_score:
            return "ELIGIBLE"
        if decision == "PASS":
            return "HOLD_FOR_REVIEW"
        if decision == "NEEDS_REVIEW":
            return "HOLD_FOR_REVIEW"
        if decision == "NO_INDEX":
            return "NO_INDEX"
        return "REJECT"

    def get_quality_report(self) -> dict[str, Any]:
        """Get comprehensive quality report for all pages."""
        return self.content_quality_service.evaluate_all_pages()

    def get_seo_page_coverage_report(self) -> dict[str, Any]:
        """Build SEO page coverage report."""
        formats = self._collect_all_formats()
        total_formats = len(formats)
        total_possible_pages = total_formats * len(self.PAGE_TYPES)

        pages_generated = 0
        complete_pages = 0

        for fmt in formats:
            for page_type in self.PAGE_TYPES:
                try:
                    page = self.generate_page(fmt, page_type)
                    if page:
                        pages_generated += 1

                        # Check if page is complete
                        if self._is_page_complete(page):
                            complete_pages += 1
                except Exception:
                    continue

        coverage_percentage = (
            (pages_generated / total_possible_pages * 100)
            if total_possible_pages > 0
            else 0
        )
        completeness_percentage = (
            (complete_pages / pages_generated * 100) if pages_generated > 0 else 0
        )
        orphan_pages = total_possible_pages - pages_generated

        return {
            "total_formats": total_formats,
            "seo_pages_total": pages_generated,
            "seo_pages_ready": complete_pages,
            "seo_page_coverage": coverage_percentage,
            "completeness_percentage": completeness_percentage,
            "orphan_seo_pages": orphan_pages,
            "page_types_supported": len(self.PAGE_TYPES),
        }

    # Page generators

    def _generate_how_to_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate 'How To' SEO page."""
        title = f"How to {format_lower.upper()}: Complete Guide"
        description = f"Learn how to use {format_lower.upper()} files effectively. Step-by-step guide with tips and best practices."

        return {
            "format": format_lower,
            "page_type": "how_to",
            "url": f"/how-to/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/how-to/{format_lower}",
                "keywords": [
                    f"how to use {format_lower}",
                    f"how to open {format_lower}",
                    f"how to convert {format_lower}",
                    f"{format_lower} tutorial",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "How To", "url": "/how-to"},
                {"name": format_name.upper(), "url": f"/how-to/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"This comprehensive guide covers everything you need to know about working with {format_lower.upper()} files.",
                "steps": [
                    {"step": 1, "title": f"Understanding {format_lower.upper()}", "content": self._get_knowledge_overview(cluster)},
                    {"step": 2, "title": f"Opening {format_lower.upper()} Files", "content": f"Learn the different ways to open {format_lower.upper()} files."},
                    {"step": 3, "title": f"Converting {format_lower.upper()}", "content": f"Convert {format_lower.upper()} to other formats easily."},
                    {"step": 4, "title": "Tips and Best Practices", "content": self._get_best_practices_content(cluster)},
                ],
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_how_to_schema(title, format_lower),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_tutorials_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Tutorials SEO page."""
        title = f"{format_lower.upper()} Tutorials and Guides"
        description = f"Explore tutorials and guides for {format_lower.upper()}. Learn from step-by-step examples."

        tutorials = cluster.get("tutorials", [])[:5]

        return {
            "format": format_lower,
            "page_type": "tutorials",
            "url": f"/tutorials/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/tutorials/{format_lower}",
                "keywords": [
                    f"{format_lower} tutorial",
                    f"learn {format_lower}",
                    f"{format_lower} guide",
                    f"{format_lower} examples",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Tutorials", "url": "/tutorials"},
                {"name": format_name.upper(), "url": f"/tutorials/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Master {format_lower.upper()} with our comprehensive tutorials.",
                "tutorials": [{"title": t.get("title", ""), "url": t.get("url", ""), "description": t.get("description", "")} for t in tutorials],
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_learning_resource_schema(title, format_lower),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_best_practices_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Best Practices SEO page."""
        title = f"{format_lower.upper()} Best Practices and Tips"
        description = f"Best practices for working with {format_lower.upper()} files. Optimize your workflow."

        best_practices = cluster.get("best_practices", [])

        return {
            "format": format_lower,
            "page_type": "best_practices",
            "url": f"/best-practices/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/best-practices/{format_lower}",
                "keywords": [
                    f"{format_lower} best practices",
                    f"{format_lower} tips",
                    f"{format_lower} optimization",
                    f"how to optimize {format_lower}",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Best Practices", "url": "/best-practices"},
                {"name": format_name.upper(), "url": f"/best-practices/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Learn the best practices for working with {format_lower.upper()} files.",
                "practices": best_practices if isinstance(best_practices, list) else [],
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "best_practices"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_troubleshooting_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Troubleshooting SEO page."""
        title = f"{format_lower.upper()} Troubleshooting and Common Issues"
        description = f"Troubleshoot common {format_lower.upper()} issues. Get solutions and fixes."

        return {
            "format": format_lower,
            "page_type": "troubleshooting",
            "url": f"/troubleshooting/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/troubleshooting/{format_lower}",
                "keywords": [
                    f"{format_lower} troubleshooting",
                    f"fix {format_lower} issues",
                    f"{format_lower} problems",
                    f"{format_lower} errors",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Troubleshooting", "url": "/troubleshooting"},
                {"name": format_name.upper(), "url": f"/troubleshooting/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Find solutions to common {format_lower.upper()} problems.",
                "issues": [
                    {"issue": f"Cannot open {format_lower.upper()} file", "solution": f"Try using recommended software to open {format_lower.upper()} files."},
                    {"issue": f"Converting {format_lower.upper()} fails", "solution": f"Ensure your {format_lower.upper()} file is not corrupted and try again."},
                    {"issue": f"{format_lower.upper()} file is too large", "solution": f"Compress or optimize your {format_lower.upper()} file."},
                ],
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_faq_schema("FAQPage", [
                {"question": f"Cannot open {format_lower.upper()} file", "answer": f"Try recommended software for {format_lower.upper()}."},
                {"question": f"How to convert {format_lower.upper()}", "answer": f"Use Converigo to convert {format_lower.upper()} to other formats."},
            ]),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_file_format_guide_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate File Format Guide SEO page."""
        title = f"Complete {format_lower.upper()} File Format Guide"
        description = f"Comprehensive guide to the {format_lower.upper()} file format. Technical specifications and details."

        return {
            "format": format_lower,
            "page_type": "file_format_guides",
            "url": f"/formats/{format_lower}/guide",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/formats/{format_lower}/guide",
                "keywords": [
                    f"{format_lower} file format",
                    f"{format_lower} specification",
                    f"{format_lower} technical guide",
                    f"what is {format_lower}",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Formats", "url": "/formats"},
                {"name": format_name.upper(), "url": f"/formats/{format_lower}"},
                {"name": "Guide", "url": f"/formats/{format_lower}/guide"},
            ],
            "content": {
                "h1": title,
                "specification": cluster.get("specification", {}),
                "mime": cluster.get("mime", {}),
                "extensions": cluster.get("file_extensions", {}),
                "history": cluster.get("history", {}),
                "compression": cluster.get("compression", {}),
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "file_format_guide"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_use_cases_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Use Cases SEO page."""
        title = f"{format_lower.upper()} Use Cases and Applications"
        description = f"Discover real-world use cases and applications for {format_lower.upper()} files."

        return {
            "format": format_lower,
            "page_type": "use_cases",
            "url": f"/use-cases/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/use-cases/{format_lower}",
                "keywords": [
                    f"{format_lower} use cases",
                    f"when to use {format_lower}",
                    f"{format_lower} applications",
                    f"{format_lower} applications",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Use Cases", "url": "/use-cases"},
                {"name": format_name.upper(), "url": f"/use-cases/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Explore practical applications and use cases for {format_lower.upper()}.",
                "use_cases": [
                    {"title": f"Digital Publishing with {format_lower.upper()}", "description": f"Learn how {format_lower.upper()} is used in digital publishing."},
                    {"title": f"Web Graphics with {format_lower.upper()}", "description": f"{format_lower.upper()} for optimized web graphics."},
                    {"title": f"Archival Storage with {format_lower.upper()}", "description": f"Long-term storage solutions using {format_lower.upper()}."},
                ],
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "use_cases"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_faqs_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate FAQs SEO page."""
        title = f"Frequently Asked Questions about {format_lower.upper()}"
        description = f"Common questions and answers about {format_lower.upper()} files."

        faq_items = cluster.get("faq", [])

        return {
            "format": format_lower,
            "page_type": "faqs",
            "url": f"/faq/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/faq/{format_lower}",
                "keywords": [
                    f"{format_lower} faq",
                    f"frequently asked questions {format_lower}",
                    f"{format_lower} questions",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "FAQ", "url": "/faq"},
                {"name": format_name.upper(), "url": f"/faq/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "faq": faq_items,
            },
            "json_ld": self._build_faq_schema(
                "FAQPage",
                [
                    {"question": item.get("question", ""), "answer": item.get("answer", "")}
                    for item in faq_items[:10]
                ],
            ),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_metadata_guide_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Metadata Guide SEO page."""
        title = f"{format_lower.upper()} Metadata Guide and Reference"
        description = f"Complete guide to metadata in {format_lower.upper()} files."

        metadata = cluster.get("metadata", {})

        return {
            "format": format_lower,
            "page_type": "metadata_guides",
            "url": f"/guides/{format_lower}/metadata",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/guides/{format_lower}/metadata",
                "keywords": [
                    f"{format_lower} metadata",
                    f"{format_lower} metadata fields",
                    f"{format_lower} properties",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Guides", "url": "/guides"},
                {"name": format_name.upper(), "url": f"/guides/{format_lower}"},
                {"name": "Metadata", "url": f"/guides/{format_lower}/metadata"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Comprehensive guide to metadata in {format_lower.upper()} files.",
                "metadata": metadata,
                "common_fields": metadata.get("common_metadata_fields", []),
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "metadata_guide"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_mime_guide_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate MIME Type Guide SEO page."""
        title = f"{format_lower.upper()} MIME Type Guide"
        description = f"MIME type reference and guide for {format_lower.upper()} files."

        mime = cluster.get("mime", {})

        return {
            "format": format_lower,
            "page_type": "mime_guides",
            "url": f"/guides/{format_lower}/mime",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/guides/{format_lower}/mime",
                "keywords": [
                    f"{format_lower} mime type",
                    f"mime type {format_lower}",
                    f"{format_lower} content type",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Guides", "url": "/guides"},
                {"name": format_name.upper(), "url": f"/guides/{format_lower}"},
                {"name": "MIME", "url": f"/guides/{format_lower}/mime"},
            ],
            "content": {
                "h1": title,
                "introduction": f"MIME type information for {format_lower.upper()} files.",
                "primary_mime": mime.get("primary", ""),
                "alternative_mimes": mime.get("alternatives", []),
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "mime_guide"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    def _generate_software_guide_page(
        self, format_lower: str, format_name: str, cluster: dict[str, Any]
    ) -> dict[str, Any]:
        """Generate Software Guide SEO page."""
        title = f"Software for {format_lower.upper()} - Open and Edit Files"
        description = f"Best software and tools to open and edit {format_lower.upper()} files."

        software = cluster.get("software", {})

        return {
            "format": format_lower,
            "page_type": "software_guides",
            "url": f"/software/{format_lower}",
            "seo": {
                "title": title,
                "meta_description": description,
                "canonical": f"https://converigo.io/software/{format_lower}",
                "keywords": [
                    f"software for {format_lower}",
                    f"open {format_lower} files",
                    f"{format_lower} editor",
                    f"best {format_lower} software",
                ],
            },
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Software", "url": "/software"},
                {"name": format_name.upper(), "url": f"/software/{format_lower}"},
            ],
            "content": {
                "h1": title,
                "introduction": f"Discover the best software to work with {format_lower.upper()} files.",
                "native_support": software.get("native_support", [])[:5],
                "also_supported_by": software.get("also_supported_by", [])[:5],
                "online_tools": software.get("online_tools", []),
                "faq": cluster.get("faq", [])[:3],
            },
            "json_ld": self._build_article_schema(title, format_lower, "software_guide"),
            "internal_links": self._get_internal_links(format_lower),
            "related_topics": self._get_related_topics(format_lower, cluster),
            "related_converters": self._get_related_converters(format_lower),
        }

    # JSON-LD Schema builders

    def _build_how_to_schema(self, title: str, format_name: str) -> dict[str, Any]:
        """Build HowTo JSON-LD schema."""
        return {
            "@context": "https://schema.org",
            "@type": "HowTo",
            "name": title,
            "description": f"Complete guide on how to use {format_name.upper()}",
            "step": [
                {
                    "@type": "HowToStep",
                    "name": "Step 1: Understanding",
                    "text": f"Learn about {format_name.upper()} format",
                },
                {
                    "@type": "HowToStep",
                    "name": "Step 2: Opening Files",
                    "text": f"Open {format_name.upper()} files with appropriate software",
                },
                {
                    "@type": "HowToStep",
                    "name": "Step 3: Converting",
                    "text": f"Convert {format_name.upper()} to other formats",
                },
            ],
        }

    def _build_learning_resource_schema(self, title: str, format_name: str) -> dict[str, Any]:
        """Build Learning Resource JSON-LD schema."""
        return {
            "@context": "https://schema.org",
            "@type": "LearningResource",
            "name": title,
            "description": f"Tutorials for {format_name.upper()}",
            "learningResourceType": "Tutorial",
        }

    def _build_article_schema(self, title: str, format_name: str, article_type: str) -> dict[str, Any]:
        """Build Article JSON-LD schema."""
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": title,
            "author": {
                "@type": "Organization",
                "name": "Converigo",
            },
            "datePublished": datetime.now().isoformat(),
            "dateModified": datetime.now().isoformat(),
            "articleBody": f"Article about {format_name.upper()} - {article_type}",
        }

    def _build_faq_schema(self, schema_type: str, faq_items: list[dict[str, str]]) -> dict[str, Any]:
        """Build FAQ JSON-LD schema."""
        main_entity = [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": item["answer"],
                },
            }
            for item in faq_items[:10]
        ]

        return {
            "@context": "https://schema.org",
            "@type": schema_type,
            "mainEntity": main_entity,
        }

    # Helper methods

    def _get_knowledge_overview(self, cluster: dict[str, Any]) -> str:
        """Extract knowledge overview from cluster."""
        knowledge = cluster.get("knowledge", {})
        return knowledge.get("overview", "")

    def _get_best_practices_content(self, cluster: dict[str, Any]) -> str:
        """Extract best practices from cluster."""
        practices = cluster.get("best_practices", [])
        if isinstance(practices, list) and practices:
            return practices[0] if isinstance(practices[0], str) else str(practices[0])
        return ""

    def _get_internal_links(self, format_name: str) -> dict[str, Any]:
        """Get internal links for format."""
        try:
            return self.internal_link_service.get_links_for_format(format_name)
        except Exception:
            return {"related": [], "comparisons": [], "converters": []}

    def _get_related_topics(self, format_name: str, cluster: dict[str, Any]) -> list[dict[str, str]]:
        """Get related topics."""
        related_formats = cluster.get("related_formats", [])
        related_comparisons = cluster.get("comparisons", [])

        topics = []
        if isinstance(related_formats, list):
            topics.extend([{"title": fmt.get("title", ""), "url": fmt.get("url", "")} for fmt in related_formats[:3]])
        if isinstance(related_comparisons, list):
            topics.extend([{"title": comp.get("title", ""), "url": comp.get("url", "")} for comp in related_comparisons[:2]])

        return topics

    def _get_related_converters(self, format_name: str) -> list[dict[str, str]]:
        """Get related converters."""
        try:
            converters = self.converter_registry_service.get_active()
            related = []
            for converter in converters:
                inputs = converter.get("input_formats", [])
                outputs = converter.get("output_formats", [])

                if format_name.upper() in inputs or format_name.upper() in outputs:
                    related.append(
                        {
                            "name": converter.get("name", ""),
                            "slug": converter.get("slug", ""),
                            "url": f"/{converter.get('slug', '')}",
                        }
                    )

            return related[:5]
        except Exception:
            return []

    def _is_page_complete(self, page: dict[str, Any]) -> bool:
        """Check if page has all required fields."""
        required_fields = [
            "format",
            "page_type",
            "url",
            "seo",
            "breadcrumb",
            "content",
            "json_ld",
            "internal_links",
            "related_topics",
            "related_converters",
        ]

        for field in required_fields:
            if field not in page or page[field] is None:
                return False

        # Check SEO fields
        seo = page.get("seo", {})
        seo_fields = ["title", "meta_description", "canonical"]
        for field in seo_fields:
            if field not in seo or not seo[field]:
                return False

        return True

    def _collect_all_formats(self) -> list[str]:
        """Collect all unique formats from converters."""
        try:
            converters = self.converter_registry_service.get_active()
            formats = set()

            for converter in converters:
                inputs = converter.get("input_formats", [])
                outputs = converter.get("output_formats", [])

                for fmt in inputs + outputs:
                    formats.add(fmt.lower())

            return sorted(list(formats))
        except Exception:
            return []
