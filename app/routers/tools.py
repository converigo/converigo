from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.services.converter_data_service import ConverterDataService
from app.services.language_service import LanguageService
from app.services.seo_service import SeoService

router = APIRouter(prefix="/tools", tags=["tools"])
templates = Jinja2Templates(directory="app/templates")
converter_data_service = ConverterDataService(Path("app/data/converters"))
seo_service = SeoService(Path("app/data/converters"))
language_service = LanguageService(Path("app/locales"))


@router.get("/{slug}", response_class=HTMLResponse)
async def tool_page(request: Request, slug: str):
    locale_data = language_service.load_locale(
        accept_language=request.headers.get("accept-language"),
        lang_query=request.query_params.get("lang"),
    )

    def t(key: str, default: str = "") -> str:
        return language_service.translate(locale_data, key, default)

    try:
        tool_data = converter_data_service.load_converter_by_slug(slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tool page not found")

    seo_data = seo_service.build_tool_meta(request, tool_data)
    related_tools = converter_data_service.resolve_related_tools(tool_data, limit=4)

    return templates.TemplateResponse(
        request=request,
        name="tool_page.html",
        context={
            "request": request,
            "locale": locale_data,
            "t": t,
            "title": seo_data["title"],
            "seo": seo_data,
            "tool": tool_data,
            "faq": tool_data.get("faq", []),
            "upload_form": tool_data.get("upload_form", {}),
            "related_tools": related_tools,
            "structured_data": seo_service.build_structured_data(request, tool_data),
        },
    )
