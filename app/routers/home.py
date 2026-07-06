"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0
"""

from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.converter_data_service import ConverterDataService
from app.services.seo_service import SeoService

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")
converter_data_service = ConverterDataService(Path("app/data/converters"))
seo_service = SeoService(Path("app/data/converters"))


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    popular = converter_data_service.list_popular_converters(limit=6)
    latest = converter_data_service.list_latest_converters(limit=4)
    metadata = seo_service.build_home_meta(request)

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "title": metadata["title"],
            "meta": metadata,
            "featured_converters": popular[:4],
            "popular_converters": popular,
            "latest_converters": latest,
            "structured_data": seo_service.build_structured_data(request),
            "year": datetime.utcnow().year,
        },
    )