from __future__ import annotations

from pathlib import Path
from typing import Any

from app.services.authority_service import AuthorityService
from app.services.comparison_service import ComparisonService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.hub_page_service import HubPageService
from app.services.knowledge_service import KnowledgeService
from app.services.landing_service import LandingPageBuilder
from app.services.related_converter_service import RelatedConverterService
from app.services.seo_service import SeoService


class InternalLinkService:
    """Generate comprehensive internal links for all page types with smart scoring and deduplication."""

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.seo_service = SeoService(self.contracts_dir)
        self.landing_builder = LandingPageBuilder(self.seo_service, self.converter_data_service)
        self.authority_service = AuthorityService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.related_service = RelatedConverterService(self.converter_data_service)
        self.comparison_service = ComparisonService(self.contracts_dir)
        self.hub_service = HubPageService()

    def get_links_for_landing(self, slug: str, contract: dict[str, Any] | None = None) -> dict[str, Any]:
        """Generate internal links for a converter landing page."""
        if contract is None:
            try:
                contract = self.converter_registry_service.get_by_slug(slug)
            except Exception:
                return self._empty_links()

        links = {
            "related_converters": self._get_related_converters(slug, contract),
            "related_formats": self._get_related_formats(contract),
            "related_comparisons": self._get_related_comparisons(contract),
            "related_knowledge": self._get_related_knowledge(contract),
            "related_hubs": self._get_related_hubs(contract),
            "related_articles": self._get_related_articles(contract),
        }
        return self._deduplicate_links(links)

    def get_links_for_comparison(self, slug: str) -> dict[str, Any]:
        """Generate internal links for a comparison page (e.g., pdf-vs-docx)."""
        links = {
            "related_converters": self._get_comparison_related_converters(slug),
            "related_formats": self._get_comparison_related_formats(slug),
            "related_comparisons": self._get_comparison_related_comparisons(slug),
            "related_hubs": self._get_comparison_related_hubs(slug),
            "related_knowledge": self._get_comparison_related_knowledge(slug),
            "related_articles": self._get_comparison_related_articles(slug),
        }
        return self._deduplicate_links(links)

    def get_links_for_format(self, format_name: str) -> dict[str, Any]:
        """Generate internal links for a format encyclopedia page."""
        links = {
            "related_converters": self._get_format_converters(format_name),
            "related_formats": self._get_format_related_formats(format_name),
            "related_comparisons": self._get_format_comparisons(format_name),
            "related_knowledge": self._get_format_knowledge(format_name),
            "related_hubs": self._get_format_hubs(format_name),
        }
        return self._deduplicate_links(links)

    def get_links_for_hub(self, hub_slug: str) -> dict[str, Any]:
        """Generate internal links for a hub page (e.g., image-conversion)."""
        links = {
            "related_converters": self._get_hub_converters(hub_slug),
            "related_formats": self._get_hub_formats(hub_slug),
            "related_comparisons": self._get_hub_comparisons(hub_slug),
            "related_knowledge": self._get_hub_knowledge(hub_slug),
        }
        return self._deduplicate_links(links)

    def get_links_for_knowledge(self, format_name: str) -> dict[str, Any]:
        """Generate internal links for a knowledge/education page."""
        links = {
            "related_converters": self._get_format_converters(format_name),
            "related_formats": self._get_format_related_formats(format_name),
            "related_comparisons": self._get_format_comparisons(format_name),
            "related_hubs": self._get_format_hubs(format_name),
        }
        return self._deduplicate_links(links)

    # Private methods for building link groups

    def _get_related_converters(self, slug: str, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related converter pages for a landing page."""
        try:
            tool_data = self.converter_data_service.load_converter_by_slug(slug)
        except Exception:
            tool_data = contract

        related = self.related_service.get_related_converters(tool_data or contract, limit=5)
        return self._score_and_format_converters(related, slug)

    def _get_related_formats(self, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related format encyclopedia pages."""
        formats = set()
        formats.update(str(f).lower() for f in (contract.get("input_formats") or []))
        formats.update(str(f).lower() for f in (contract.get("output_formats") or []))

        result = []
        for fmt in sorted(formats)[:3]:
            result.append({
                "title": f"{fmt.upper()} format guide",
                "href": f"/formats/{fmt.lower()}",
                "description": f"Learn about the {fmt.upper()} file format and when to use it.",
                "score": 10,
            })
        return result

    def _get_related_comparisons(self, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related comparison pages."""
        input_formats = [str(f).lower() for f in (contract.get("input_formats") or [])]
        output_formats = [str(f).lower() for f in (contract.get("output_formats") or [])]

        comparison_pairs = [
            ("pdf", "docx"),
            ("png", "jpg"),
            ("webp", "png"),
            ("mp4", "mov"),
            ("mp3", "wav"),
        ]

        result = []
        for fmt1, fmt2 in comparison_pairs:
            if (fmt1 in input_formats or fmt1 in output_formats) and (fmt2 in input_formats or fmt2 in output_formats):
                slug = f"{fmt1}-vs-{fmt2}"
                result.append({
                    "title": f"{fmt1.upper()} vs {fmt2.upper()}",
                    "href": f"/{slug}",
                    "description": f"Compare {fmt1.upper()} and {fmt2.upper()} formats side-by-side.",
                    "score": 8,
                })
        return result

    def _get_related_knowledge(self, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related knowledge/educational pages."""
        formats = set()
        formats.update(str(f).lower() for f in (contract.get("input_formats") or []))
        formats.update(str(f).lower() for f in (contract.get("output_formats") or []))

        result = []
        for fmt in sorted(formats)[:2]:
            result.append({
                "title": f"Guide to {fmt.upper()} files",
                "href": f"/knowledge/{fmt.lower()}",
                "description": f"Deep dive into {fmt.upper()} format specifications and best practices.",
                "score": 7,
            })
        return result

    def _get_related_hubs(self, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related hub pages by category."""
        category_to_hub = {
            "image": "image-conversion",
            "pdf": "pdf-conversion",
            "document": "document-conversion",
            "audio": "audio-conversion",
            "video": "video-conversion",
        }

        category = str(contract.get("category", "")).lower()
        result = []

        if category in category_to_hub:
            hub_slug = category_to_hub[category]
            hub_name = hub_slug.replace("-", " ").title()
            result.append({
                "title": f"{hub_name} hub",
                "href": f"/{hub_slug}",
                "description": f"Explore more {hub_slug.replace('-', ' ')} tools and workflows.",
                "score": 9,
            })

        return result

    def _get_related_articles(self, contract: dict[str, Any]) -> list[dict[str, Any]]:
        """Find related blog articles."""
        slug = contract.get("slug", "")
        result = []

        blog_articles = [
            ("how-to-convert-mp4-to-mp3", "How to Convert MP4 to MP3", "mp4", "mp3"),
            ("png-to-jpg-guide", "PNG to JPG Guide", "png", "jpg"),
        ]

        for article_slug, title, fmt1, fmt2 in blog_articles:
            input_formats = [str(f).lower() for f in (contract.get("input_formats") or [])]
            output_formats = [str(f).lower() for f in (contract.get("output_formats") or [])]
            if fmt1 in input_formats and fmt2 in output_formats:
                result.append({
                    "title": title,
                    "href": f"/blog/{article_slug}",
                    "description": f"Step-by-step guide for {slug} conversion workflow.",
                    "score": 6,
                })

        return result

    # Comparison page link builders

    def _get_comparison_related_converters(self, slug: str) -> list[dict[str, Any]]:
        """Find converter pages related to a comparison."""
        try:
            comparison_specs = self._get_comparison_specs(slug)
            source_format = comparison_specs["source_format"]
            target_format = comparison_specs["target_format"]

            converters = self.converter_registry_service.get_active()
            related = []

            for converter in converters:
                score = 0
                input_formats = [str(f).lower() for f in (converter.get("input_formats") or [])]
                output_formats = [str(f).lower() for f in (converter.get("output_formats") or [])]

                if source_format.lower() in input_formats:
                    score += 5
                if target_format.lower() in output_formats:
                    score += 5

                if score > 0:
                    related.append({
                        "converter": converter,
                        "score": score,
                    })

            related.sort(key=lambda x: x["score"], reverse=True)
            return self._score_and_format_converters([r["converter"] for r in related[:4]], "")
        except Exception:
            return []

    def _get_comparison_related_formats(self, slug: str) -> list[dict[str, Any]]:
        """Find format pages related to a comparison."""
        try:
            comparison_specs = self._get_comparison_specs(slug)
            source_format = comparison_specs["source_format"]
            target_format = comparison_specs["target_format"]

            result = [
                {
                    "title": f"{source_format.upper()} format guide",
                    "href": f"/formats/{source_format.lower()}",
                    "description": f"Learn more about the {source_format.upper()} format.",
                    "score": 10,
                },
                {
                    "title": f"{target_format.upper()} format guide",
                    "href": f"/formats/{target_format.lower()}",
                    "description": f"Learn more about the {target_format.upper()} format.",
                    "score": 10,
                },
            ]
            return result
        except Exception:
            return []

    def _get_comparison_related_comparisons(self, slug: str) -> list[dict[str, Any]]:
        """Find other comparison pages."""
        comparison_pairs = [
            ("pdf", "docx"),
            ("png", "jpg"),
            ("webp", "png"),
            ("mp4", "mov"),
            ("mp3", "wav"),
        ]

        result = []
        for fmt1, fmt2 in comparison_pairs:
            pair_slug = f"{fmt1}-vs-{fmt2}"
            if pair_slug != slug:
                result.append({
                    "title": f"{fmt1.upper()} vs {fmt2.upper()}",
                    "href": f"/{pair_slug}",
                    "description": f"Compare {fmt1.upper()} and {fmt2.upper()} formats.",
                    "score": 5,
                })

        return result[:3]

    def _get_comparison_related_hubs(self, slug: str) -> list[dict[str, Any]]:
        """Find hub pages related to a comparison."""
        comparison_map = {
            "pdf-vs-docx": "document-conversion",
            "png-vs-jpg": "image-conversion",
            "webp-vs-png": "image-conversion",
            "mp4-vs-mov": "video-conversion",
            "mp3-vs-wav": "audio-conversion",
        }

        hub_slug = comparison_map.get(slug)
        if hub_slug:
            hub_name = hub_slug.replace("-", " ").title()
            return [
                {
                    "title": f"{hub_name} hub",
                    "href": f"/{hub_slug}",
                    "description": f"Explore more {hub_slug.replace('-', ' ')} tools.",
                    "score": 8,
                }
            ]
        return []

    def _get_comparison_related_knowledge(self, slug: str) -> list[dict[str, Any]]:
        """Find knowledge pages related to a comparison."""
        try:
            comparison_specs = self._get_comparison_specs(slug)
            source_format = comparison_specs["source_format"]
            target_format = comparison_specs["target_format"]

            result = [
                {
                    "title": f"Guide to {source_format.upper()} files",
                    "href": f"/knowledge/{source_format.lower()}",
                    "description": f"Deep dive into {source_format.upper()} format details.",
                    "score": 7,
                },
                {
                    "title": f"Guide to {target_format.upper()} files",
                    "href": f"/knowledge/{target_format.lower()}",
                    "description": f"Deep dive into {target_format.upper()} format details.",
                    "score": 7,
                },
            ]
            return result
        except Exception:
            return []

    def _get_comparison_related_articles(self, slug: str) -> list[dict[str, Any]]:
        """Find blog articles related to a comparison."""
        article_map = {
            "pdf-vs-docx": ("how-to-convert-pdf-to-docx", "PDF to Word Conversion"),
            "png-vs-jpg": ("png-to-jpg-guide", "PNG to JPG Guide"),
        }

        article_info = article_map.get(slug)
        if article_info:
            article_slug, title = article_info
            return [
                {
                    "title": title,
                    "href": f"/blog/{article_slug}",
                    "description": f"Detailed guide for {slug.replace('-', ' ')} comparison.",
                    "score": 6,
                }
            ]
        return []

    # Format page link builders

    def _get_format_converters(self, format_name: str) -> list[dict[str, Any]]:
        """Find converters for a format."""
        converters = self.converter_registry_service.get_active()
        relevant = []

        format_lower = format_name.lower()
        for converter in converters:
            score = 0
            input_formats = [str(f).lower() for f in (converter.get("input_formats") or [])]
            output_formats = [str(f).lower() for f in (converter.get("output_formats") or [])]

            if format_lower in input_formats:
                score += 5
            if format_lower in output_formats:
                score += 5

            if score > 0:
                relevant.append({
                    "converter": converter,
                    "score": score,
                })

        relevant.sort(key=lambda x: x["score"], reverse=True)
        return self._score_and_format_converters([r["converter"] for r in relevant[:5]], "")

    def _get_format_related_formats(self, format_name: str) -> list[dict[str, Any]]:
        """Find related formats."""
        format_relations = {
            "pdf": ["docx", "txt", "jpg"],
            "docx": ["pdf", "txt", "odt"],
            "png": ["jpg", "webp", "gif"],
            "jpg": ["png", "webp", "pdf"],
            "webp": ["png", "jpg", "gif"],
            "mp4": ["mov", "avi", "mkv"],
            "mp3": ["wav", "ogg", "flac"],
        }

        related = format_relations.get(format_name.lower(), [])
        result = []

        for related_fmt in related[:3]:
            result.append({
                "title": f"{related_fmt.upper()} format guide",
                "href": f"/formats/{related_fmt.lower()}",
                "description": f"Compare with {related_fmt.upper()} format specs.",
                "score": 7,
            })

        return result

    def _get_format_comparisons(self, format_name: str) -> list[dict[str, Any]]:
        """Find comparison pages mentioning this format."""
        format_lower = format_name.lower()
        comparison_pairs = [
            ("pdf", "docx"),
            ("png", "jpg"),
            ("webp", "png"),
            ("mp4", "mov"),
            ("mp3", "wav"),
        ]

        result = []
        for fmt1, fmt2 in comparison_pairs:
            if format_lower == fmt1 or format_lower == fmt2:
                slug = f"{fmt1}-vs-{fmt2}"
                result.append({
                    "title": f"{fmt1.upper()} vs {fmt2.upper()}",
                    "href": f"/{slug}",
                    "description": f"Compare with {fmt2.upper() if fmt1 == format_lower else fmt1.upper()}.",
                    "score": 8,
                })

        return result

    def _get_format_knowledge(self, format_name: str) -> list[dict[str, Any]]:
        """Find knowledge pages for this format."""
        result = [
            {
                "title": f"Complete {format_name.upper()} specification",
                "href": f"/knowledge/{format_name.lower()}/specs",
                "description": f"Technical details about {format_name.upper()} compression and encoding.",
                "score": 9,
            }
        ]
        return result

    def _get_format_hubs(self, format_name: str) -> list[dict[str, Any]]:
        """Find hub pages relevant to this format."""
        format_to_hub = {
            "pdf": "pdf-conversion",
            "docx": "document-conversion",
            "png": "image-conversion",
            "jpg": "image-conversion",
            "webp": "image-conversion",
            "mp4": "video-conversion",
            "mp3": "audio-conversion",
            "wav": "audio-conversion",
        }

        hub_slug = format_to_hub.get(format_name.lower())
        if hub_slug:
            hub_name = hub_slug.replace("-", " ").title()
            return [
                {
                    "title": f"{hub_name} hub",
                    "href": f"/{hub_slug}",
                    "description": f"Find all {hub_name.lower()} tools.",
                    "score": 8,
                }
            ]
        return []

    # Hub page link builders

    def _get_hub_converters(self, hub_slug: str) -> list[dict[str, Any]]:
        """Find converters for this hub."""
        category_map = {
            "image-conversion": "image",
            "pdf-conversion": "pdf",
            "document-conversion": "document",
            "audio-conversion": "audio",
            "video-conversion": "video",
        }

        category = category_map.get(hub_slug)
        if category:
            converters = self.converter_registry_service.get_by_category(category)
            return self._score_and_format_converters(converters[:8], "")
        return []

    def _get_hub_formats(self, hub_slug: str) -> list[dict[str, Any]]:
        """Find format pages for this hub."""
        format_by_hub = {
            "image-conversion": ["png", "jpg", "webp", "gif"],
            "pdf-conversion": ["pdf"],
            "document-conversion": ["docx", "pdf", "txt"],
            "audio-conversion": ["mp3", "wav", "ogg"],
            "video-conversion": ["mp4", "mov", "avi"],
        }

        formats = format_by_hub.get(hub_slug, [])
        result = []

        for fmt in formats[:4]:
            result.append({
                "title": f"{fmt.upper()} format",
                "href": f"/formats/{fmt.lower()}",
                "description": f"Learn about {fmt.upper()} format specifications.",
                "score": 7,
            })

        return result

    def _get_hub_comparisons(self, hub_slug: str) -> list[dict[str, Any]]:
        """Find comparison pages for this hub."""
        hub_comparisons = {
            "image-conversion": [("png", "jpg"), ("webp", "png")],
            "audio-conversion": [("mp3", "wav")],
            "video-conversion": [("mp4", "mov")],
            "document-conversion": [("pdf", "docx")],
        }

        comparisons = hub_comparisons.get(hub_slug, [])
        result = []

        for fmt1, fmt2 in comparisons:
            result.append({
                "title": f"{fmt1.upper()} vs {fmt2.upper()}",
                "href": f"/{fmt1}-vs-{fmt2}",
                "description": f"Compare {fmt1.upper()} and {fmt2.upper()} formats.",
                "score": 7,
            })

        return result

    def _get_hub_knowledge(self, hub_slug: str) -> list[dict[str, Any]]:
        """Find knowledge pages for this hub."""
        knowledge_by_hub = {
            "image-conversion": ["Image optimization", "Compression basics"],
            "audio-conversion": ["Audio encoding", "Codec comparison"],
            "video-conversion": ["Video transcoding", "Bitrate optimization"],
            "document-conversion": ["Document formats", "PDF standards"],
        }

        topics = knowledge_by_hub.get(hub_slug, [])
        result = []

        for idx, topic in enumerate(topics[:2]):
            result.append({
                "title": topic,
                "href": f"/knowledge/{hub_slug}/topic-{idx + 1}",
                "description": f"Learn about {topic.lower()} for {hub_slug.replace('-', ' ')}.",
                "score": 6,
            })

        return result

    # Utility methods

    def _get_comparison_specs(self, slug: str) -> dict[str, Any]:
        """Get comparison specs for a slug."""
        specs = {
            "pdf-vs-docx": {"title": "PDF vs DOCX", "source_format": "pdf", "target_format": "docx"},
            "png-vs-jpg": {"title": "PNG vs JPG", "source_format": "png", "target_format": "jpg"},
            "webp-vs-png": {"title": "WebP vs PNG", "source_format": "webp", "target_format": "png"},
            "mp4-vs-mov": {"title": "MP4 vs MOV", "source_format": "mp4", "target_format": "mov"},
            "mp3-vs-wav": {"title": "MP3 vs WAV", "source_format": "mp3", "target_format": "wav"},
        }
        if slug not in specs:
            raise ValueError(f"Unknown comparison slug: {slug}")
        return specs[slug]

    def _score_and_format_converters(self, converters: list[dict[str, Any]], exclude_slug: str = "") -> list[dict[str, Any]]:
        """Format converters with score for display."""
        result = []
        for converter in converters:
            if converter.get("slug") == exclude_slug:
                continue
            result.append({
                "title": converter.get("name", converter.get("slug", "")),
                "href": f"/tools/{converter.get('slug', '')}",
                "description": converter.get("description", "Convert files with this tool."),
                "score": 8,
            })
        return result

    def _deduplicate_links(self, links: dict[str, list[dict[str, Any]]]) -> dict[str, list[dict[str, Any]]]:
        """Remove duplicate links across categories."""
        seen_hrefs = set()
        deduplicated = {}

        # Sort by score to keep highest-scoring links
        all_links = []
        for category, link_list in links.items():
            for link in link_list:
                all_links.append((category, link))

        all_links.sort(key=lambda x: x[1].get("score", 0), reverse=True)

        for category, link in all_links:
            href = link.get("href", "")
            if href and href not in seen_hrefs:
                if category not in deduplicated:
                    deduplicated[category] = []
                deduplicated[category].append(link)
                seen_hrefs.add(href)

        return deduplicated

    def _empty_links(self) -> dict[str, list[dict[str, Any]]]:
        """Return empty links structure."""
        return {
            "related_converters": [],
            "related_formats": [],
            "related_comparisons": [],
            "related_knowledge": [],
            "related_hubs": [],
            "related_articles": [],
        }

    def build_internal_link_coverage_report(self) -> dict[str, Any]:
        """Generate report on internal linking coverage across all pages."""
        converters = self.converter_registry_service.get_active()
        comparison_slugs = ["pdf-vs-docx", "png-vs-jpg", "webp-vs-png", "mp4-vs-mov", "mp3-vs-wav"]
        formats = set()

        # Collect all formats
        for converter in converters:
            formats.update(str(f).lower() for f in (converter.get("input_formats") or []))
            formats.update(str(f).lower() for f in (converter.get("output_formats") or []))

        total_pages = len(converters) + len(comparison_slugs) + len(formats)

        # Check coverage
        landing_with_links = 0
        comparison_with_links = 0
        format_with_links = 0
        orphan_pages = 0

        for converter in converters:
            links = self.get_links_for_landing(converter.get("slug", ""), converter)
            if any(links.get(category, []) for category in links):
                landing_with_links += 1
            else:
                orphan_pages += 1

        for slug in comparison_slugs:
            links = self.get_links_for_comparison(slug)
            if any(links.get(category, []) for category in links):
                comparison_with_links += 1
            else:
                orphan_pages += 1

        for fmt in sorted(formats):
            links = self.get_links_for_format(fmt)
            if any(links.get(category, []) for category in links):
                format_with_links += 1
            else:
                orphan_pages += 1

        total_with_links = landing_with_links + comparison_with_links + format_with_links

        return {
            "total_pages": total_pages,
            "pages_with_internal_links": total_with_links,
            "internal_links_coverage_percentage": round((total_with_links / total_pages * 100) if total_pages > 0 else 0, 2),
            "landing_pages_with_links": landing_with_links,
            "comparison_pages_with_links": comparison_with_links,
            "format_pages_with_links": format_with_links,
            "orphan_pages": orphan_pages,
            "avg_internal_links_per_page": round(total_with_links / total_pages if total_pages > 0 else 0, 2),
        }
