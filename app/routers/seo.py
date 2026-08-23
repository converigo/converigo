from xml.etree import ElementTree as ET

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse, Response

import os
from app.services.public_seo_service import build_public_canonical

router = APIRouter(tags=["seo"])

# Static canonical paths to always include in sitemap (as paths).
_STATIC_PATHS = [
    "/",
    "/about",
    "/privacy-policy",
    "/terms",
    "/contact",
    "/cookies",
    "/pricing",
    "/blog",
    "/blog/how-to-convert-mp4-to-mp3",
    "/blog/jpg-to-pdf-guide",
    "/blog/png-to-jpg-guide",
    "/learning",
    "/tools",
    "/formats",
    "/pdf-vs-docx",
    "/png-vs-jpg",
    "/webp-vs-png",
    "/mp4-vs-mov",
    "/mp3-vs-wav",
    "/image-conversion",
    "/pdf-conversion",
    "/audio-conversion",
    "/video-conversion",
    "/document-conversion",
]


def _collect_public_urls() -> list[str]:
    """Assemble canonical public URLs for the sitemap.

    - Include static trusted paths.
    - Include all converter tool pages from app/data/converters/*.json
    - Include learning article pages from app/data/articles/**/*.json
    """
    urls: list[str] = []

    # Add static canonical paths
    for p in _STATIC_PATHS:
        urls.append(build_public_canonical(p))

    # Add converter tool pages from data files
    conv_dir = os.path.join(os.path.dirname(__file__), "..", "data", "converters")
    conv_dir = os.path.normpath(os.path.join(conv_dir))
    try:
        for fn in sorted(os.listdir(conv_dir)):
            if not fn.endswith('.json'):
                continue
            if fn.endswith('.contract.json') or fn.endswith('.metadata.json'):
                continue
            slug = fn[:-5]
            urls.append(build_public_canonical(f"/tools/{slug}"))
    except FileNotFoundError:
        # If data folder missing, fall back to static set only
        pass

    # Add learning pages by scanning article JSON files
    articles_dir = os.path.join(os.path.dirname(__file__), "..", "data", "articles")
    articles_dir = os.path.normpath(os.path.join(articles_dir))
    try:
        for root_dir, _, files in os.walk(articles_dir):
            for fn in sorted(files):
                if not fn.endswith('.json'):
                    continue
                slug = fn[:-5]
                urls.append(build_public_canonical(f"/learning/{slug}"))
    except FileNotFoundError:
        pass

    # Normalize: remove duplicates while preserving order, filter out legacy patterns
    seen: set[str] = set()
    ordered: list[str] = []
    for u in urls:
        if not u or "?lang=" in u or '/knowledge/' in u:
            continue
        if u in seen:
            continue
        seen.add(u)
        ordered.append(u)

    return ordered


def _build_public_sitemap_xml(urls: list[str]) -> str:
    seen: set[str] = set()
    ordered_urls: list[str] = []
    for url in urls:
        normalized = str(url).strip()
        if not normalized or "?lang=" in normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered_urls.append(normalized)

    root = ET.Element("urlset", {"xmlns": "http://www.sitemaps.org/schemas/sitemap/0.9"})
    for url in ordered_urls:
        url_el = ET.SubElement(root, "url")
        loc_el = ET.SubElement(url_el, "loc")
        loc_el.text = url

    return ET.tostring(root, encoding="utf-8", xml_declaration=True).decode("utf-8")


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    urls = _collect_public_urls()
    xml = _build_public_sitemap_xml(urls)
    return Response(content=xml, media_type="application/xml", status_code=200)


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    robots_content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        "Sitemap: https://converigo.com/sitemap.xml\n"
    )
    return PlainTextResponse(robots_content)
