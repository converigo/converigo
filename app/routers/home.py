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
from app.services.language_service import LanguageService
from app.services.seo_service import PRODUCTION_BASE_URL, SeoService

router = APIRouter()

converter_data_service = ConverterDataService(
    Path("app/data/converters")
)

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
        "About Converigo | Fast Online File Conversion",
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
            "year": datetime.utcnow().year,
        },
    )


@router.get("/mp4-to-mp3", response_class=HTMLResponse)
async def mp4_to_mp3_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("mp4-to-mp3")
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)
    seo_data = seo_service.build_tool_meta(request, tool_data)

    faq_items = [
        {
            "question": "What is MP4 to MP3 conversion?",
            "answer": "MP4 to MP3 conversion extracts the audio track from a video file and saves it as a standalone MP3 audio file.",
        },
        {
            "question": "How do I convert MP4 to MP3?",
            "answer": "Upload your MP4 video, choose MP3 as the output, and download the converted audio once the process finishes.",
        },
        {
            "question": "Is Converigo free?",
            "answer": "Yes. Converigo lets you convert MP4 to MP3 online free for quick audio extraction.",
        },
        {
            "question": "What file types can I upload?",
            "answer": "Upload MP4 video files only, and Converigo will extract the MP3 audio track.",
        },
    ]

    supported_formats = [
        {"label": "Input format", "value": tool_data.get("source", "MP4").upper()},
        {"label": "Output format", "value": tool_data.get("target", "MP3").upper()},
    ]

    how_to_use = [
        {
            "step": "1",
            "title": "Upload your MP4",
            "description": "Choose an MP4 video file from your device or drag it into the converter.",
        },
        {
            "step": "2",
            "title": "Convert to MP3",
            "description": "Start the conversion and let Converigo process the audio track securely.",
        },
        {
            "step": "3",
            "title": "Download MP3",
            "description": "Download your MP3 file instantly once the conversion is complete.",
        },
    ]

    return templates.TemplateResponse(
        request=request,
        name="pages/mp4_to_mp3_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": seo_data,
            "title": seo_data["title"],
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Fast conversion", "text": "Convert your MP4 videos to MP3 in seconds without installing software."},
                {"title": "Secure processing", "text": "Your files are handled safely and kept private during conversion."},
                {"title": "High-quality audio", "text": "Extract clean MP3 audio from your video while preserving sound clarity."},
            ],
            "supported_formats": supported_formats,
            "how_to_use": how_to_use,
            "related_tools": related_tools,
            "structured_data": seo_service.build_structured_data(request, tool_data),
        },
    )


@router.get("/jpg-to-png", response_class=HTMLResponse)
async def jpg_to_png_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("jpg-to-png")
    base_url = _build_base_url(request)
    seo_title = "JPG to PNG Converter Online Free - Converigo"
    seo_description = (
        "Convert JPG to PNG online free. Fast, secure and easy JPG to PNG image converter."
    )

    faq_items = [
        {
            "question": "What is JPG to PNG conversion?",
            "answer": "JPG to PNG conversion changes JPG images into PNG format while preserving image quality.",
        },
        {
            "question": "How do I convert JPG to PNG?",
            "answer": "Upload your JPG image, choose PNG format, and download the converted file.",
        },
        {
            "question": "Is JPG to PNG converter free?",
            "answer": "Yes, Converigo provides free online JPG to PNG conversion.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/jpg-to-png",
        "og_url": f"{base_url}/jpg-to-png",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "jpg to png converter, convert jpg to png online, jpg to png online free",
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    structured_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq_items
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/jpg_to_png_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": meta,
            "title": seo_title,
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Fast image conversion", "text": "Convert your JPG images to PNG quickly without installing software."},
                {"title": "Secure file processing", "text": "Your files are handled safely and kept private during conversion."},
                {"title": "Free online converter", "text": "Use Converigo online for free to turn JPG into PNG."},
                {"title": "High quality PNG output", "text": "Export your images in crisp PNG format with strong visual quality."},
            ],
            "structured_data": structured_data,
        },
    )


