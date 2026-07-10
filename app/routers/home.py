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