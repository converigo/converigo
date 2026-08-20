from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from app.services.article_service import ArticleService
from app.services.converter_data_service import ConverterDataService

PRODUCTION_BASE_URL = "https://converigo.com"


class SeoService:
    def __init__(self, data_dir: Path) -> None:
        self.data_service = ConverterDataService(data_dir)
        self.article_service = ArticleService(Path("app/data/articles"))

    def _build_base_url(self, request: Any) -> str:
        """
        Build canonical base URL.

        Production SEO should use the public domain consistently.
        """

        return PRODUCTION_BASE_URL.rstrip("/")

    def build_home_meta(self, request: Any) -> dict[str, str]:
        base_url = self._build_base_url(request)

        # Determine locale language code from request.state.locale (LanguageService sets 'lang_code')
        lang_code = "en"
        try:
            locale_obj = getattr(request.state, "locale", None)
            if isinstance(locale_obj, dict):
                lang_code = locale_obj.get("lang_code") or lang_code
            else:
                # support attribute access if present
                lang_code = getattr(locale_obj, "lang_code", lang_code) or lang_code
        except Exception:
            lang_code = "en"

        # Localized title/description: prefer existing locale keys where available
        t = getattr(request.state, "t", None)
        if callable(t):
            brand = t("footer.brand", "Converigo")
            heading = t("hero.title", "Convert All Files")
            description = t(
                "hero.description",
                "Converigo offers fast, secure, and automatic file conversion from video, audio, image, and document formats.",
            )
        else:
            brand = "Converigo"
            heading = "Convert All Files"
            description = "Converigo offers fast, secure, and automatic file conversion from video, audio, image, and document formats."

        title = f"{brand} | {heading}"

        # Homepage canonical: use root to align with x-default and non-home pages
        canonical = f"{base_url}/"
        og_url = canonical

        return {
            "title": title,
            "description": description,
            "canonical": canonical,
            "og_url": og_url,
            "og_site_name": brand,
            "og_image": f"{base_url}/static/images/converigo-og-image.png",
            "og_image_alt": "Converigo file conversion platform",
            "og_image_width": 1200,
            "og_image_height": 630,
            "og_type": "website",
            "twitter_card": "summary_large_image",
            "twitter_site": "@converigo",
            "twitter_creator": "@converigo",
            "keywords": "online file converter, file conversion, document conversion, image conversion, audio conversion, video conversion",
            "author": brand,
            "robots": "index,follow",
        }

    def build_tool_meta(
        self,
        request: Any,
        tool_data: dict[str, Any],
        canonical_path: str | None = None,
    ) -> dict[str, str]:

        base_url = self._build_base_url(request)

        slug = tool_data.get("slug", "")
        label = tool_data.get("title", "").replace(" Converter", "").strip()
        seo_meta = tool_data.get("seo", {})

        base_title = tool_data.get("title") or label or slug.replace("-", " ").title()
        if base_title and "converter" not in base_title.lower():
            base_title = f"{base_title} Converter"

        if slug == "mp4-to-mp3":
            title = "MP4 to MP3 | Converigo"
        elif slug in {"pdf-to-jpg", "png-to-jpg"}:
            title = f"{base_title} Online Free"
        else:
            title = f"{base_title} Online Free - Converigo"

        source = (tool_data.get("source") or slug.split("-to-")[0] if "-to-" in slug else "").strip()
        target = (tool_data.get("target") or slug.split("-to-")[1] if "-to-" in slug else "").strip()
        source_display = source.upper() if source else ""
        target_display = target.upper() if target else ""

        if slug == "mp4-to-mp3":
            description = "Convert MP4 to MP3 Online Free"
        elif source == "pdf" and target in {"jpg", "jpeg"}:
            description = "Convert PDF files to JPG images online free"
        elif source == "png" and target == "jpg":
            description = "Convert PNG images to JPG online free"
        elif source_display and target_display:
            description = f"Convert {source_display} to {target_display} online free"
        else:
            description = tool_data.get("description") or seo_meta.get("description") or f"Convert {label} online free"

        canonical = self._resolve_url(
            base_url,
            canonical_path or f"/tools/{tool_data['slug']}",
        )

        og_image = seo_meta.get("image") or f"{base_url}/static/images/og-default.png"
        og_image_alt = seo_meta.get("og_image_alt") or title
        twitter_title = seo_meta.get("twitter_title") or title
        twitter_description = seo_meta.get("twitter_description") or description
        twitter_image = seo_meta.get("twitter_image") or og_image

        return {
            "title": title or seo_meta.get("title"),
            "description": description or seo_meta.get("description"),
            "canonical": canonical,
            "og_url": canonical,
            "og_site_name": "Converigo",
            "og_image": og_image,
            "og_image_alt": og_image_alt,
            "og_image_width": 1200,
            "og_image_height": 630,
            "keywords": seo_meta.get("keywords", ""),
            "og_type": seo_meta.get("type", "website"),
            "twitter_card": seo_meta.get("twitter_card", "summary_large_image"),
            "twitter_title": twitter_title,
            "twitter_description": twitter_description,
            "twitter_image": twitter_image,
            "twitter_site": "@converigo",
            "twitter_creator": "@converigo",
            "author": "Converigo",
            "robots": "index,follow",
        }

    def _build_blog_entries(self, base_url: str) -> list[dict[str, str]]:
        today = datetime.utcnow().date().isoformat()
        paths = [
            "/blog",
            "/blog/how-to-convert-mp4-to-mp3",
            "/blog/jpg-to-pdf-guide",
            "/blog/png-to-jpg-guide",
        ]

        return [
            {
                "loc": base_url.rstrip("/") + path,
                "lastmod": today,
            }
            for path in paths
        ]

    def _build_learning_entries(self, base_url: str) -> list[dict[str, str]]:
        today = datetime.utcnow().date().isoformat()
        articles = self.article_service.list_articles()
        entries: list[dict[str, str]] = []

        if articles:
            entries.append({"loc": base_url.rstrip("/") + "/learning", "lastmod": today})

        for article in articles:
            slug = str(article.get("slug", "")).strip()
            if not slug:
                continue
            entries.append({"loc": base_url.rstrip("/") + f"/learning/{slug}", "lastmod": today})

        return entries

    def build_sitemap_xml(self, request: Any) -> str:

        base_url = self._build_base_url(request)

        entries = self.data_service.sitemap_entries(base_url)
        entries.extend(self._build_blog_entries(base_url))
        entries.extend(self._build_learning_entries(base_url))

        deduped_entries: list[dict[str, str]] = []
        seen_locs: set[str] = set()
        for entry in entries:
            loc = str(entry.get("loc", "")).strip()
            if not loc or loc in seen_locs:
                continue
            seen_locs.add(loc)
            deduped_entries.append(entry)

        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]

        for entry in deduped_entries:

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

    def _normalize_url(self, base_url: str, path: str) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return base_url.rstrip("/") + path

    def _resolve_url(self, base_url: str, path: str | None) -> str:
        if not path:
            return base_url
        if path.startswith("http://") or path.startswith("https://"):
            return path
        return base_url.rstrip("/") + (path if path.startswith("/") else f"/{path}")

    def _build_breadcrumb_list(self, base_url: str, items: list[dict[str, str]]) -> dict[str, Any]:
        return {
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": index + 1,
                    "name": item["name"],
                    "item": self._normalize_url(base_url, item["url"]),
                }
                for index, item in enumerate(items)
            ],
        }

    def build_structured_data(
        self,
        request: Any,
        tool_data: dict[str, Any] | None = None,
        page_type: str | None = None,
        page_data: dict[str, Any] | None = None,
        canonical_path: str | None = None,
    ) -> dict[str, Any]:

        request_state = getattr(request, "state", None) if request is not None else None
        base_url = self._build_base_url(request)

        organization = {
            "@type": "Organization",
            "name": "Converigo",
            "url": base_url,
            "logo": f"{base_url}/static/images/converigo-logo.png",
        }

        # Determine locale language code (if available) to use localized site URL
        lang_code = "en"
        try:
            locale_obj = getattr(request_state, "locale", None)
            if isinstance(locale_obj, dict):
                lang_code = locale_obj.get("lang_code") or lang_code
            else:
                lang_code = getattr(locale_obj, "lang_code", lang_code) or lang_code
        except Exception:
            lang_code = "en"

        t = getattr(request_state, "t", None) if request_state is not None else None
        if callable(t):
            site_name = t("footer.brand", "Converigo")
            site_description = t("hero.description", "")
        else:
            site_name = "Converigo"
            site_description = ""

        website = {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "url": f"{base_url}/?lang={lang_code}",
            "name": site_name,
            "description": site_description,
            "publisher": organization,
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{base_url}/tools/{{search_term}}",
                "query-input": "required name=search_term",
            },
        }

        if tool_data is None and page_type is None:
            faq_items = [
                {
                    "@type": "Question",
                    "name": "What is Converigo?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Converigo is a fast online file converter that helps you convert documents, images, audio, and video files without installing software.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "Is Converigo free?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Yes, Converigo offers free file conversion so you can quickly transform files without paying for basic conversion tasks.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "Are uploaded files safe?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Uploaded files are processed securely and kept only as long as needed to complete the conversion, with privacy and safety in mind.",
                    },
                },
                {
                    "@type": "Question",
                    "name": "What files can Converigo convert?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Converigo supports many popular formats for images, documents, audio, and video, so you can convert the files you need quickly.",
                    },
                },
            ]

            graph = [
                organization,
                website,
                {
                    "@type": "FAQPage",
                    "mainEntity": faq_items,
                },
            ]

            if page_data and page_data.get("breadcrumb"):
                graph.append(self._build_breadcrumb_list(base_url, page_data["breadcrumb"]))

            return {
                "@context": "https://schema.org",
                "@graph": graph,
            }

        if page_type == "blog_index" and page_data is not None:
            blog_posts: list[dict[str, Any]] = []
            for article in page_data.get("articles", []):
                post = {
                    "@type": "BlogPosting",
                    "headline": article["title"],
                    "description": article["description"],
                    "url": self._normalize_url(base_url, f"/blog/{article['slug']}"),
                    "author": {"@type": "Organization", "name": "Converigo"},
                }
                if article.get("datePublished"):
                    post["datePublished"] = article["datePublished"]
                if article.get("dateModified"):
                    post["dateModified"] = article["dateModified"]
                blog_posts.append(post)

            graph = [
                organization,
                website,
                {
                    "@type": "Blog",
                    "name": page_data.get("name", "Converigo Blog"),
                    "description": page_data.get("description", ""),
                    "url": self._normalize_url(base_url, page_data.get("url", "/blog")),
                    "publisher": organization,
                    "blogPost": blog_posts,
                },
                self._build_breadcrumb_list(
                    base_url,
                    [{"name": "Home", "url": "/"}, {"name": "Blog", "url": "/blog"}],
                ),
            ]

            return {
                "@context": "https://schema.org",
                "@graph": graph,
            }

        if page_type == "blog_article" and page_data is not None:
            graph = [
                organization,
                website,
                {
                    "@type": "BlogPosting",
                    "headline": page_data.get("headline", ""),
                    "description": page_data.get("description", ""),
                    "url": self._normalize_url(base_url, page_data.get("url", "")),
                    "mainEntityOfPage": {
                        "@type": "WebPage",
                        "@id": self._normalize_url(base_url, page_data.get("url", "")),
                    },
                    "author": {"@type": "Organization", "name": "Converigo"},
                    "publisher": organization,
                },
                self._build_breadcrumb_list(
                    base_url,
                    page_data.get(
                        "breadcrumb",
                        [{"name": "Home", "url": "/"}, {"name": "Blog", "url": "/blog"}],
                    ),
                ),
            ]

            return {
                "@context": "https://schema.org",
                "@graph": graph,
            }

        if page_type == "trust_page" and page_data is not None:
            title = page_data.get("name", page_data.get("title", ""))
            faq_items_source = page_data.get("faq_items") or page_data.get("faq") or []
            faq_items = [
                {
                    "@type": "Question",
                    "name": item.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item.get("answer", ""),
                    },
                }
                for item in faq_items_source
                if isinstance(item, dict) and item.get("question") and item.get("answer")
            ]

            graph = [
                organization,
                website,
                {
                    "@type": "WebPage",
                    "name": title,
                    "description": page_data.get("description", ""),
                    "url": self._normalize_url(base_url, page_data.get("url", "")),
                    "publisher": organization,
                },
                self._build_breadcrumb_list(
                    base_url,
                    [{"name": "Home", "url": "/"}, {"name": title, "url": page_data.get("url", "")}],
                ),
            ]

            if faq_items:
                graph.append(
                    {
                        "@type": "FAQPage",
                        "mainEntity": faq_items,
                    }
                )

            return {
                "@context": "https://schema.org",
                "@graph": graph,
            }

        tool_url = self._resolve_url(base_url, canonical_path or f"/tools/{tool_data['slug']}")

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
                "item": tool_url,
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
            "url": tool_url,
            "description": tool_data.get("description", ""),
        }

        graph: list[dict[str, Any]] = [
            organization,
            website,
            software_application,
        ]

        if tool_data.get("seo", {}).get("keywords"):
            software_application["keywords"] = tool_data["seo"]["keywords"]

        if faq_items:
            graph.append(
                {
                    "@type": "FAQPage",
                    "mainEntity": faq_items,
                }
            )

        source = str(tool_data.get("source") or "").strip().upper()
        target = str(tool_data.get("target") or "").strip().upper()
        if source and target:
            graph.append(
                {
                    "@type": "HowTo",
                    "name": f"How to convert {source} to {target}",
                    "step": [
                        {
                            "@type": "HowToStep",
                            "position": 1,
                            "name": f"Upload your {source} file",
                            "text": f"Upload your {source} file",
                        },
                        {
                            "@type": "HowToStep",
                            "position": 2,
                            "name": "Click the convert button",
                            "text": "Click the convert button",
                        },
                        {
                            "@type": "HowToStep",
                            "position": 3,
                            "name": f"Download your converted {target} file",
                            "text": f"Download your converted {target} file",
                        },
                    ],
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