"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.services.converter_data_service import ConverterDataService
from app.services.hub_service import HubService
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService
from app.routers.tools import render_universal_tool_page

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


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(
            locale_data,
            key,
            default,
        )

    popular = converter_data_service.list_popular_converters(
        limit=6
    )

    latest = converter_data_service.list_latest_converters(
        limit=4
    )

    metadata = seo_service.build_home_meta(request)
    _, _, supported_locales = _get_locale_context(request)

    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "supported_locales": supported_locales,
            "title": metadata["title"],
            "meta": metadata,
            "featured_converters": popular[:4],
            "popular_converters": popular,
            "latest_converters": latest,
            "structured_data": seo_service.build_structured_data(
                request
            ),
            "year": datetime.utcnow().year,
        },
    )


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


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return await _render_trust_page(
        request,
        "privacy-policy.html",
        "Privacy Policy | Converigo",
        "Read Converigo's privacy policy and understand how we handle your files, analytics, cookies, and uploads.",
        "/privacy",
    )


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


@router.get("/blog", response_class=HTMLResponse)
async def blog_index(request: Request):
    articles = [
        {
            "slug": "how-to-convert-mp4-to-mp3",
            "title": "Cara Convert MP4 ke MP3 Online Gratis Tanpa Aplikasi",
            "description": "Panduan lengkap tentang cara mengubah video MP4 menjadi audio MP3 secara online, cepat, aman, dan tanpa aplikasi tambahan.",
            "category": "Audio",
        },
        {
            "slug": "jpg-to-pdf-guide",
            "title": "Panduan JPG ke PDF: Cara Mengubah Gambar Menjadi PDF dengan Mudah",
            "description": "Pelajari langkah-langkah mengonversi file JPG ke PDF secara online untuk dokumen, portofolio, dan arsip.",
            "category": "Documents",
        },
        {
            "slug": "png-to-jpg-guide",
            "title": "Panduan PNG ke JPG: Ubah Gambar Transparan Menjadi JPG tanpa Ribet",
            "description": "Temukan cara mengubah file PNG ke JPG online dengan hasil yang tajam dan cepat untuk kebutuhan sehari-hari.",
            "category": "Images",
        },
    ]

    metadata = {
        "title": "Blog Converigo | Panduan Konversi File dan Tips SEO",
        "description": "Temukan panduan praktis, tips konversi file, dan artikel SEO tentang alat online Converigo.",
        "canonical": f"{PRODUCTION_BASE_URL}/blog",
        "og_url": f"{PRODUCTION_BASE_URL}/blog",
        "keywords": "blog converigo, panduan convert file, tips konversi online",
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
            "title": "Cara Convert MP4 ke MP3 Online Gratis Tanpa Aplikasi",
            "description": "Panduan lengkap cara mengonversi MP4 ke MP3 secara online gratis dengan hasil yang cepat, aman, dan praktis.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/how-to-convert-mp4-to-mp3",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/how-to-convert-mp4-to-mp3",
            "template": "pages/blog_mp4_to_mp3.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "Cara Convert MP4 ke MP3 Online Gratis Tanpa Aplikasi", "url": "/blog/how-to-convert-mp4-to-mp3"},
            ],
        },
        "jpg-to-pdf-guide": {
            "title": "Panduan JPG ke PDF: Cara Mengubah Gambar Menjadi PDF dengan Mudah",
            "description": "Pelajari langkah mudah mengubah JPG ke PDF online secara gratis untuk dokumen, portofolio, dan arsip digital.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/jpg-to-pdf-guide",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/jpg-to-pdf-guide",
            "template": "pages/blog_jpg_to_pdf.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "Panduan JPG ke PDF", "url": "/blog/jpg-to-pdf-guide"},
            ],
        },
        "png-to-jpg-guide": {
            "title": "Panduan PNG ke JPG: Ubah Gambar Transparan Menjadi JPG tanpa Ribet",
            "description": "Pelajari cara mengubah PNG ke JPG online untuk kebutuhan desain, dokumen, dan berbagi gambar secara lebih luas.",
            "canonical": f"{PRODUCTION_BASE_URL}/blog/png-to-jpg-guide",
            "og_url": f"{PRODUCTION_BASE_URL}/blog/png-to-jpg-guide",
            "template": "pages/blog_png_to_jpg.html",
            "breadcrumb": [
                {"name": "Home", "url": "/"},
                {"name": "Blog", "url": "/blog"},
                {"name": "Panduan PNG ke JPG", "url": "/blog/png-to-jpg-guide"},
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
        "keywords": "blog converigo, panduan konversi file, converter online",
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
    return await render_universal_tool_page(request, "mp4-to-mp3", canonical_path="/mp4-to-mp3")


@router.get("/jpg-to-png", response_class=HTMLResponse)
async def jpg_to_png_landing(request: Request):
    return await render_universal_tool_page(request, "jpg-to-png", canonical_path="/jpg-to-png")


@router.get("/png-to-jpg", response_class=HTMLResponse)
async def png_to_jpg_landing(request: Request):
    return await render_universal_tool_page(request, "png-to-jpg", canonical_path="/png-to-jpg")


@router.get("/png-to-webp", response_class=HTMLResponse)
async def png_to_webp_landing(request: Request):
    return await render_universal_tool_page(request, "png-to-webp", canonical_path="/png-to-webp")


@router.get("/webp-to-jpg", response_class=HTMLResponse)
async def webp_to_jpg_landing(request: Request):
    return await render_universal_tool_page(request, "webp-to-jpg", canonical_path="/webp-to-jpg")


@router.get("/webp-to-png", response_class=HTMLResponse)
async def webp_to_png_landing(request: Request):
    return await render_universal_tool_page(request, "webp-to-png", canonical_path="/webp-to-png")


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
    return await render_universal_tool_page(request, "pdf-to-jpg", canonical_path="/pdf-to-jpg")


@router.get("/word-to-pdf", response_class=HTMLResponse)
async def word_to_pdf_landing(request: Request):
    return await render_universal_tool_page(request, "word-to-pdf", canonical_path="/word-to-pdf")


@router.get("/jpg-to-pdf", response_class=HTMLResponse)
async def jpg_to_pdf_landing(request: Request):
    return await render_universal_tool_page(request, "jpg-to-pdf", canonical_path="/jpg-to-pdf")


@router.get("/{slug}", response_class=HTMLResponse)
async def universal_converter_route(request: Request, slug: str):
    if slug in RESERVED_PATHS:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        converter_data_service.load_converter_by_slug(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Converter not found")

    return await render_universal_tool_page(request, slug, canonical_path=f"/{slug}")