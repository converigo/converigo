import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.seo_service import SeoService

router = APIRouter(prefix="/tools", tags=["tools"])
templates = Jinja2Templates(directory="app/templates")
seo_service = SeoService(Path("app/data/converters"))


@router.get("/{slug}", response_class=HTMLResponse)
async def tool_page(request: Request, slug: str):
    try:
        tool_data = seo_service.load_converter_by_slug(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tool page not found")

    seo_data = seo_service.build_seo_metadata(request, tool_data)

    return templates.TemplateResponse(
        request,
        "tool.html",
        {
            "request": request,
            "title": seo_data["title"],
            "description": seo_data["description"],
            "canonical": seo_data["canonical"],
            "faq": tool_data.get("faq", []),
            "upload_form": tool_data.get("upload_form", {}),
            "related_tools": tool_data.get("related_tools", []),
            "tool": tool_data,
        },
    )
