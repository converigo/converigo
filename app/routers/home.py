"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

import logging
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.core.templates import templates
from app.services.converter_data_service import ConverterDataService
from app.services.hub_service import HubService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService
from app.routers.tools import render_universal_tool_page

logger = logging.getLogger(__name__)
router = APIRouter()

RESERVED_PATHS = {
    "about",
    "privacy-policy",
    "privacy",
    "terms",
    "contact",
    "cookies",
    "blog",
    "image-conversion",
    "sitemap.xml",
    "robots.txt",
    "health",
}

converter_data_service = ConverterDataService(
    Path("app/data/converters")
)

hub_service = HubService(converter_data_service)

seo_service = SeoService(
    Path("app/data/converters")
)

language_service = LanguageService(
    Path("app/locales")
)


def _build_base_url(request: Request) -> str:
    base_url = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.port:
        base_url += f":{request.url.port}"
    return base_url.rstrip("/")


def _get_locale_context(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    return locale_data, t, language_service.get_supported_locales()


async def _render_trust_page(
    request: Request,
    template_name: str,
    title: str,
    description: str,
    canonical_path: str,
) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)
    metadata = {
        "title": title,
        "description": description,
        "canonical": f"{PRODUCTION_BASE_URL}{canonical_path}",
        "og_url": f"{PRODUCTION_BASE_URL}{canonical_path}",
        "keywords": "Converigo, file conversion, online converter, document conversion, image conversion",
        "author": "Converigo",
        "robots": "index,follow",
    }
    return templates.TemplateResponse(
        request=request,
        name=f"pages/{template_name}",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="trust_page",
                page_data={
                    "title": title,
                    "description": description,
                    "url": canonical_path,
                    "name": title,
                },
            ),
            "year": datetime.utcnow().year,
        },
    )


async def _render_not_found_page(request: Request, path: str | None = None) -> HTMLResponse:
    locale_data, t, supported_locales = _get_locale_context(request)
    popular = converter_data_service.list_popular_converters(limit=6)
    metadata = {
        "title": "Page Not Found | Converigo",
        "description": "The page you requested could not be found. Explore popular converters and help articles instead.",
        "canonical": f"{PRODUCTION_BASE_URL}/404",
        "og_url": f"{PRODUCTION_BASE_URL}/404",
        "keywords": "404 page, page not found, converter help",
        "author": "Converigo",
        "robots": "noindex,follow",
    }
    return templates.TemplateResponse(
        request=request,
        name="pages/404.html",
        status_code=404,
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "path": path or "",
            "popular_converters": popular,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="trust_page",
                page_data={
                    "title": metadata["title"],
                    "description": metadata["description"],
                    "url": "/404",
                    "name": "Page Not Found",
                },
            ),
            "year": datetime.utcnow().year,
        },
    )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    locale_data, t, supported_locales = _get_locale_context(request)
    metadata = seo_service.build_home_meta(request)

    # IMPORTANT: Phase B uses the frozen Phase A audit snapshot as the source of truth for
    # which source->target pairs are allowed in the UI. This is intentionally NOT re-derived
    # from the live plugin registry on every request. If registry plugins change later, the
    # audit snapshot must be regenerated manually by rerunning `audit_phase_a_matrix.py` and
    # refreshing the JSON snapshot used here.
    matrix_path = Path(__file__).resolve().parents[1] / "data" / "phase_a_matrix.json"
    phase_a_matrix = []
    if matrix_path.exists():
        try:
            phase_a_matrix = __import__("json").loads(matrix_path.read_text(encoding="utf-8"))
        except Exception:
            phase_a_matrix = []
    else:
        logger.warning("Phase A matrix snapshot missing at %s; fail-closed UI filtering is enabled.", matrix_path)

    return templates.TemplateResponse(
        request=request,
        name="main/converigo_main.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "phase_a_matrix": phase_a_matrix,
            "structured_data": seo_service.build_structured_data(
                request,
                page_data={
                    "name": "Converigo",
                    "description": metadata["description"],
                    "url": "/",
                    "breadcrumb": [{"name": "Home", "url": "/"}],
                },
            ),
            "year": datetime.utcnow().year,
        },
    )


@router.get("/certification")
async def certification():
    return RedirectResponse(url="/", status_code=301)


@router.get("/about", response_class=HTMLResponse)
async def about(request: Request):
    return await _render_trust_page(
        request,
        "about.html",
        "About Converigo | Fast, Free & Secure Online File Converter",
        "Learn about Converigo, our mission, and how we make file conversion simple, fast, and secure.",
        "/about",
    )


@router.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy(request: Request):
    return await _render_trust_page(
        request,
        "privacy-policy.html",
        "Privacy Policy | Converigo",
        "Read Converigo's privacy policy and understand how we handle your files, analytics, cookies, and uploads.",
        "/privacy-policy",
    )