@router.get("/png-to-jpg", response_class=HTMLResponse)
async def png_to_jpg_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("png-to-jpg")
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)
    seo_data = seo_service.build_tool_meta(request, tool_data)

    faq_items = [
        {
            "question": "What is PNG to JPG conversion?",
            "answer": "PNG to JPG conversion changes PNG images into JPG format for easier sharing and smaller file size.",
        },
        {
            "question": "Why convert PNG images to JPG?",
            "answer": "JPG files are widely supported and typically have smaller file sizes for faster sharing and loading.",
        },
        {
            "question": "Can I convert multiple PNG files at once?",
            "answer": "Yes, Converigo lets you convert one or more PNG images to JPG in a single session.",
        },
        {
            "question": "Is PNG to JPG converter free?",
            "answer": "Yes, Converigo provides free online PNG to JPG conversion.",
        },
    ]

    supported_formats = [
        {"label": "Input format", "value": tool_data.get("source", "PNG").upper()},
        {"label": "Output format", "value": tool_data.get("target", "JPG").upper()},
    ]

    how_to_use = [
        {
            "step": "1",
            "title": "Upload your PNG images",
            "description": "Choose one or more PNG files from your device or drag them into the converter.",
        },
        {
            "step": "2",
            "title": "Convert to JPG",
            "description": "Start the conversion and let Converigo transform your images securely.",
        },
        {
            "step": "3",
            "title": "Download your JPG files",
            "description": "Download the converted JPG files instantly once conversion is complete.",
        },
    ]

    tool_data_with_faq = {**tool_data, "faq": faq_items}
    structured_data = seo_service.build_structured_data(request, tool_data_with_faq)

    return templates.TemplateResponse(
        request=request,
        name="pages/png_to_jpg_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": seo_data,
            "title": seo_data["title"],
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Fast conversion", "text": "Convert PNG to JPG in seconds without installing software."},
                {"title": "Smaller image size", "text": "Reduce your PNG file size while keeping good visual quality."},
                {"title": "Broad compatibility", "text": "JPG files work with more devices, websites, and apps than PNG."},
            ],
            "supported_formats": supported_formats,
            "how_to_use": how_to_use,
            "related_tools": related_tools,
            "structured_data": structured_data,
        },
    )


@router.get("/png-to-webp", response_class=HTMLResponse)
async def png_to_webp_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("png-to-webp")
    base_url = _build_base_url(request)
    seo_title = "PNG to WEBP Converter Online Free - Converigo"
    seo_description = (
        "Convert PNG to WEBP online free. Fast, secure and easy PNG image converter."
    )

    faq_items = [
        {
            "question": "What is PNG to WEBP conversion?",
            "answer": "PNG to WEBP conversion transforms PNG images into modern WEBP format with efficient compression.",
        },
        {
            "question": "Why convert PNG to WEBP?",
            "answer": "WEBP images usually provide smaller file sizes while maintaining good visual quality.",
        },
        {
            "question": "Is PNG to WEBP converter free?",
            "answer": "Yes, Converigo provides free online PNG to WEBP conversion.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/png-to-webp",
        "og_url": f"{base_url}/png-to-webp",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "png to webp converter, convert png to webp online, png to webp online free",
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    structured_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq_items
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/png_to_webp_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": meta,
            "title": seo_title,
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Smaller image size", "text": "Reduce the size of your PNG files while keeping the visual quality high."},
                {"title": "Fast conversion", "text": "Convert your PNG images to WEBP in seconds without installing software."},
                {"title": "Secure processing", "text": "Your images are handled safely and kept private during conversion."},
                {"title": "Free online tool", "text": "Use Converigo online for free to turn PNG into WEBP."},
            ],
            "structured_data": structured_data,
        },
    )


