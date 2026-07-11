from __future__ import annotations

from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from app.services.converter_data_service import ConverterDataService


class SeoService:
    def __init__(self, data_dir: Path) -> None:
        self.data_service = ConverterDataService(data_dir)

    def _build_base_url(self, request: Any) -> str:
        """
        Build canonical base URL.

        Railway runs behind a reverse proxy.
        The original request scheme may appear as HTTP internally,
        while the public URL is HTTPS.

        Uses x-forwarded-proto when available.
        """

        forwarded_proto = request.headers.get("x-forwarded-proto")

        if forwarded_proto:
            scheme = forwarded_proto.split(",")[0].strip()
        else:
            scheme = request.url.scheme

        hostname = request.url.hostname

        base_url = f"{scheme}://{hostname}"

        if request.url.port and request.url.port not in (80, 443):
            base_url += f":{request.url.port}"

        return base_url.rstrip("/")

    def build_home_meta(self, request: Any) -> dict[str, str]:
        base_url = self._build_base_url(request)

        return {
            "title": "Converigo | Fast Online File Conversion",
            "description": "Converigo offers fast, secure, and automatic file conversion from video, audio, image, and document formats.",
            "canonical": f"{base_url}/",
            "og_url": f"{base_url}/",
            "og_site_name": "Converigo",
            "og_image": f"{base_url}/static/images/og-home.png",
            "og_image_alt": "Converigo file conversion platform",
            "og_image_width": 1200,
            "og_image_height": 630,
            "og_type": "website",
            "twitter_card": "summary_large_image",
            "twitter_site": "@converigo",
            "twitter_creator": "@converigo",
        }

    def build_tool_meta(
        self,
        request: Any,
        tool_data: dict[str, Any],
    ) -> dict[str, str]:

        base_url = self._build_base_url(request)

        title = (
            tool_data.get("seo", {}).get("title")
            or f"{tool_data['title']} | Converigo"
        )

        description = (
            tool_data.get("seo", {}).get("description")
            or tool_data.get("description", "")
        )

        canonical = (
            tool_data.get("seo", {}).get("canonical")
            or f"{base_url}/tools/{tool_data['slug']}"
        )

        og_image = (
            tool_data.get("seo", {}).get("image")
            or f"{base_url}/static/images/og-default.png"
        )

        return {
            "title": title,
            "description": description,
            "canonical": canonical,
            "og_url": canonical,
            "og_site_name": "Converigo",
            "og_image": og_image,
            "og_image_alt": title,
            "og_image_width": 1200,
            "og_image_height": 630,
            "keywords": tool_data.get("seo", {}).get("keywords", ""),
            "og_type": tool_data.get("seo", {}).get(
                "type",
                "website",
            ),
            "twitter_card": tool_data.get("seo", {}).get(
                "twitter_card",
                "summary_large_image",
            ),
            "twitter_site": "@converigo",
            "twitter_creator": "@converigo",
        }

    def build_sitemap_xml(self, request: Any) -> str:

        base_url = self._build_base_url(request)

        entries = self.data_service.sitemap_entries(base_url)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        for entry in entries:

            loc = escape(str(entry["loc"]))

            lines.append("  <url>")
            lines.append(f"    <loc>{loc}</loc>")

            if "lastmod" in entry:
                lines.append(
                    f"    <lastmod>{escape(str(entry['lastmod']))}</lastmod>"
                )

            lines.append("  </url>")

        lines.append("</urlset>")

        return "\n".join(lines)

    def build_structured_data(
        self,
        request: Any,
        tool_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        base_url = self._build_base_url(request)

        organization = {
            "@type": "Organization",
            "name": "Converigo",
            "url": base_url,
            "logo": f"{base_url}/static/images/convertin-logo.png",
        }

        website = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": base_url,
            "name": "Converigo",
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
                "@graph": [
                    organization,
                    website,
                ],
            }

        breadcrumb_items = [
            {
                "@type": "ListItem",
                "position": 1,
                "name": "Home",
                "item": base_url,
            },
            {
                "@type": "ListItem",
                "position": 2,
                "name": tool_data["title"],
                "item": f"{base_url}/tools/{tool_data['slug']}",
            },
        ]

        faq_items = [
            {
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"],
                },
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

        graph: list[dict[str, Any]] = [
            organization,
            website,
            software_application,
        ]

        if faq_items:
            graph.append(
                {
                    "@type": "FAQPage",
                    "mainEntity": faq_items,
                }
            )

        graph.append(
            {
                "@type": "BreadcrumbList",
                "itemListElement": breadcrumb_items,
            }
        )

        return {
            "@context": "https://schema.org",
            "@graph": graph,
        }