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