@router.get("/webp-to-jpg", response_class=HTMLResponse)
async def webp_to_jpg_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("webp-to-jpg")
    base_url = _build_base_url(request)
    seo_title = "WEBP to JPG Converter Online Free - Converigo"
    seo_description = (
        "Convert WEBP to JPG online free. Fast, secure and easy WEBP image converter."
    )

    faq_items = [
        {
            "question": "What is WEBP to JPG conversion?",
            "answer": "WEBP to JPG conversion changes modern WEBP images into widely supported JPG format.",
        },
        {
            "question": "Why convert WEBP to JPG?",
            "answer": "JPG files are supported by more applications and devices, making sharing easier.",
        },
        {
            "question": "Is WEBP to JPG converter free?",
            "answer": "Yes, Converigo provides free online WEBP to JPG conversion.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/webp-to-jpg",
        "og_url": f"{base_url}/webp-to-jpg",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "webp to jpg converter, convert webp to jpg online, webp to jpg online free",
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    structured_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq_items
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/webp_to_jpg_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": meta,
            "title": seo_title,
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Convert WEBP images quickly", "text": "Convert your WEBP images to JPG in seconds without installing software."},
                {"title": "Improve compatibility with JPG format", "text": "Use your images across more apps, devices, and platforms."},
                {"title": "Secure file processing", "text": "Your files are handled safely and kept private during conversion."},
                {"title": "Free online converter", "text": "Use Converigo online for free to turn WEBP into JPG."},
            ],
            "structured_data": structured_data,
        },
    )


@router.get("/pdf-to-jpg", response_class=HTMLResponse)
async def pdf_to_jpg_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("pdf-to-jpg")
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)
    seo_data = seo_service.build_tool_meta(request, tool_data)

    faq_items = [
        {
            "question": "What is PDF to JPG conversion?",
            "answer": "PDF to JPG conversion converts PDF pages into image files that are easier to view and share.",
        },
        {
            "question": "Why convert PDF to JPG?",
            "answer": "JPG images are supported widely across devices and applications for easier sharing.",
        },
        {
            "question": "Can I convert multiple PDF pages at once?",
            "answer": "Yes, Converigo converts multiple PDF pages into JPG images in one session.",
        },
        {
            "question": "Is PDF to JPG converter free?",
            "answer": "Yes, Converigo provides free online PDF to JPG conversion.",
        },
    ]

    supported_formats = [
        {"label": "Input format", "value": tool_data.get("source", "PDF").upper()},
        {"label": "Output format", "value": tool_data.get("target", "JPG").upper()},
    ]

    how_to_use = [
        {
            "step": "1",
            "title": "Upload your PDF",
            "description": "Choose a PDF file from your device or drag it into the converter.",
        },
        {
            "step": "2",
            "title": "Convert to JPG",
            "description": "Start the conversion and let Converigo transform each PDF page into JPG.",
        },
        {
            "step": "3",
            "title": "Download your images",
            "description": "Download the converted JPG files instantly once conversion is complete.",
        },
    ]

    tool_data_with_faq = {**tool_data, "faq": faq_items}
    structured_data = seo_service.build_structured_data(request, tool_data_with_faq)

    return templates.TemplateResponse(
        request=request,
        name="pages/pdf_to_jpg_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": seo_data,
            "title": seo_data["title"],
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Fast conversion", "text": "Convert PDF to JPG in seconds without installing software."},
                {"title": "Easy image sharing", "text": "Share your JPG images across more devices, platforms, and apps."},
                {"title": "Preserve page clarity", "text": "Keep your PDF page visuals crisp and clear inside JPG images."},
            ],
            "supported_formats": supported_formats,
            "how_to_use": how_to_use,
            "related_tools": related_tools,
            "structured_data": structured_data,
        },
    )


