from pathlib import Path
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response

from app.services.seo_service import SeoService

router = APIRouter(tags=["seo"])
seo_service = SeoService(Path("app/data/converters"))


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    xml_content = seo_service.build_sitemap_xml(request)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    return FileResponse("app/static/robots.txt", media_type="text/plain")