@router.get("/privacy", response_class=RedirectResponse)
async def privacy(request: Request):
    # LD-02: legacy /privacy URL permanently redirects to /privacy-policy.
    # The dedicated template remains in use (served via /privacy-policy).
    return RedirectResponse(url="/privacy-policy", status_code=301)


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return await _render_trust_page(
        request,
        "terms.html",
        "Terms of Service | Converigo",
        "Review Converigo's terms of service and usage guidelines for converting files online.",
        "/terms",
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return await _render_trust_page(
        request,
        "contact.html",
        "Contact Converigo | File Conversion Support",
        "Get in touch with Converigo for support, questions, or feedback about our file conversion tools.",
        "/contact",
    )


@router.get("/cookies", response_class=HTMLResponse)
async def cookies(request: Request):
    return await _render_trust_page(
        request,
        "cookies.html",
        "Cookie Policy | Converigo",
        "Learn how Converigo uses cookies, analytics, and advertising technologies on our website.",
        "/cookies",
    )


@router.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return await _render_trust_page(
        request,
        "pricing.html",
        "Pricing | Converigo",
        "Compare Converigo plans and choose the best option for your file conversion needs.",
        "/pricing",
    )


@router.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    articles = [
        {
            "slug": "how-to-convert-mp4-to-mp3",
            "title": "How to Convert MP4 to MP3 Online for Free (No Apps Needed)",
            "description": "Convert MP4 video to MP3 audio online quickly, safely, and free, with no extra software required.",
            "category": "Audio",
        },
        {
            "slug": "jpg-to-pdf-guide",
            "title": "JPG to PDF Guide: Convert Images to PDF the Easy Way",
            "description": "Learn how to convert JPG images to PDF online for documents, portfolios, and archives.",
            "category": "Documents",
        },
        {
            "slug": "png-to-jpg-guide",
            "title": "PNG to JPG Guide: Convert Transparent PNG to JPG Online",
            "description": "Find out how to convert PNG files to JPG online with sharp, fast results for everyday needs.",
            "category": "Images",
        },
    ]

    metadata = {
        "title": "Converigo Blog | File Conversion Guides and SEO Tips",
        "description": "Find practical guides, file conversion tips, and SEO articles about Converigo's online tools.",
        "canonical": f"{PRODUCTION_BASE_URL}/blog",
        "og_url": f"{PRODUCTION_BASE_URL}/blog",
        "keywords": "converigo blog, file conversion guides, online converter tips",
        "author": "Converigo",
        "robots": "index,follow",
    }

    locale_data, t, supported_locales = _get_locale_context(request)

    return templates.TemplateResponse(
        request=request,
        name="pages/blog_index.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "articles": articles,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="blog_index",
                page_data={
                    "name": "Converigo Blog",
                    "description": metadata["description"],
                    "url": "/blog",
                    "articles": articles,
                },
            ),
            "year": datetime.utcnow().year,
        },
    )


@router.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_article(request: Request, slug: str):
    article_map = {
        "how-to-convert-mp4-to-mp3": {
            "title": "How to Convert MP4 to MP3 Online for Free (No Apps Needed)",
            "description": "A complete guide to converting MP4 to MP3 online for free with fast, safe, and practical results.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/how-to-convert-mp4-to-mp3",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/how-to-convert-mp4-to-mp3",
            "template": "pages/blog_mp4_to_mp3.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "How to Convert MP4 to MP3 Online for Free (No Apps Needed)", "url": "/blog/how-to-convert-mp4-to-mp3"},
            ],
        },
        "jpg-to-pdf-guide": {
            "title": "JPG to PDF Guide: Convert Images to PDF the Easy Way",
            "description": "Learn the easy steps to convert JPG to PDF online for free, ideal for documents, portfolios, and archives.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/jpg-to-pdf-guide",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/jpg-to-pdf-guide",
            "template": "pages/blog_jpg_to_pdf.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "JPG to PDF Guide", "url": "/blog/jpg-to-pdf-guide"},
            ],
        },
        "png-to-jpg-guide": {
            "title": "PNG to JPG Guide: Convert Transparent PNG to JPG Online",
            "description": "Learn how to convert PNG to JPG online for design, documents, and wider image sharing needs.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/png-to-jpg-guide",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/png-to-jpg-guide",
            "template": "pages/blog_png_to_jpg.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "PNG to JPG Guide", "url": "/blog/png-to-jpg-guide"},
            ],
        },
    }

    article = article_map.get(slug)
    if article is None:
        raise HTTPException(status_code=404, detail="Blog article not found")

    locale_data, t, supported_locales = _get_locale_context(request)

    metadata = {
        "title": article["title"],
        "description": article["description"],
        "canonical": article["canonical"],
        "keywords": "converigo blog, file conversion guides, online converter",
        "author": "Converigo",
        "robots": "index,follow",
    }

    return templates.TemplateResponse(
        request=request,
        name=article["template"],
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": metadata,
            "article": article,
            "structured_data": seo_service.build_structured_data(
                request,
                page_type="blog_article",
                page_data={
                    "headline": article["title"],
                    "description": article["description"],
                    "url": article["canonical"].replace(PRODUCTION_BASE_URL, ""),
                    "breadcrumb": article["breadcrumb"],
                },
            ),
            "year": datetime.utcnow().year,
        },
    )