@router.get("/word-to-pdf", response_class=HTMLResponse)
async def word_to_pdf_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("word-to-pdf")
    base_url = _build_base_url(request)
    seo_title = "Word to PDF Converter Online Free - Converigo"
    seo_description = (
        "Convert Word documents to PDF online free. Fast, secure and easy DOCX to PDF converter."
    )

    faq_items = [
        {
            "question": "What is Word to PDF conversion?",
            "answer": "Word to PDF conversion transforms DOCX documents into PDF files for easier sharing and viewing.",
        },
        {
            "question": "Why convert Word files to PDF?",
            "answer": "PDF files keep documents consistent across different devices.",
        },
        {
            "question": "Is Word to PDF converter free?",
            "answer": "Yes, Converigo provides free online Word to PDF conversion.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/word-to-pdf",
        "og_url": f"{base_url}/word-to-pdf",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "word to pdf converter, convert word to pdf online, docx to pdf online free",
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    structured_data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": item["question"],
                "acceptedAnswer": {"@type": "Answer", "text": item["answer"]},
            }
            for item in faq_items
        ],
    }

    return templates.TemplateResponse(
        request=request,
        name="pages/word_to_pdf_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": meta,
            "title": seo_title,
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Convert DOCX files quickly", "text": "Turn your Word documents into PDF in seconds without installing software."},
                {"title": "Preserve document readability", "text": "Keep your formatting and layout intact for reliable viewing and printing."},
                {"title": "Easy PDF sharing", "text": "Share polished PDF files across devices, email, and cloud storage."},
                {"title": "Free online converter", "text": "Use Converigo online for free to turn Word files into PDF."},
            ],
            "structured_data": structured_data,
        },
    )


@router.get("/jpg-to-pdf", response_class=HTMLResponse)
async def jpg_to_pdf_landing(request: Request):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    tool_data = converter_data_service.load_converter_by_slug("jpg-to-pdf")
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)
    base_url = _build_base_url(request)
    seo_title = "JPG to PDF Converter Online Free - Converigo"
    seo_description = (
        "Convert JPG images to PDF online free. Fast, secure and easy image to PDF conversion."
    )

    faq_items = [
        {
            "question": "What is JPG to PDF conversion?",
            "answer": "JPG to PDF conversion combines one or more JPG images into a single PDF document.",
        },
        {
            "question": "Why convert JPG images to PDF?",
            "answer": "PDF documents are easy to share, print, and store while keeping your images intact.",
        },
        {
            "question": "Can I convert multiple JPG files into one PDF?",
            "answer": "Yes, Converigo can combine multiple JPG images into a single PDF document for easier sharing and archiving.",
        },
        {
            "question": "Is JPG to PDF converter free?",
            "answer": "Yes, Converigo provides free online JPG to PDF conversion.",
        },
    ]

    supported_formats = [
        {"label": "Input format", "value": tool_data.get("source", "JPG").upper()},
        {"label": "Output format", "value": tool_data.get("target", "PDF").upper()},
    ]

    how_to_use = [
        {
            "step": "1",
            "title": "Upload your JPG images",
            "description": "Choose one or more JPG files from your device or drag them into the converter.",
        },
        {
            "step": "2",
            "title": "Convert to PDF",
            "description": "Start the conversion and let Converigo create a single PDF from your JPG images.",
        },
        {
            "step": "3",
            "title": "Download your PDF",
            "description": "Download the finished PDF document instantly once conversion is complete.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/jpg-to-pdf",
        "og_url": f"{base_url}/jpg-to-pdf",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "jpg to pdf converter, convert jpg to pdf online, jpg to pdf online free",
        "og_type": "website",
        "twitter_card": "summary_large_image",
    }

    tool_data_with_faq = {**tool_data, "faq": faq_items}
    structured_data = seo_service.build_structured_data(request, tool_data_with_faq)

    return templates.TemplateResponse(
        request=request,
        name="pages/jpg_to_pdf_landing.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "meta": meta,
            "title": seo_title,
            "tool": tool_data,
            "upload_form": tool_data.get("upload_form", {}),
            "faq_items": faq_items,
            "benefits": [
                {"title": "Convert JPG images quickly", "text": "Turn your JPG images into PDF in seconds without installing software."},
                {"title": "Easy sharing and printing", "text": "Create a single PDF that is simple to send, print, and archive."},
                {"title": "Secure file processing", "text": "Your files are handled safely and kept private during conversion."},
                {"title": "Free online converter", "text": "Use Converigo online for free to turn JPG into PDF."},
            ],
            "supported_formats": supported_formats,
            "how_to_use": how_to_use,
            "related_tools": related_tools,
            "structured_data": structured_data,
        },
    )