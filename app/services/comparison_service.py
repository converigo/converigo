from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.authority_service import AuthorityService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_service import KnowledgeService
from app.services.landing_service import LandingPageBuilder
from app.services.programmatic_seo_service import ProgrammaticSEOService
from app.services.related_converter_service import RelatedConverterService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService


class ComparisonService:
    """Build comparison landing-page content for format-pair pages."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.related_service = RelatedConverterService(self.converter_data_service)
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.programmatic_seo_service = ProgrammaticSEOService(self.contracts_dir)

    def build_payload(self, slug: str) -> dict[str, Any]:
        comparison = self._comparison_specs(slug)
        title = comparison["title"]
        source_format = comparison["source_format"]
        target_format = comparison["target_format"]
        source_authority = self.authority_service.generate_payload(source_format)
        target_authority = self.authority_service.generate_payload(target_format)
        related_converters = self._related_converter_items(slug, source_format, target_format)
        related_formats = self._related_format_items(source_authority, target_authority)
        internal_links = self._build_internal_links(slug)
        faq = self._build_faq(slug, source_format, target_format)
        breadcrumb = [
            {"name": "Home", "url": "/"},
            {"name": title, "url": f"/{slug}"},
        ]
        comparison_table = [
            {"feature": "Best for", "source": f"{source_format.upper()} files", "target": f"{target_format.upper()} files"},
            {"feature": "Compression", "source": source_authority.get("compression", ""), "target": target_authority.get("compression", "")},
            {"feature": "Compatibility", "source": source_authority.get("compatibility", ""), "target": target_authority.get("compatibility", "")},
        ]
        seo_title = f"{title} | Converigo"
        meta_description = f"Compare {source_format.upper()} and {target_format.upper()} to choose the best format for your workflow."
        introduction = {
            "title": f"{title} explained",
            "text": f"Choose between {source_format.upper()} and {target_format.upper()} based on compatibility, quality, and workflow needs.",
        }
        winner_summary = {
            "title": "Winner summary",
            "text": f"{source_format.upper()} is often better when you need broad compatibility, while {target_format.upper()} is better when you need a more specific output workflow.",
        }
        json_ld = {
            "@context": "https://schema.org",
            "@type": "WebPage",
            "name": seo_title,
            "description": meta_description,
            "url": f"{PRODUCTION_BASE_URL}/{slug}",
            "breadcrumb": breadcrumb,
        }

        return {
            "slug": slug,
            "h1": title,
            "seo_title": seo_title,
            "meta_description": meta_description,
            "introduction": introduction,
            "winner_summary": winner_summary,
            "comparison_table": comparison_table,
            "advantages": self._build_list_items(source_format, target_format, "advantages"),
            "disadvantages": self._build_list_items(source_format, target_format, "disadvantages"),
            "best_use_cases": [
                {"title": f"Use {source_format.upper()} when", "text": f"You need the original {source_format.upper()} workflow for editing or sharing."},
                {"title": f"Use {target_format.upper()} when", "text": f"You need the output {target_format.upper()} workflow for distribution or compatibility."},
            ],
            "faq": faq,
            "related_converters": related_converters,
            "related_formats": related_formats,
            "internal_links": internal_links,
            "json_ld": json_ld,
            "breadcrumb": breadcrumb,
            "meta": {"title": seo_title, "description": meta_description, "canonical": f"{PRODUCTION_BASE_URL}/{slug}", "og_url": f"{PRODUCTION_BASE_URL}/{slug}"},
        }

    def render_context(self, request: Any, slug: str) -> dict[str, Any]:
        payload = self.build_payload(slug)
        return {
            "request": request,
            "comparison": payload,
            "title": payload["seo_title"],
            "meta": payload["meta"],
            "structured_data": payload["json_ld"],
            "faq": payload["faq"],
            "related_tools": payload["related_converters"],
            "landing": {
                "h1": payload["h1"],
                "seo_title": payload["seo_title"],
                "meta_description": payload["meta_description"],
                "intro": payload["introduction"],
                "steps": [],
                "benefits": payload["advantages"],
                "supported_formats": {"input": [payload["slug"].split("-vs-")[0].upper()], "output": [payload["slug"].split("-vs-")[1].upper()], "description": "Feature comparison for the selected formats"},
                "tips": payload["best_use_cases"],
                "common_problems": payload["disadvantages"],
                "faq": payload["faq"],
                "json_ld": payload["json_ld"],
                "breadcrumb": payload["breadcrumb"],
                "structured_data": payload["json_ld"],
                "related_tools": payload["related_converters"],
                "related_converters": payload["related_converters"],
                "related_converter": payload["related_converters"][0] if payload["related_converters"] else {"title": payload["h1"], "slug": payload["slug"], "description": payload["meta_description"], "href": f"/{payload['slug']}"},
                "cta": {"title": "Try the converter", "text": "Use the matching converter workflow for the format you need.", "primary_text": "Convert now", "secondary_text": "Read FAQs", "primary_href": "#converter", "secondary_href": "#faq"},
                "download": {"title": "Ready to convert", "text": "Start the conversion process from the relevant converter page.", "primary_text": "Convert now", "primary_href": "#converter"},
                "internal_links": payload["internal_links"],
                "meta": payload["meta"],
            },
        }

    def _comparison_specs(self, slug: str) -> dict[str, Any]:
        spec_map = {
            "pdf-vs-docx": {"title": "PDF vs DOCX", "source_format": "pdf", "target_format": "docx"},
            "png-vs-jpg": {"title": "PNG vs JPG", "source_format": "png", "target_format": "jpg"},
            "webp-vs-png": {"title": "WEBP vs PNG", "source_format": "webp", "target_format": "png"},
            "mp4-vs-mov": {"title": "MP4 vs MOV", "source_format": "mp4", "target_format": "mov"},
            "mp3-vs-wav": {"title": "MP3 vs WAV", "source_format": "mp3", "target_format": "wav"},
        }
        if slug not in spec_map:
            raise ValueError(f"Unsupported comparison slug: {slug}")
        return spec_map[slug]

    def _build_list_items(self, source_format: str, target_format: str, section: str) -> list[dict[str, str]]:
        if section == "advantages":
            return [
                {"title": f"{source_format.upper()} strengths", "text": f"{source_format.upper()} is strong for broad compatibility and stable archival workflows."},
                {"title": f"{target_format.upper()} strengths", "text": f"{target_format.upper()} is strong for editable content and more flexible collaboration."},
            ]
        return [
            {"title": f"{source_format.upper()} limitations", "text": f"{source_format.upper()} may be less flexible for editing after export."},
            {"title": f"{target_format.upper()} limitations", "text": f"{target_format.upper()} may be less ideal for broad compatibility in every workflow."},
        ]

    def _related_converter_items(self, slug: str, source_format: str, target_format: str) -> list[dict[str, Any]]:
        candidates = []
        for contract in self.converter_registry_service.get_active():
            contract_slug = str(contract.get("slug", "")).strip()
            if not contract_slug or contract_slug == slug:
                continue
            if {str(item).lower() for item in contract.get("input_formats", [])} & {source_format, target_format}:
                candidates.append({
                    "slug": contract_slug,
                    "title": str(contract.get("name", contract_slug)).strip(),
                    "description": str(contract.get("description", "")).strip(),
                    "href": str(contract.get("landing_path", f"/{contract_slug}")).strip() or f"/{contract_slug}",
                })
            if len(candidates) >= 4:
                break
        if candidates:
            return candidates
        return [{"slug": "pdf-to-jpg", "title": "PDF to JPG", "description": "Convert documents into images for sharing and previews.", "href": "/pdf-to-jpg"}]

    def _related_format_items(self, source_authority: dict[str, Any], target_authority: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"title": str(source_authority.get("title", "Source format")).strip(), "description": str(source_authority.get("description", "")).strip(), "href": str(source_authority.get("landing_path", "#")).strip() or "#"},
            {"title": str(target_authority.get("title", "Target format")).strip(), "description": str(target_authority.get("description", "")).strip(), "href": str(target_authority.get("landing_path", "#")).strip() or "#"},
        ]

    def _build_internal_links(self, slug: str) -> dict[str, Any]:
        return {
            "title": "Related resources",
            "items": [
                {"title": "Converter hub", "href": "/image-conversion", "description": "Explore more conversion workflows in the hub page."},
                {"title": "Format encyclopedia", "href": "/formats", "description": "Browse format reference pages for more context."},
                {"title": "Blog guide", "href": "/blog", "description": "Read practical conversion guides and how-tos."},
            ],
        }

    def _build_faq(self, slug: str, source_format: str, target_format: str) -> list[dict[str, str]]:
        return [
            {"question": f"Which is better for {source_format.upper()} workflows?", "answer": f"Choose {source_format.upper()} when compatibility or archival needs matter most."},
            {"question": f"Which is better for {target_format.upper()} workflows?", "answer": f"Choose {target_format.upper()} when editing or collaboration is the main goal."},
        ]