@router.get("/mp4-to-mp3", response_class=HTMLResponse)
async def mp4_to_mp3_landing(request: Request):
    return Response(status_code=410)


@router.get("/jpg-to-png", response_class=HTMLResponse)
async def jpg_to_png_landing(request: Request):
    return Response(status_code=410)


@router.get("/png-to-jpg", response_class=HTMLResponse)
async def png_to_jpg_landing(request: Request):
    return Response(status_code=410)


@router.get("/png-to-webp", response_class=HTMLResponse)
async def png_to_webp_landing(request: Request):
    return Response(status_code=410)


@router.get("/webp-to-jpg", response_class=HTMLResponse)
async def webp_to_jpg_landing(request: Request):
    return Response(status_code=410)


@router.get("/webp-to-png", response_class=HTMLResponse)
async def webp_to_png_landing(request: Request):
    return Response(status_code=410)


@router.get("/image-conversion", response_class=HTMLResponse)
async def image_hub(request: Request):
    return await _render_hub_page(request, "image-conversion")


@router.get("/pdf-conversion", response_class=HTMLResponse)
async def pdf_hub(request: Request):
    return await _render_hub_page(request, "pdf-conversion")


@router.get("/audio-conversion", response_class=HTMLResponse)
async def audio_hub(request: Request):
    return await _render_hub_page(request, "audio-conversion")


@router.get("/video-conversion", response_class=HTMLResponse)
async def video_hub(request: Request):
    return await _render_hub_page(request, "video-conversion")


@router.get("/document-conversion", response_class=HTMLResponse)
async def document_hub(request: Request):
    return await _render_hub_page(request, "document-conversion")


@router.get("/data-conversion", response_class=HTMLResponse)
async def data_hub(request: Request):
    return await _render_hub_page(request, "data-conversion")


async def _render_hub_page(request: Request, slug: str) -> HTMLResponse:
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    page_data = hub_service.get_hub_page_data(slug)
    hub = page_data["hub"]

    faq_items = [
        {
            "question": f"How can I use {hub['title']}?",
            "answer": f"Browse the featured and popular converters in {hub['title']} to find the workflow that matches your file format needs.",
        },
        {
            "question": "Why use a hub page?",
            "answer": "A hub page helps you quickly find the most relevant converter tools and related workflows without searching manually.",
        },
    ]

    meta = {
        "title": f"{hub['title']} | Converigo",
        "description": hub["description"],
        "canonical": f"{PRODUCTION_BASE_URL}{hub['path']}",
        "og_url": f"{PRODUCTION_BASE_URL}{hub['path']}",
        "og_image": f"{PRODUCTION_BASE_URL}/static/images/og-default.png",
        "og_image_alt": f"Converigo {hub['title']}",
        "keywords": hub["keywords"],
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    structured_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{PRODUCTION_BASE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": hub["title"], "item": f"{PRODUCTION_BASE_URL}{hub['path']}"},
                ],
            },
            {
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": item["question"],
                        "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
                    }
                    for item in faq_items
                ],
            },
        ],
    }

    _, _, supported_locales = _get_locale_context(request)

    return templates.TemplateResponse(
        request=request,
        name="components/hub_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "meta": meta,
            "title": hub["title"],
            "structured_data": structured_data,
            "featured_converters": page_data["featured_converters"],
            "featured_tools": page_data["featured_converters"],
            "popular_converters": page_data["popular_converters"],
            "related_converters": page_data["related_converters"],
            "all_converters": page_data["all_converters"],
            "image_tools": page_data["all_converters"],
            "internal_links": page_data["internal_links"],
            "faq_items": faq_items,
            "hub": hub,
            "year": datetime.utcnow().year,
        },
    )


@router.get("/pdf-to-jpg", response_class=HTMLResponse)
async def pdf_to_jpg_landing(request: Request):
    return Response(status_code=410)


@router.get("/word-to-pdf", response_class=HTMLResponse)
async def word_to_pdf_landing(request: Request):
    return Response(status_code=410)


@router.get("/jpg-to-pdf", response_class=HTMLResponse)
async def jpg_to_pdf_landing(request: Request):
    return Response(status_code=410)
