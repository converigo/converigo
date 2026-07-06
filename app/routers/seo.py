from pathlib import Path
from typing import List

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.services.converter_data_service import ConverterDataService

router = APIRouter(tags=["seo"])
converter_data_service = ConverterDataService(Path("app/data/converters"))


@router.get("/sitemap.xml", response_class=HTMLResponse)
async def sitemap(request: Request):
    base_url = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.port:
        base_url += f":{request.url.port}"

    entries = converter_data_service.sitemap_entries(base_url)
    xml_parts: List[str] = [
        "<?xml version=\"1.0\" encoding=\"UTF-8\"?>",
        "<urlset xmlns=\"http://www.sitemaps.org/schemas/sitemap/0.9\">",
    ]
    for entry in entries:
        xml_parts.append("  <url>")
        xml_parts.append(f"    <loc>{entry['loc']}</loc>")
        xml_parts.append(f"    <lastmod>{entry['lastmod']}</lastmod>")
        xml_parts.append("  </url>")
    xml_parts.append("</urlset>")
    return HTMLResponse("\n".join(xml_parts), media_type="application/xml")


@router.get("/robots.txt", response_class=PlainTextResponse)
async def robots(request: Request):
    base_url = f"{request.url.scheme}://{request.url.hostname}"
    if request.url.port:
        base_url += f":{request.url.port}"
    lines = [
        "User-agent: *",
        "Allow: /",
        f"Sitemap: {base_url}/sitemap.xml",
    ]
    return PlainTextResponse("\n".join(lines))
