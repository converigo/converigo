from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from app.services.converter_data_service import ConverterDataService


class SeoService:
    def __init__(self, data_dir: Path) -> None:
        self.data_service = ConverterDataService(data_dir)

    def _build_base_url(self, request: Any) -> str:
        base_url = f"{request.url.scheme}://{request.url.hostname}"
        if request.url.port:
            base_url += f":{request.url.port}"
        return base_url.rstrip("/")

    def build_home_meta(self, request: Any) -> dict[str, str]:
        base_url = self._build_base_url(request)
        return {
            "title": "Convertin | Fast Online File Conversion",
            "description": "Convertin offers fast, secure, and automatic file conversion from video, audio, image, and document formats.",
            "canonical": f"{base_url}/",
            "og_url": f"{base_url}/",
            "og_image": f"{base_url}/static/images/og-home.png",
            "og_type": "website",
            "twitter_card": "summary_large_image",
        }

    def build_tool_meta(self, request: Any, tool_data: dict[str, Any]) -> dict[str, str]:
        base_url = self._build_base_url(request)
        title = tool_data.get("seo", {}).get("title") or f"{tool_data['title']} | Convertin"
        description = tool_data.get("seo", {}).get("description") or tool_data.get("description", "")
        canonical = tool_data.get("seo", {}).get("canonical") or f"{base_url}/tools/{tool_data['slug']}"
        og_image = tool_data.get("seo", {}).get("image") or f"{base_url}/static/images/og-default.png"
        return {
            "title": title,
            "description": description,
            "canonical": canonical,
            "og_url": canonical,
            "og_image": og_image,
            "keywords": tool_data.get("seo", {}).get("keywords", ""),
            "og_type": tool_data.get("seo", {}).get("type", "website"),
            "twitter_card": tool_data.get("seo", {}).get("twitter_card", "summary_large_image"),
        }

    def build_structured_data(self, request: Any, tool_data: dict[str, Any] | None = None) -> dict[str, Any]:
        base_url = self._build_base_url(request)
        organization = {
            "@type": "Organization",
            "name": "Convertin",
            "url": base_url,
            "logo": f"{base_url}/static/images/logo.png",
        }

        website = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": base_url,
            "name": "Convertin",
            "publisher": organization,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{base_url}/tools/{{search_term}}",
                "query-input": "required name=search_term",
            },
        }

        if tool_data is None:
            return {
                "@context": "https://schema.org",
                "@graph": [organization, website],
            }

        breadcrumb_items = [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": base_url},
            {"@type": "ListItem", "position": 2, "name": tool_data["title"], "item": f"{base_url}/tools/{tool_data['slug']}"},
        ]

        faq_items = [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {"@type": "Answer", "text": faq["answer"]},
            }
            for faq in tool_data.get("faq", [])
        ]

        software_application = {
            "@type": "SoftwareApplication",
            "name": tool_data["title"],
            "operatingSystem": "Web",
            "applicationCategory": "Utilities",
            "url": f"{base_url}/tools/{tool_data['slug']}",
            "description": tool_data.get("description", ""),
        }

        graph: list[dict[str, Any]] = [organization, website, software_application]
        if faq_items:
            graph.append({"@type": "FAQPage", "mainEntity": faq_items})
        graph.append({"@type": "BreadcrumbList", "itemListElement": breadcrumb_items})

        return {
            "@context": "https://schema.org",
            "@graph": graph,
        }
