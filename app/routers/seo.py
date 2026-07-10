from pathlib import Path
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse

from app.services.converter_data_service import ConverterDataService

router = APIRouter(tags=["seo"])
converter_data_service = ConverterDataService(Path("app/data/converters"))


@router.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap(request: Request):
    return FileResponse("app/static/sitemap.xml", media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    return FileResponse("app/static/robots.txt", media_type="text/plain")
