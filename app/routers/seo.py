from pathlib import Path
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, PlainTextResponse, Response

from app.services.seo_service import PRODUCTION_BASE_URL, SeoService

router = APIRouter(tags=["seo"])
seo_service = SeoService(Path("app/data/converters"))


@router.get("/sitemap.xml")
async def sitemap(request: Request):
    xml_content = seo_service.build_sitemap_xml(request)
    return Response(content=xml_content, media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    robots_content = (
        "User-agent: *\n"
        "Allow: /\n\n"
        f"Sitemap: {PRODUCTION_BASE_URL}/sitemap.xml\n"
    )
    return PlainTextResponse(robots_content)
