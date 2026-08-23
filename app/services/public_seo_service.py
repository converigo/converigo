from __future__ import annotations

from urllib.parse import urlsplit

PRODUCTION_BASE_URL = "https://converigo.com"
DEFAULT_HREFLANG_LOCALES = ["en", "id", "es", "fr", "ja"]


def _normalize_path(path: str) -> str:
    if not path:
        return "/"

    candidate = path.strip()
    if candidate.startswith("http://") or candidate.startswith("https://"):
        candidate = urlsplit(candidate).path or "/"

    candidate = urlsplit(candidate).path or "/"
    if candidate == "":
        return "/"
    return candidate if candidate.startswith("/") else f"/{candidate}"


def build_public_canonical(path: str) -> str:
    normalized = _normalize_path(path)
    return f"{PRODUCTION_BASE_URL}{normalized}"


def build_public_hreflang_links(path: str, locales: list[str] | None = None) -> list[dict[str, str]]:
    normalized = _normalize_path(path)
    base = f"{PRODUCTION_BASE_URL}{normalized}"
    links: list[dict[str, str]] = []
    for locale in (locales or DEFAULT_HREFLANG_LOCALES):
        links.append({"locale": locale, "href": base})
    links.append({"locale": "x-default", "href": base})
    return links


def build_public_breadcrumb_list(items: list[dict[str, str]]) -> dict[str, str | list[dict[str, str | int]]]:
    breadcrumb_items: list[dict[str, str | int]] = []
    for index, item in enumerate(items, start=1):
        url = str(item.get("url", "/")).strip()
        breadcrumb_items.append({
            "@type": "ListItem",
            "position": index,
            "name": str(item.get("name", "Home")),
            "item": build_public_canonical(url),
        })
    return {
        "@type": "BreadcrumbList",
        "itemListElement": breadcrumb_items,
    }


def build_public_structured_data(
    path: str,
    title: str,
    description: str,
    *,
    schema_type: str = "WebSite",
    breadcrumbs: list[dict[str, str]] | None = None,
    faq_items: list[dict[str, str]] | None = None,
) -> dict[str, str | dict[str, str] | list[dict[str, str | int]] | dict[str, str | list[dict[str, str | int]]]]:
    canonical = build_public_canonical(path)

    base_graph: list[dict[str, object]] = [
        {
            "@type": schema_type,
            "name": title,
            "url": canonical,
            "description": description,
        }
    ]

    if schema_type == "WebSite" or path == "/":
        base_graph = [
            {
                "@type": "Organization",
                "name": "Converigo",
                "url": PRODUCTION_BASE_URL,
                "logo": f"{PRODUCTION_BASE_URL}/static/images/converigo-logo.png",
            },
            {
                "@type": "WebSite",
                "name": "Converigo",
                "url": canonical,
                "description": description,
                "publisher": {"@type": "Organization", "name": "Converigo"},
            },
        ]

    if schema_type == "Article":
        base_graph[0]["headline"] = title
        base_graph[0]["author"] = {"@type": "Organization", "name": "Converigo"}

    if breadcrumbs:
        base_graph.append(build_public_breadcrumb_list(breadcrumbs))

    if faq_items:
        base_graph.append({
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item.get("answer", ""),
                    },
                }
                for item in faq_items
                if item.get("question") and item.get("answer")
            ],
        })

    if schema_type == "WebPage" and path.startswith("/tools/"):
        base_graph.append({
            "@type": "SoftwareApplication",
            "name": title,
            "description": description,
            "url": canonical,
            "applicationCategory": "Utility",
            "operatingSystem": "Web",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
            },
        })

    if schema_type == "WebSite" or path == "/" or breadcrumbs or faq_items:
        return {"@context": "https://schema.org", "@graph": base_graph}

    payload: dict[str, str | dict[str, str] | list[dict[str, str | int]] | dict[str, str | list[dict[str, str | int]]]] = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "name": title,
        "url": canonical,
        "description": description,
    }
    if schema_type == "Article":
        payload["headline"] = title
        payload["author"] = {"@type": "Organization", "name": "Converigo"}
    return payload


def build_public_page_seo(
    path: str,
    title: str,
    description: str,
    *,
    schema_type: str = "WebPage",
    site_name: str = "Converigo",
    keywords: str | None = None,
    author: str = "Converigo",
    robots: str = "index,follow",
    og_image: str | None = None,
    og_type: str = "website",
    breadcrumbs: list[dict[str, str]] | None = None,
    faq_items: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    canonical = build_public_canonical(path)
    og_image_url = og_image or f"{PRODUCTION_BASE_URL}/static/images/converigo-og-image.png"
    meta = {
        "title": title,
        "description": description,
        "canonical": canonical,
        "og_url": canonical,
        "og_site_name": site_name,
        "og_image": og_image_url,
        "og_image_alt": title,
        "og_image_width": "1200",
        "og_image_height": "630",
        "og_type": og_type,
        "twitter_card": "summary_large_image",
        "twitter_site": "@converigo",
        "twitter_creator": "@converigo",
        "keywords": keywords or "convert files, file conversion, online converter, convert video, convert image",
        "author": author,
        "robots": robots,
        "hreflang": build_public_hreflang_links(path),
        "x_default": canonical,
        "breadcrumbs": breadcrumbs or [],
    }
    structured_data = build_public_structured_data(path, title, description, schema_type=schema_type, breadcrumbs=breadcrumbs, faq_items=faq_items)
    meta["structured_data"] = structured_data
    return {
        "meta": meta,
        "structured_data": structured_data,
    }


def build_public_meta(
    path: str,
    title: str,
    description: str,
    *,
    site_name: str = "Converigo",
    keywords: str | None = None,
    author: str = "Converigo",
    robots: str = "index,follow",
    og_image: str | None = None,
    og_type: str = "website",
    breadcrumbs: list[dict[str, str]] | None = None,
) -> dict[str, object]:
    return build_public_page_seo(
        path,
        title,
        description,
        schema_type="WebPage",
        site_name=site_name,
        keywords=keywords,
        author=author,
        robots=robots,
        og_image=og_image,
        og_type=og_type,
        breadcrumbs=breadcrumbs,
    )["meta"]
