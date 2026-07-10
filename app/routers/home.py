"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 2.0.0
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.converter_data_service import ConverterDataService
from app.services.language_service import LanguageService
from app.services.seo_service import SeoService

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")

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


async def _render_trust_page(
    request: Request,
    template_name: str,
    title: str,
    description: str,
    canonical_path: str,
) -> HTMLResponse:
    base_url = _build_base_url(request)
    metadata = {
        "title": title,
        "description": description,
        "canonical": f"{base_url}{canonical_path}",
        "keywords": "Convertin, file conversion, online converter, document conversion, image conversion",
        "author": "Convertin",
        "robots": "index,follow",
    }
    return templates.TemplateResponse(
        request=request,
        name=f"pages/{template_name}",
        context={
            "request": request,
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

    return templates.TemplateResponse(
        request=request,
        name="pages/home.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
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
        "About Convertin | Fast Online File Conversion",
        "Learn about Convertin, our mission, and how we make file conversion simple, fast, and secure.",
        "/about",
    )


@router.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return await _render_trust_page(
        request,
        "privacy.html",
        "Privacy Policy | Convertin",
        "Read Convertin's privacy policy and understand how we handle your files and personal data.",
        "/privacy",
    )


@router.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return await _render_trust_page(
        request,
        "terms.html",
        "Terms of Service | Convertin",
        "Review Convertin's terms of service and usage guidelines for converting files online.",
        "/terms",
    )


@router.get("/contact", response_class=HTMLResponse)
async def contact(request: Request):
    return await _render_trust_page(
        request,
        "contact.html",
        "Contact Convertin | File Conversion Support",
        "Get in touch with Convertin for support, questions, or feedback about our file conversion tools.",
        "/contact",
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
    base_url = _build_base_url(request)
    seo_title = "MP4 to MP3 Converter Online Free - Convertin"
    seo_description = (
        "Convert MP4 videos to MP3 audio online free. Fast, secure and easy MP4 to MP3 converter."
    )

    faq_items = [
        {
            "question": "What is MP4 to MP3 conversion?",
            "answer": "MP4 to MP3 conversion extracts the audio track from a video file and saves it as a standalone MP3 audio file.",
        },
        {
            "question": "How do I convert MP4 to MP3?",
            "answer": "Upload your MP4 video, choose the MP3 output, and download the converted file once the process finishes.",
        },
        {
            "question": "Is Convertin free?",
            "answer": "Yes. Convertin lets you convert MP4 to MP3 online free for quick audio extraction.",
        },
    ]

    meta = {
        "title": seo_title,
        "description": seo_description,
        "canonical": f"{base_url}/mp4-to-mp3",
        "og_url": f"{base_url}/mp4-to-mp3",
        "og_image": f"{base_url}/static/images/og-default.png",
        "keywords": "mp4 to mp3 converter, convert mp4 to mp3, mp4 to mp3 online free",
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
        name="pages/mp4_to_mp3_landing.html",
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
                {"title": "Fast conversion", "text": "Convert your MP4 videos to MP3 in seconds without installing software."},
                {"title": "Secure processing", "text": "Your files are handled safely and kept private during conversion."},
                {"title": "Free online tool", "text": "Use Convertin online for free to extract audio from MP4 videos."},
            ],
            "structured_data": structured_data,
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
    seo_title = "JPG to PNG Converter Online Free - Convertin"
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
            "answer": "Yes, Convertin provides free online JPG to PNG conversion.",
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
                {"title": "Free online converter", "text": "Use Convertin online for free to turn JPG into PNG."},
                {"title": "High quality PNG output", "text": "Export your images in crisp PNG format with strong visual quality."},
            ],
            "structured_data": structured_data,
        },
    )